#!/usr/bin/env python3
"""
Raceline Studio — Web-based raceline management for F1Tenth racing.

Wraps the existing raceline_optimizer.py as a backend, serves a modern UI
for managing up to 4 racelines (primary, pass-left, pass-right, fallback),
generating offset variants, tuning velocity profiles, and exporting CSVs.

Usage:
    pip install flask
    cd <this directory>
    python3 app.py
    → opens http://localhost:5050
"""
import os, sys, json, glob, yaml, hashlib, datetime, threading, time, webbrowser
import numpy as np
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_file

import rclpy
from rclpy.node import Node
from raceline_msgs.srv import UpdateRaceline

# ═══════════════════════════════════════════════════════════════════════════
# WORKSPACE PATHS — edit these to match your setup
# ═══════════════════════════════════════════════════════════════════════════
PURE_PURSUIT_WAYPOINTS = "/home/nvidia/f1tenth_ws/src/pure-pursuit/pure_pursuit/waypoints"
MPPI_WAYPOINTS         = "~/ros2_ws/roboracer_ws/src/mppi/mppi_bringup/waypoints"

MAPS_DIRS = ["/home/nvidia/f1tenth_ws/src/particle_filter/maps"]

# Map stem (no extension) that gets floated to the top of the dropdown
DEFAULT_MAP = "under_map"

# MPPI export endpoint writes here (under the MPPI waypoints root)
MPPI_EXPORT_SUBDIR = ""
# ═══════════════════════════════════════════════════════════════════════════

sys.path.insert(0, str(Path(__file__).resolve().parent))
import raceline_optimizer as ropt

app = Flask(__name__)

WP_ROOTS = {
    "pure_pursuit": Path(os.path.expanduser(PURE_PURSUIT_WAYPOINTS)),
    "mppi":         Path(os.path.expanduser(MPPI_WAYPOINTS)),
}
MPPI_WP_DIR = WP_ROOTS["mppi"] / MPPI_EXPORT_SUBDIR
MAPS_DIRS = [Path(os.path.expanduser(d)) for d in MAPS_DIRS]


# ── ROS2 node with service clients ────────────────────────────────────────
class StudioNode(Node):
    def __init__(self):
        super().__init__('raceline_studio')
        self.pp_client   = self.create_client(UpdateRaceline, '/pure_pursuit/update_raceline')
        self.mppi_client = self.create_client(UpdateRaceline, '/mppi/update_raceline')

STUDIO_NODE: "StudioNode | None" = None


def _resolve(rel_path):
    """Map a sidebar path like 'pure_pursuit/race/foo.csv' to its absolute file."""
    parts = rel_path.split("/", 1)
    if len(parts) < 2 or parts[0] not in WP_ROOTS:
        raise ValueError(f"Path must start with one of {list(WP_ROOTS)}: {rel_path!r}")
    return WP_ROOTS[parts[0]] / parts[1]

# ── Helpers ─────────────────────────────────────────────────────────────────
def _find_maps():
    """Return list of {name, yaml_path, img_path} for all available track maps.
    Handles both PNG and PGM image formats (PGM converted on-the-fly via /api/map-image)."""
    maps = []
    for d in MAPS_DIRS:
        if not d.exists():
            continue
        for y in sorted(d.glob("*.yaml")):
            meta = yaml.safe_load(y.read_text())
            if "image" not in meta:
                continue
            img = d / meta["image"]
            if not img.exists():
                # Try alternate extensions (pgm ↔ png)
                for ext in ['.pgm', '.png', '.bmp']:
                    alt = img.with_suffix(ext)
                    if alt.exists():
                        img = alt
                        break
            if not img.exists():
                continue
            maps.append({"name": f"{d.name}/{y.stem}", "yaml": str(y), "image": str(img),
                         "resolution": meta.get("resolution", 0.05),
                         "origin": meta.get("origin", [0, 0, 0])})
    maps.sort(key=lambda m: (not m["name"].endswith("/" + DEFAULT_MAP), m["name"]))
    return maps

# ── Waypoint JSON ↔ numpy helpers (handle nullable friction column) ─────
def _wps_from_json(data, min_friction=None):
    """JSON [[x,y,yaw,speed,friction_or_null], ...] → numpy (N, ≥5) array.
    None values become NaN; if min_friction given, NaN in col 4 is filled.

    Tolerant of mixed-width rows (e.g. a freshly inserted 4-col waypoint
    among 5-col rows): shorter rows are padded with NaN to the widest row.
    """
    if not data:
        return np.zeros((0, 5))
    rows = [[(np.nan if v is None else float(v)) for v in row] for row in data]
    max_cols = max((len(r) for r in rows), default=5)
    # Pad short rows with NaN so np.array doesn't choke on mixed widths
    rows = [r + [np.nan] * (max_cols - len(r)) for r in rows]
    arr = np.array(rows, dtype=float)
    if arr.ndim == 1:
        arr = arr[None, :]
    # Pad to 5 cols if legacy 4-col input
    if arr.shape[1] == 4:
        arr = np.hstack([arr, np.full((arr.shape[0], 1), np.nan)])
    if min_friction is not None and arr.shape[1] >= 5:
        nanmask = ~np.isfinite(arr[:, 4])
        arr[nanmask, 4] = min_friction
    return arr

def _wps_to_json(arr):
    """(N, ≥4) numpy → JSON-safe list, mapping NaN → None."""
    return [[(float(v) if np.isfinite(v) else None) for v in row] for row in arr]


def _find_csvs():
    """List CSVs from all waypoint roots, prefixed with their root name
    (e.g. 'pure_pursuit/race/foo.csv', 'mppi/mppi/sim/bar.csv')."""
    csvs = []
    for prefix, root in WP_ROOTS.items():
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.csv")):
            csvs.append(f"{prefix}/{f.relative_to(root)}")
    return sorted(csvs)

def _read_meta_header(path):
    """Read studio metadata from leading '#' comment lines.
    Returns dict with any of {v_min, v_max, min_friction, max_friction, a_max, a_brake}
    that were found. Missing keys are simply absent (no None fill)."""
    import re
    keys = ("v_min", "v_max", "min_friction", "max_friction", "a_max", "a_brake")
    out = {}
    try:
        with open(path, "r") as f:
            for _ in range(8):
                line = f.readline()
                if not line or not line.startswith("#"):
                    break
                low = line.lower()
                for k in keys:
                    if k in out:
                        continue
                    m = re.search(rf"\b{k}\s*=\s*([0-9.+\-eE]+)", low)
                    if m:
                        try:
                            out[k] = float(m.group(1))
                        except ValueError:
                            pass
    except Exception:
        pass
    return out


PP_CSV_HEADER = 'x_m,y_m,vx_mps,s_m,psi_rad,kappa_radpm,ax_mps2'


def _geometry_internal(xy, ratio=None, friction=None):
    xy = np.asarray(xy, dtype=float)
    if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 3 or not np.isfinite(xy).all():
        raise ValueError('At least three finite XY points are required')
    delta = np.roll(xy, -1, axis=0) - xy
    if np.any(np.linalg.norm(delta, axis=1) < 1e-9):
        raise ValueError('Duplicate consecutive points: remove duplicates and repeated closing point')
    yaw = np.arctan2(delta[:, 1], delta[:, 0])
    if ratio is None:
        ratio = np.zeros(len(xy))
    if friction is None:
        friction = np.full(len(xy), np.nan)
    return np.column_stack([xy, yaw, ratio, friction])


def _load_pp_geometry_csv(full):
    import csv
    names = None
    rows = []
    friction = None
    with open(full, encoding='utf-8-sig', newline='') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                comment = line[1:].strip()
                if comment.startswith('studio_friction='):
                    friction = json.loads(comment.split('=', 1)[1])
                tokens = [v.strip().lower() for v in comment.split(',')]
                if 'x_m' in tokens and 'y_m' in tokens:
                    names = tokens
                continue
            tokens = next(csv.reader([line]))
            low = [v.strip().lower() for v in tokens]
            if 'x_m' in low and 'y_m' in low and not rows:
                names = low
                continue
            rows.append(tokens)
    if not rows:
        raise ValueError('CSV has no data rows')
    if names is None:
        if len(rows[0]) == 2:
            names = ['x_m', 'y_m']
        elif len(rows[0]) in (4, 5):
            return None  # Legacy x,y,yaw,ratio[,friction].
        elif ';' in rows[0][0]:
            return None  # Keep existing MPPI reader.
        else:
            raise ValueError('CSV needs a named header; ambiguous column order is not accepted')
    def column(name, optional=False):
        if name not in names:
            return np.full(len(rows), np.nan)
        idx = names.index(name)
        values = []
        for number, row in enumerate(rows, 1):
            value = row[idx].strip() if idx < len(row) else ''
            if not value and optional:
                values.append(np.nan)
            else:
                try:
                    values.append(float(value))
                except ValueError:
                    raise ValueError(f'Invalid {name} at data row {number}')
        return np.asarray(values)
    xy = np.column_stack([column('x_m'), column('y_m')])
    vx = column('vx_mps', optional=True)
    meta = _read_meta_header(full)
    if np.isfinite(vx).all() and np.all(vx >= 0):
        vmin = min(float(meta.get('v_min', vx.min())), float(vx.min()))
        vmax = max(float(meta.get('v_max', vx.max())), float(vx.max()))
        ratio = np.zeros(len(vx)) if vmax == vmin else (vx-vmin)/(vmax-vmin)
        meta.update(v_min=vmin, v_max=vmax)
        needs_profile = False
    else:
        ratio = np.zeros(len(rows))
        needs_profile = True
    if friction is None:
        friction = column('friction', optional=True)
    friction = np.asarray(friction, dtype=float)
    if friction.shape != (len(rows),) or np.any(np.isinf(friction)) or np.any(friction <= 0):
        raise ValueError('Friction must be positive; reload the original named CSV')
    # A duplicated final point is a common closed-loop CSV convention.
    if len(xy) > 3 and np.linalg.norm(xy[-1]-xy[0]) < 1e-9:
        xy, ratio, friction = xy[:-1], ratio[:-1], friction[:-1]
    arr = _geometry_internal(xy, ratio, friction)
    return {**meta, 'waypoints': _wps_to_json(arr), 'needs_profile': needs_profile}


def _save_pp_geometry_csv(rel_path, data, **meta):
    wps = _wps_from_json(data)
    if wps.ndim != 2 or wps.shape[1] != 5:
        raise ValueError('Reload the source CSV: expected internal XY/yaw/ratio/friction')
    if meta.get('v_min') is None or meta.get('v_max') is None:
        raise ValueError('Speed limits are required; use Re-profile Speed first')
    lo, hi = float(meta['v_min']), float(meta['v_max'])
    if not np.isfinite([lo, hi]).all() or not 0 < lo <= hi:
        raise ValueError('Require 0 < v_min <= v_max')
    if not np.isfinite(wps[:, 3]).all() or np.any((wps[:, 3] < 0) | (wps[:, 3] > 1)):
        raise ValueError('Invalid speed ratios; reload CSV and Re-profile Speed')
    wps = _geometry_internal(wps[:, :2], wps[:, 3], wps[:, 4])
    rows = _to_mppi_rows(wps, lo, hi)[:, [1, 2, 5, 0, 3, 4, 6]]
    if not np.isfinite(rows).all():
        raise ValueError('Non-finite export; re-profile the source CSV')
    full = _resolve(rel_path)
    full.parent.mkdir(parents=True, exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write('# ' + PP_CSV_HEADER + chr(10))
        f.write('# ' + '; '.join(f'{k}={float(v):.9f}' for k,v in meta.items() if v is not None) + chr(10))
        friction = [float(v) if np.isfinite(v) else None for v in wps[:,4]]
        f.write('# studio_friction=' + json.dumps(friction, allow_nan=False) + chr(10))
        np.savetxt(f, rows, delimiter=',', fmt='%.9f')


def _load_csv(rel_path):
    """Load waypoints CSV → {waypoints, v_min?, v_max?, min_friction?}.

    'mppi/...' paths are Levine 9-col (';' delimited, 3 header lines): extract
    [x_m, y_m, psi_rad, vx_mps] and rescale vx to a 0-1 ratio using the file's
    own min/max so the colormap spans red→cyan regardless of absolute speed.
    The file's min/max vx ALSO populate v_min/v_max in the response so the UI
    sliders snap to the values that produced the trajectory.
    If a 10th column is present it's loaded as per-waypoint friction; otherwise
    friction = NaN (the UI fills it in with current min_friction on display).
    For pure-pursuit-style 4/5-col files, v_min/v_max are read from a
    '# v_min=X; v_max=Y' header comment if `_save_csv` wrote one."""
    full = _resolve(rel_path)
    geometry = _load_pp_geometry_csv(full)
    if geometry is not None:
        return geometry
    if rel_path.startswith("mppi/"):
        wps = np.loadtxt(str(full), delimiter=';', skiprows=3)
        cols = [1, 2, 3, 5]
        xy_yaw_v = wps[:, cols]   # x_m, y_m, psi_rad, vx_mps
        vx = xy_yaw_v[:, 3]
        vmin, vmax = float(vx.min()), float(vx.max())
        span = max(vmax - vmin, 1e-6)
        xy_yaw_v[:, 3] = np.clip((vx - vmin) / span, 0.0, 1.0)
        # Optional 10th column = friction
        if wps.shape[1] >= 10:
            fric = wps[:, 9:10]
        else:
            fric = np.full((len(wps), 1), np.nan)
        out = np.hstack([xy_yaw_v, fric])
        return {
            "waypoints": [[float(v) if np.isfinite(v) else None for v in row] for row in out],
            "v_min": vmin,
            "v_max": vmax,
        }
    arr = ropt.load_waypoints(str(full))
    meta = _read_meta_header(full)
    return {
        "waypoints": [[float(v) if np.isfinite(v) else None for v in row] for row in arr],
        **meta,
    }

def _save_csv(rel_path, data, **meta):
    """Save [[x,y,yaw,speed,friction?], ...] to CSV with optional studio metadata
    in a leading '# k=v; ...' comment line. Recognised metadata keys:
    v_min, v_max, min_friction, max_friction, a_max, a_brake. numpy.loadtxt
    skips '#' lines by default."""
    if rel_path.startswith("pure_pursuit/"):
        return _save_pp_geometry_csv(rel_path, data, **meta)
    full = _resolve(rel_path)
    full.parent.mkdir(parents=True, exist_ok=True)
    wps = np.array(data)
    finite = {k: v for k, v in meta.items() if v is not None}
    if finite:
        header = "# " + "; ".join(f"{k}={float(v):.6f}" for k, v in finite.items())
        with open(full, "w") as f:
            f.write(header + "\n")
            np.savetxt(f, wps, fmt='%.6f', delimiter=', ')
        print(f"Saved {len(wps)} waypoints ({wps.shape[1]} cols) to {full}  [{header.strip('# ')}]")
    else:
        ropt.save_waypoints(wps, str(full))


# ── MPPI export (Levine 9-column format) ───────────────────────────────────
def _signed_curvature(xy):
    """Signed Menger curvature on a closed loop. Sign convention matches
    cubic_spline._calc_kappa_from_xy: positive = CCW (left turn) in ENU."""
    n = len(xy)
    k = np.zeros(n)
    for i in range(n):
        p0 = xy[(i - 1) % n]
        p1 = xy[i]
        p2 = xy[(i + 1) % n]
        d1 = p1 - p0
        d2 = p2 - p1
        cross = d1[0] * d2[1] - d1[1] * d2[0]   # signed
        a = np.linalg.norm(d1)
        b = np.linalg.norm(d2)
        c = np.linalg.norm(p2 - p0)
        denom = a * b * c
        if denom > 1e-10:
            k[i] = 2.0 * cross / denom
    return k


def _to_mppi_rows(wps, v_min, v_max, w_tr_const=1.0, default_friction=None):
    """Convert [x, y, yaw, speed_ratio, friction?] (closed loop, N rows) into the
    Levine 9-or-10-column array: s_m, x_m, y_m, psi_rad, kappa_radpm, vx_mps,
    ax_mps2, w_tr_right_m, w_tr_left_m [, friction]. The 10th column is included
    only when the input has a friction column with at least one finite value or
    a default_friction is supplied."""
    wps = np.asarray(wps, dtype=float)
    n = len(wps)
    xy = wps[:, :2]
    psi = wps[:, 2]
    ratio = np.clip(wps[:, 3], 0.0, 1.0)

    # Segment lengths (closed loop)
    diffs = np.roll(xy, -1, axis=0) - xy
    ds = np.linalg.norm(diffs, axis=1)

    s = np.concatenate([[0.0], np.cumsum(ds[:-1])])
    kappa = _signed_curvature(xy)
    vx = v_min + ratio * (v_max - v_min)
    ds_safe = np.maximum(ds, 1e-6)
    ax = (np.roll(vx, -1) ** 2 - vx ** 2) / (2.0 * ds_safe)
    w_tr_right = np.full(n, float(w_tr_const))
    w_tr_left  = np.full(n, float(w_tr_const))

    cols = [s, xy[:, 0], xy[:, 1], psi, kappa, vx, ax, w_tr_right, w_tr_left]

    # Friction column: only emit if input has it OR default supplied
    fric_arr = None
    if wps.shape[1] >= 5 and np.isfinite(wps[:, 4]).any():
        fric_arr = wps[:, 4].copy()
        # Replace any remaining NaN with default_friction or column mean
        if not np.isfinite(fric_arr).all():
            fill = default_friction if default_friction is not None else float(np.nanmean(fric_arr))
            fric_arr[~np.isfinite(fric_arr)] = fill
    elif default_friction is not None:
        fric_arr = np.full(n, float(default_friction))

    if fric_arr is not None:
        cols.append(fric_arr)

    return np.column_stack(cols)


def _save_mppi_csv(out_path, rows):
    """Write 3-line header + ';'-delimited body, %.18e precision. Header
    auto-extends to 10th column when friction is present."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    has_fric = rows.shape[1] >= 10
    cols_str = "s_m; x_m; y_m; psi_rad; kappa_radpm; vx_mps; ax_mps2; w_tr_right_m; w_tr_left_m"
    if has_fric:
        cols_str += "; friction"
    header = (
        "# " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
        "# " + hashlib.md5(rows.tobytes()).hexdigest() + "\n"
        "# " + cols_str + "\n"
    )
    with open(out_path, "w") as f:
        f.write(header)
        np.savetxt(f, rows, delimiter=";", fmt="%.18e")

def _offset_raceline(base_wps, offset_m, map_yaml=None, safety_margin=0.15):
    """Generate a raceline offset perpendicular to the base line.
    offset_m > 0 → left (positive y in ROS), < 0 → right.
    If map_yaml provided, clamps points to stay within track walls (with safety_margin).
    Returns np array of [x, y, yaw, speed]."""
    xy = base_wps[:, :2]
    n = len(xy)

    # Tangent vectors via central differences (wrapped)
    tangents = np.zeros_like(xy)
    for i in range(n):
        tangents[i] = xy[(i + 1) % n] - xy[(i - 1) % n]
    norms = np.linalg.norm(tangents, axis=1, keepdims=True)
    norms[norms < 1e-8] = 1e-8
    tangents /= norms

    # Normal = rotate tangent 90° CCW
    normals = np.column_stack([-tangents[:, 1], tangents[:, 0]])

    # Compute per-point feasible offset using distance transform
    if map_yaml:
        try:
            from scipy.ndimage import distance_transform_edt
            img, resolution, origin = ropt.load_map(map_yaml)
            free = (img > 250).astype(np.uint8)
            dt = distance_transform_edt(free) * resolution

            # For each point, find max offset that keeps it safety_margin away from walls
            feasible = np.full(n, abs(offset_m))
            for i in range(n):
                # Sample along the normal from base to full offset, find where dt drops below margin
                for frac in np.linspace(1.0, 0.0, 30):
                    trial = xy[i] + frac * offset_m * normals[i]
                    r, c = ropt.world_to_pixel(trial[0], trial[1], resolution, origin, img.shape)
                    r, c = int(round(r)), int(round(c))
                    if 0 <= r < dt.shape[0] and 0 <= c < dt.shape[1] and dt[r, c] >= safety_margin:
                        feasible[i] = abs(frac * offset_m)
                        break
                else:
                    feasible[i] = 0.0

            # Smooth the feasible offsets to avoid jagged transitions
            from scipy.ndimage import uniform_filter1d
            feasible = uniform_filter1d(feasible, size=max(3, n // 15), mode='wrap')

            sign = 1.0 if offset_m > 0 else -1.0
            capped = np.minimum(np.full(n, abs(offset_m)), feasible)
            new_xy = xy + sign * capped[:, None] * normals
        except Exception as e:
            print(f"[offset] Wall clamp failed: {e}")
            new_xy = xy + offset_m * normals
    else:
        new_xy = xy + offset_m * normals

    # Final spline smooth
    try:
        from scipy.interpolate import splprep, splev
        tck, _ = splprep([new_xy[:, 0], new_xy[:, 1]], s=0.5, per=True, k=3)
        u = np.linspace(0, 1, n, endpoint=False)
        sx, sy = splev(u, tck)
        new_xy = np.column_stack([sx, sy])
    except Exception:
        pass

    # Recompute yaw
    dx = np.diff(new_xy[:, 0], append=new_xy[0, 0])
    dy = np.diff(new_xy[:, 1], append=new_xy[0, 1])
    yaw = np.arctan2(dy, dx)

    # Keep base speed profile and friction (5-col if present)
    if base_wps.shape[1] >= 5:
        result = np.column_stack([new_xy, yaw, base_wps[:, 3], base_wps[:, 4]])
    else:
        result = np.column_stack([new_xy, yaw, base_wps[:, 3]])
    return result


# ── API Routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/maps")
def api_maps():
    return jsonify(_find_maps())

@app.route("/api/map-image")
def api_map_image():
    path = request.args.get("path", "")
    if not os.path.isfile(path):
        return "not found", 404
    # PGM files aren't browser-native — convert to PNG on the fly
    if path.lower().endswith('.pgm'):
        from PIL import Image
        import io
        img = Image.open(path)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype="image/png")
    return send_file(path, mimetype="image/png")

@app.route("/api/csvs")
def api_csvs():
    return jsonify(_find_csvs())

@app.route("/api/csv")
def api_csv_load():
    rel = request.args.get("path", "")
    try:
        return jsonify(_load_csv(rel))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/csv", methods=["POST"])
def api_csv_save():
    body = request.json
    rel = body.get("path", "")
    data = body.get("data", [])
    min_friction = body.get("min_friction")  # fills NaN friction on save if provided
    try:
        wps = _wps_from_json(data, min_friction=min_friction)
        meta = {k: body.get(k) for k in ("v_min", "v_max", "min_friction",
                                          "max_friction", "a_max", "a_brake")}
        _save_csv(rel, wps.tolist(), **meta)
        return jsonify({"ok": True, "path": rel})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/offset", methods=["POST"])
def api_offset():
    body = request.json
    base = _wps_from_json(body["base"], min_friction=body.get("min_friction"))
    offset_m = float(body.get("offset", 0.3))
    map_yaml = body.get("map_yaml")
    safety_margin = float(body.get("safety_margin", 0.15))
    result = _offset_raceline(base, offset_m, map_yaml=map_yaml, safety_margin=safety_margin)
    return jsonify(_wps_to_json(result))

@app.route("/api/profile", methods=["POST"])
def api_profile():
    body = request.json
    params = body.get('params', {})
    try:
        limits = {k: float(params.get(k, d)) for k,d in
                  [('v_max',5.0),('v_min',1.5),('a_max',6.0),('a_brake',8.0),('mu',0.41)]}
        if not all(np.isfinite(v) and v > 0 for v in limits.values()):
            raise ValueError('Speed, acceleration, braking and friction must be finite and positive')
        if limits['v_max'] < limits['v_min']:
            raise ValueError('v_max must be >= v_min')
        if 'mu_max' in params:
            mu_max = float(params['mu_max'])
            if not np.isfinite(mu_max) or mu_max < limits['mu']:
                raise ValueError('max friction must be >= min friction')
        wps = _wps_from_json(body['waypoints'], min_friction=limits['mu'])
        if wps.ndim != 2 or wps.shape[1] != 5:
            raise ValueError('Reload the original CSV: stale or incorrectly parsed waypoint columns')
        if not np.isfinite(wps[:,4]).all() or np.any(wps[:,4] <= 0):
            raise ValueError('Invalid per-point friction; reload the original CSV')
        # Rebuild heading from XY and discard old speed before the existing planner.
        clean = _geometry_internal(wps[:,:2], friction=wps[:,4])
        result = ropt.profile_velocity(clean, **limits)
        if not np.isfinite(result).all():
            raise ValueError('Speed planner returned invalid values; check geometry and friction')
        return jsonify(_wps_to_json(result))
    except (ValueError, TypeError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

@app.route("/api/estimate-laptime", methods=["POST"])
def api_estimate_laptime():
    body = request.json
    wps = np.array(body["waypoints"])
    v_min = body.get("v_min")
    v_max = body.get("v_max")
    try:
        t = ropt.estimate_lap_time(wps, v_min=v_min, v_max=v_max)
        return jsonify({"lap_time": round(t, 3)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/extract-centerline", methods=["POST"])
def api_extract_centerline():
    body = request.json
    yaml_path = body["map_yaml"]
    num_points = body.get("num_points", 350)
    margin = body.get("margin", 0.20)
    try:
        img, resolution, origin = ropt.load_map(yaml_path)
        result = ropt.extract_centerline(img, resolution, origin,
                                         num_points=num_points, margin=margin)
        # extract_centerline returns (waypoints, track_widths) tuple
        wps = result[0] if isinstance(result, tuple) else result
        return jsonify(_wps_to_json(wps))
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 400

@app.route("/api/reverse", methods=["POST"])
def api_reverse():
    """Reverse waypoint order and flip yaw by pi."""
    body = request.json
    wps = _wps_from_json(body["waypoints"])
    wps = wps[::-1].copy()
    # Flip yaw by pi
    wps[:, 2] = np.arctan2(np.sin(wps[:, 2] + np.pi), np.cos(wps[:, 2] + np.pi))
    return jsonify(_wps_to_json(wps))

@app.route("/api/resample", methods=["POST"])
def api_resample():
    """Resample waypoints with curvature-biased point distribution.
    Preserves friction column by nearest-neighbor interpolation."""
    body = request.json
    wps = _wps_from_json(body["waypoints"], min_friction=body.get("min_friction"))
    num_points = body.get("num_points", len(wps))
    turn_bias = body.get("turn_bias", 2.0)
    try:
        from scipy.interpolate import splprep, splev
        xy = wps[:, :2]
        try:
            tck, _ = splprep([xy[:, 0], xy[:, 1]], s=0, per=True, k=3)
        except Exception:
            tck, _ = splprep([xy[:, 0], xy[:, 1]], s=0.001, per=True, k=3)
        u_dense = np.linspace(0, 1, max(300, len(xy) * 4), endpoint=False)
        x_d, y_d = splev(u_dense, tck)
        xy_dense = np.column_stack([x_d, y_d])
        u_new = ropt.curvature_biased_resample(xy_dense, num_points, turn_bias=turn_bias)
        x_s, y_s = splev(u_new, tck)
        dx_s, dy_s = splev(u_new, tck, der=1)
        yaw_s = np.arctan2(dy_s, dx_s)
        orig_u = np.linspace(0, 1, len(wps), endpoint=False)
        speed_s = np.interp(u_new, orig_u, wps[:, 3])
        # Per-waypoint friction via nearest-input-index lookup
        nearest_idx = np.round(u_new * len(wps)).astype(int) % len(wps)
        fric_s = wps[nearest_idx, 4]
        result = np.column_stack([x_s, y_s, yaw_s, speed_s, fric_s])
        return jsonify(_wps_to_json(result))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

@app.route("/api/apply-friction", methods=["POST"])
def api_apply_friction():
    """Set friction value for a list of waypoint indices.
    Body: {waypoints, indices: [i, ...], friction: float}
    Returns updated waypoints."""
    body = request.json
    wps = _wps_from_json(body["waypoints"], min_friction=body.get("min_friction"))
    indices = body.get("indices", [])
    friction = float(body.get("friction", 0.0))
    if wps.shape[1] < 5:
        # Pad to 5-col (defensive — _wps_from_json should already do this)
        wps = np.hstack([wps, np.full((wps.shape[0], 1), friction)])
    n = wps.shape[0]
    for i in indices:
        if 0 <= int(i) < n:
            wps[int(i), 4] = friction
    return jsonify(_wps_to_json(wps))

@app.route("/api/inflation", methods=["POST"])
def api_inflation():
    """Return inflation zone points for visualization (no optimization, just the map inflation)."""
    body = request.json
    yaml_path = body["map_yaml"]
    car_width = body.get("car_width", 0.30)
    try:
        img, resolution, origin = ropt.load_map(yaml_path)
        _, _, newly_blocked = ropt.inflate_map(img, resolution, car_width)
        pts = []
        if newly_blocked.any():
            rows, cols = np.where(newly_blocked)
            # Subsample for performance
            step = max(1, len(rows) // 3000)
            for r, c in zip(rows[::step], cols[::step]):
                wx, wy = ropt.pixel_to_world(r, c, resolution, origin, img.shape)
                pts.append([float(wx), float(wy)])
        return jsonify(pts)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    body = request.json
    mu = body.get("mu", 0.34)
    wps = _wps_from_json(body["waypoints"], min_friction=mu)
    yaml_path = body["map_yaml"]
    margin = body.get("margin", 0.20)
    car_width = body.get("car_width", 0.30)
    num_points = body.get("num_points", 150)
    try:
        img, resolution, origin = ropt.load_map(yaml_path)
        # Get track widths for optimization
        img_inflated, free_inflated, newly_blocked = ropt.inflate_map(img, resolution, car_width)
        # Compute track widths at each waypoint
        from scipy.ndimage import distance_transform_edt
        dt = distance_transform_edt(free_inflated) * resolution
        xy = wps[:, :2]
        track_widths = np.zeros(len(xy))
        for i, (x, y) in enumerate(xy):
            r, c = ropt.world_to_pixel(x, y, resolution, origin, img.shape)
            r, c = int(round(r)), int(round(c))
            if 0 <= r < dt.shape[0] and 0 <= c < dt.shape[1]:
                track_widths[i] = dt[r, c]
            else:
                track_widths[i] = margin
        # Run optimization
        turn_bias = body.get("turn_bias", 2.0)
        opt_wps = ropt.optimize_raceline(wps, track_widths, margin=margin,
                                         num_points=num_points, turn_bias=turn_bias)
        # Profile velocity
        v_max = body.get("v_max", 5.0)
        a_max = body.get("a_max", 5.0)
        a_brake = body.get("a_brake", 8.0)
        v_min = body.get("v_min", 0.5)
        opt_wps = ropt.profile_velocity(opt_wps, mu=mu, v_max=v_max, v_min=v_min, a_max=a_max, a_brake=a_brake)
        # Return inflation zone for visualization (sparse — every 4th blocked pixel)
        inflation_pts = []
        if newly_blocked.any():
            rows, cols = np.where(newly_blocked)
            for r, c in zip(rows[::4], cols[::4]):
                wx, wy = ropt.pixel_to_world(r, c, resolution, origin, img.shape)
                inflation_pts.append([float(wx), float(wy)])
        return jsonify({"waypoints": _wps_to_json(opt_wps), "inflation": inflation_pts})
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 400


@app.route("/api/export-mppi", methods=["POST"])
def api_export_mppi():
    """Export the active raceline in Levine 9-column format for the MPPI controller.

    Body: {waypoints: [[x,y,yaw,speed_ratio], ...], v_min, v_max, name, w_tr}
    Writes to MPPI_WP_DIR/<name>.csv and verifies it parses with the MPPI loader.
    """
    body = request.json
    min_friction = body.get("min_friction")
    wps = _wps_from_json(body["waypoints"], min_friction=min_friction)
    v_min = float(body.get("v_min", 1.5))
    v_max = float(body.get("v_max", 7.6))
    name = (body.get("name") or "raceline").strip()
    if not name.endswith(".csv"):
        name += ".csv"
    w_tr = float(body.get("w_tr", 1.0))

    try:
        rows = _to_mppi_rows(wps, v_min, v_max, w_tr_const=w_tr, default_friction=min_friction)
        out_path = MPPI_WP_DIR / name
        _save_mppi_csv(out_path, rows)

        # Sanity-check: re-load with the exact loader settings the MPPI uses
        check = np.loadtxt(str(out_path), delimiter=";", skiprows=3)
        if check.shape != rows.shape or check.shape[1] not in (9, 10):
            return jsonify({"error": f"Round-trip shape mismatch: got {check.shape}, expected {rows.shape}"}), 500

        return jsonify({
            "ok": True,
            "path": str(out_path),
            "rows": int(rows.shape[0]),
            "vx_min": float(rows[:, 5].min()),
            "vx_max": float(rows[:, 5].max()),
            "kappa_min": float(rows[:, 4].min()),
            "kappa_max": float(rows[:, 4].max()),
            "s_total": float(rows[-1, 0] + np.linalg.norm(rows[0, 1:3] - rows[-1, 1:3])),
        })
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 400


@app.route("/api/push", methods=["POST"])
def api_push():
    """Send the active raceline directly to a running node via ROS2 service.

    Body: {target: 'pp'|'mppi', waypoints: [[x,y,yaw,ratio], ...], v_min, v_max}
    PP target sends 4-col; MPPI target encodes vx using v_min/v_max and sends 9-col.
    """
    if STUDIO_NODE is None:
        return jsonify({"error": "ROS node not initialized"}), 500
    body = request.json
    target = body.get("target", "")
    min_friction = body.get("min_friction")
    wps = _wps_from_json(body["waypoints"], min_friction=min_friction)
    if target == "mppi":
        v_min = float(body.get("v_min", 1.5))
        v_max = float(body.get("v_max", 7.6))
        rows = _to_mppi_rows(wps, v_min, v_max, default_friction=min_friction)
        client, fmt = STUDIO_NODE.mppi_client, "mppi"
    elif target == "pp":
        rows = wps
        client, fmt = STUDIO_NODE.pp_client, "pure_pursuit"
    else:
        return jsonify({"error": f"Unknown target {target!r}"}), 400

    if not client.wait_for_service(timeout_sec=1.0):
        return jsonify({"error": f"{target} service not available"}), 503

    req = UpdateRaceline.Request()
    r, c = rows.shape
    req.data   = rows.flatten().astype(float).tolist()
    req.rows   = int(r)
    req.cols   = int(c)
    req.format = fmt

    future = client.call_async(req)
    start = time.time()
    while not future.done() and time.time() - start < 3.0:
        time.sleep(0.02)
    if not future.done():
        return jsonify({"error": "timeout"}), 504
    resp = future.result()
    return jsonify({"success": resp.success, "message": resp.message,
                    "rows": int(r), "format": fmt})


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    global STUDIO_NODE
    rclpy.init()
    STUDIO_NODE = StudioNode()
    threading.Thread(target=rclpy.spin, args=(STUDIO_NODE,), daemon=True).start()
    try:
        port = 5050
        url = f"http://localhost:{port}"
        print(f"\n  Raceline Studio → {url}\n")
        threading.Timer(0.1, lambda: webbrowser.open(url)).start()
        app.run(host="0.0.0.0", port=port, use_reloader=False)
    finally:
        STUDIO_NODE.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
