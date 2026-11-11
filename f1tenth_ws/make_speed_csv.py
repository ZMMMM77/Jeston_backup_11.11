#!/usr/bin/env python3
"""
Turn a recorded x,y lap (e.g. from waypoint_logger.py) into the CSV format the
pure_pursuit node reads:

    # x_m,y_m,vx_mps,s_m,psi_rad,kappa_radpm,ax_mps2
      col0 col1  col2  col3  col4    col5       col6
    node uses: x,y (0,1), speed (2), curvature (5)

Steps: smooth joystick wobble -> resample evenly -> heading & curvature ->
speed profile (corner limit + accel/brake limits around the closed loop).

Usage:
    python3 make_speed_csv.py levine_2nd_lap.csv levine_2nd.csv --v-max 1.5
Then copy the output into the pure_pursuit package's waypoints/ folder.
"""
import argparse
import numpy as np


def load_xy(path):
    d = np.loadtxt(path, delimiter=",", comments="#", ndmin=2)
    return d[:, :2]


def dedupe(p, tol=1e-3):
    keep = [0]
    for i in range(1, len(p)):
        if np.hypot(*(p[i] - p[keep[-1]])) > tol:
            keep.append(i)
    p = p[keep]
    if np.hypot(*(p[0] - p[-1])) < tol:      # drop repeated closing point
        p = p[:-1]
    return p


def resample_closed(p, ds):
    closed = np.vstack([p, p[:1]])
    seg = np.hypot(*np.diff(closed, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(12, int(round(s[-1] / ds)))
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.c_[np.interp(t, s, closed[:, 0]), np.interp(t, s, closed[:, 1])]


def smooth_closed(p, window_pts):
    if window_pts < 3:
        return p
    k = window_pts | 1                       # odd
    h = k // 2
    pad = np.vstack([p[-h:], p, p[:h]])
    ker = np.ones(k) / k
    return np.c_[np.convolve(pad[:, 0], ker, "valid"), np.convolve(pad[:, 1], ker, "valid")]


def geometry(p, baseline_m=0.5, spacing=0.1):
    """Heading and signed curvature. Curvature uses the circle through points
    +-baseline apart, then a short moving average, so small wobbles don't read
    as sharp turns."""
    nxt = np.roll(p, -1, 0)
    seg = np.hypot(*(nxt - p).T)
    k = max(1, int(round(baseline_m / spacing)))
    a, b, c = np.roll(p, k, 0), p, np.roll(p, -k, 0)
    ab, bc, ac = b - a, c - b, c - a
    cross = ab[:, 0] * bc[:, 1] - ab[:, 1] * bc[:, 0]
    den = np.hypot(*ab.T) * np.hypot(*bc.T) * np.hypot(*ac.T)
    kappa = 2.0 * cross / np.maximum(den, 1e-9)
    w = 2 * k + 1
    kappa = np.convolve(np.r_[kappa[-k:], kappa, kappa[:k]], np.ones(w) / w, "valid")
    psi = np.arctan2(*(c - a)[:, ::-1].T)
    s = np.concatenate([[0], np.cumsum(seg[:-1])])
    return s, psi, kappa, seg


def speed_profile(kappa, seg, v_max, v_min, a_lat, a_acc, a_brk):
    v = np.minimum(v_max, np.sqrt(a_lat / np.maximum(np.abs(kappa), 1e-6)))
    v = np.maximum(v, v_min)
    n = len(v)
    for _ in range(3):                       # wrap around the loop a few times
        for i in range(n):                   # acceleration limit (forward)
            j = (i + 1) % n
            v[j] = min(v[j], np.sqrt(v[i] ** 2 + 2 * a_acc * seg[i]))
        for i in range(n - 1, -1, -1):       # braking limit (backward)
            j = (i + 1) % n
            v[i] = min(v[i], np.sqrt(v[j] ** 2 + 2 * a_brk * seg[i]))
    ax = (np.roll(v, -1) ** 2 - v**2) / (2 * seg)
    return v, ax


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp", help="recorded CSV with x,y in the first two columns")
    ap.add_argument("out", help="output CSV, e.g. levine_1st_map.csv (name = track parameter)")
    ap.add_argument("--spacing", type=float, default=0.10, help="m between output points")
    ap.add_argument("--smooth", type=float, default=0.8, help="smoothing window in m (0 = off)")
    ap.add_argument("--v-max", type=float, default=1.5, help="straight-line speed m/s")
    ap.add_argument("--v-min", type=float, default=0.8, help="never plan slower than this")
    ap.add_argument("--a-lat", type=float, default=1.5, help="lateral accel limit m/s^2")
    ap.add_argument("--a-acc", type=float, default=1.0, help="acceleration limit m/s^2")
    ap.add_argument("--a-brake", type=float, default=1.5, help="braking limit m/s^2")
    ap.add_argument("--reverse", action="store_true", help="flip driving direction")
    a = ap.parse_args()

    p = dedupe(load_xy(a.inp))
    if a.reverse:
        p = p[::-1]
    p = resample_closed(p, a.spacing)
    p = smooth_closed(p, int(round(a.smooth / a.spacing)) if a.smooth > 0 else 0)
    p = resample_closed(p, a.spacing)        # even spacing again after smoothing
    s, psi, kappa, seg = geometry(p, spacing=a.spacing)
    v, ax = speed_profile(kappa, seg, a.v_max, a.v_min, a.a_lat, a.a_acc, a.a_brake)

    with open(a.out, "w") as f:
        f.write("# x_m,y_m,vx_mps,s_m,psi_rad,kappa_radpm,ax_mps2\n")
        for r in zip(p[:, 0], p[:, 1], v, s, psi, kappa, ax):
            f.write(",".join(f"{x:.5f}" for x in r) + "\n")

    ak = np.abs(kappa)
    lap = np.sum(seg / ((v + np.roll(v, -1)) / 2))
    gap = np.hypot(*(p[0] - p[-1]))
    print(f"Wrote {a.out}: {len(p)} points, lap length {np.sum(seg):.1f} m, "
          f"est. lap time {lap:.1f} s")
    print(f"Speed: {v.min():.2f} .. {v.max():.2f} m/s   |kappa|: median {np.median(ak):.3f}, "
          f"90th pct {np.percentile(ak, 90):.3f}, max {ak.max():.3f} 1/m "
          f"(tightest radius {1/max(ak.max(),1e-6):.2f} m)")
    lo = max(0.05, 3 * float(np.median(ak)))
    hi = max(2 * lo, 0.5 * float(ak.max()))
    print("Suggested node params for this track (pure_pursuit_car.yaml):")
    print(f"  curve_kappa_low:  {lo:.3f}")
    print(f"  curve_kappa_high: {hi:.3f}")
    if ak.max() > np.tan(0.36) / 0.33:
        print("[WARN] some corners are tighter than the car can steer "
              f"(min radius ~{0.33/np.tan(0.36):.2f} m): increase --smooth or re-record wider")


if __name__ == "__main__":
    main()
