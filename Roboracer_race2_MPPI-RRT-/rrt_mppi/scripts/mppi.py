"""Independent NumPy MPPI: solve(state, path, speed, grid, origin).

Returns first [acceleration, steering], reference, prediction and diagnostics.
No ROS dependency. Swept-body and braking validation stay enabled.
"""
from dataclasses import dataclass,replace
import math
import numpy as np
from numba import njit
from planning_common import (Config, arc, arc_clear, collides, csv_local_reference, path_clear, scan_grid, sweep_segment_clear, wrap)

@dataclass(frozen=True)
class MPPIConfig:
    # Immutable numerical parameters shared by rollout and cost.
    NX: int = 4  # length of state vector: x = [p_x, p_y, yaw, v]
    NU: int = 2  # length of input vector: u = [a, delta]
    T: int = 1024  # number of sampled control sequences
    H: int = 20  # horizon length
    DT: float = 0.05  # time step [s]
    INTEGRATOR: str = "euler"  # "euler" or "rk4" (bonus)

    # ---------------------------------------------------
    # TODO: you may need to tune the following parameters
    LAMBDA: float = 0.1  # temperature
    U_STD: tuple = (1.0, 0.05)  # std of the sampled inputs [a, delta]
    Q: tuple = (5.0, 5.0, 1.0, 1.0)  # state error cost [x, y, yaw, v]
    Qf: tuple = (5.0, 5.0, 1.0, 1.0)  # final state error cost [x, y, yaw, v]
    R: tuple = (0.01, 5.0)  # input cost [a, delta]
    Rd: tuple = (0.01, 5.0)  # input difference cost [a, delta]
    # ---------------------------------------------------

    WB: float = 0.33  # Wheelbase [m]
    MIN_STEER: float = -0.4189  # minimum steering angle [rad]
    MAX_STEER: float = 0.4189  # maximum steering angle [rad]
    MIN_ACCEL: float = -6.0  # minimum acceleration [m/ss]
    MAX_ACCEL: float = 6.0  # maximum acceleration [m/ss]
    MIN_SPEED: float = 0.0  # minimum speed [m/s]
    MAX_SPEED: float = 10.0  # maximum speed [m/s]


def dynamics(x, u, cfg):
    """Bicycle derivatives for one state or a batch of states."""
    x = np.asarray(x, dtype=float)
    u = np.asarray(u, dtype=float)
    return np.stack((x[..., 3] * np.cos(x[..., 2]),
                     x[..., 3] * np.sin(x[..., 2]),
                     x[..., 3] * np.tan(u[..., 1]) / cfg.WB,
                     u[..., 0]), axis=-1)


def step_euler(x, u, cfg):
    """
    Forward Euler step: x_{k+1} = x_k + f(x_k, u_k) * DT (README Section II.b.i)
    :return: next state, shape (NX,)
    """
    # TODO: fill in the Euler step
    return x + cfg.DT * dynamics(x, u, cfg)


def step_rk4(x, u, cfg):
    """
    Bonus: Runge-Kutta 4 step (README Section II.b.ii)
    :return: next state, shape (NX,)
    """
    # TODO: fill in the RK4 step
    k1 = dynamics(x, u, cfg)
    k2 = dynamics(x + 0.5 * cfg.DT * k1, u, cfg)
    k3 = dynamics(x + 0.5 * cfg.DT * k2, u, cfg)
    k4 = dynamics(x + cfg.DT * k3, u, cfg)
    return x + cfg.DT * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0


def step(x, u, cfg):
    """
    Discretized dynamics F(x, u): the state after DT, holding u constant
    """
    if cfg.INTEGRATOR == "rk4":
        return step_rk4(x, u, cfg)
    return step_euler(x, u, cfg)


def simulate(x0, U, cfg):
    """Single control sequence, returning states with shape (H+1, NX)."""
    return rollout(x0, np.asarray(U)[None], cfg)[0]


def rollout(x0, U, cfg):
    """Vectorize over all samples; loop only over the prediction horizon."""
    U = np.asarray(U, dtype=float)
    states = np.empty((U.shape[0], U.shape[1] + 1, cfg.NX), dtype=float)
    states[:, 0] = x0
    for t in range(U.shape[1]):
        states[:, t + 1] = step(states[:, t], U[:, t], cfg)
    return states


def cost(X, U, ref, cfg, previous_steering=None):
    """Lab8 per-step costs, supporting a single trajectory or a batch.

    Retains wrapped yaw error, terminal Qf, input/slew costs, first-step
    steering continuity and the speed-violation penalty.
    """
    X, U, ref = (np.asarray(a, dtype=float) for a in (X, U, ref))
    error = X[..., 1:, :] - ref[..., 1:, :]
    error[..., 2] = np.arctan2(np.sin(error[..., 2]), np.cos(error[..., 2]))
    weights = np.broadcast_to(np.asarray(cfg.Q), error.shape).copy()
    weights[..., -1, :] = cfg.Qf
    costs = np.sum(weights * error ** 2, axis=-1)
    costs += np.sum(np.asarray(cfg.R) * U ** 2, axis=-1)
    costs[..., 1:] += np.sum(np.asarray(cfg.Rd) * np.diff(U, axis=-2) ** 2, axis=-1)
    if previous_steering is not None:
        costs[..., 0] += cfg.Rd[1] * (U[..., 0, 1] - previous_steering) ** 2
    violation = np.maximum(X[..., 1:, 3] - cfg.MAX_SPEED, 0.)
    violation += np.maximum(cfg.MIN_SPEED - X[..., 1:, 3], 0.)
    return costs + 1000. * violation ** 2


def mppi_step(key, U, x0, ref, cfg, previous_steering=None):
    """NumPy MPPI update; key is a Generator or an integer seed.

    Pass a persistent Generator for fresh samples across successive updates.
    """
    rng = np.random.default_rng(key)
    samples = np.asarray(U)[None] + rng.standard_normal((cfg.T, cfg.H, cfg.NU)) * np.asarray(cfg.U_STD)
    samples = np.clip(samples, [cfg.MIN_ACCEL, cfg.MIN_STEER], [cfg.MAX_ACCEL, cfg.MAX_STEER])
    trajectories = rollout(x0, samples, cfg)
    costs = cost(trajectories, samples, ref, cfg, previous_steering)
    remaining = np.cumsum(costs[:, ::-1], axis=1)[:, ::-1]
    normalized = (remaining - remaining.min(axis=0)) / (np.ptp(remaining, axis=0) + 1e-6)
    weights = np.exp(-normalized / cfg.LAMBDA)
    weights /= weights.sum(axis=0)
    return np.sum(weights[..., None] * samples, axis=0), trajectories, weights


@njit(cache=True,nogil=True)
def advance(state,action,dt,wb,vmax,brake):
    v1=max(0.,min(vmax,state[3]+action[0]*dt))
    # Avoid integrating past zero speed under braking.
    moving_dt=dt
    if action[0]<0 and state[3]+action[0]*dt<0:
        moving_dt=state[3]/(-action[0])
    distance=(state[3]+v1)*moving_dt/2
    curvature=math.tan(action[1])/wb
    pose=arc(state[:3],distance,curvature)
    return np.array([pose[0],pose[1],pose[2],v1]),distance,curvature


@njit(cache=True,nogil=True)
def braking_clear(state,steer,grid,origin,res,body,wb,brake,step):
    return arc_clear(state[:3],state[3]**2/(2*brake),math.tan(steer)/wb,
                     grid,origin,res,body,step)


@njit(cache=True,nogil=True)
def evaluate(initial,samples,reference,previous,grid,origin,res,body,
             dt,wb,vmax,brake,steer_rate,steer_max,amax,q,qf,r,rd,step):
    count,horizon,_=samples.shape
    costs=np.zeros(count); states=np.empty((count,horizon+1,4))
    applied=np.empty_like(samples)
    for k in range(count):
        state=initial.copy(); states[k,0]=state; prev=previous.copy()
        invalid=collides(state[:3],grid,origin,res,body)
        for t in range(horizon):
            action=samples[k,t].copy()
            action[0]=min(amax,max(-brake,action[0]))
            action[1]=min(steer_max,max(-steer_max,action[1]))
            action[1]=min(prev[1]+steer_rate*dt,max(prev[1]-steer_rate*dt,action[1]))
            applied[k,t]=action
            nxt,distance,curvature=advance(state,action,dt,wb,vmax,brake)
            if not invalid and not arc_clear(state[:3],distance,curvature,
                                              grid,origin,res,body,step): invalid=True
            state=nxt; states[k,t+1]=state
            weights=qf if t==horizon-1 else q
            for j in range(4):
                e=state[j]-reference[t+1,j]
                if j==2: e=wrap(e)
                costs[k]+=weights[j]*e*e
            for j in range(2):
                costs[k]+=r[j]*action[j]**2+rd[j]*(action[j]-prev[j])**2
            prev=action
        if not invalid and not braking_clear(state,prev[1],grid,origin,res,body,wb,brake,step):
            invalid=True
        if invalid: costs[k]=math.inf
    return costs,states,applied


def reference_from_path(state,path,speed,cfg):
    # Open local paths NEVER wrap. Decelerate to zero at the available endpoint.
    dist=np.linalg.norm(path[:,:2]-state[:2],axis=1)
    near=int(np.argmin(dist)); local=path[near:]
    if len(local)<2: return np.tile(np.r_[local[-1,:3],0.],(cfg.H+1,1))
    s=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(local[:,:2],axis=0),axis=1))]
    keep=np.r_[True,np.diff(s)>1e-8]; local=local[keep]; s=s[keep]
    yaw=np.unwrap(local[:,2]); curvature=np.abs(np.gradient(yaw,s)) if len(s)>1 else np.zeros(1)
    speeds=np.minimum(speed,np.sqrt(cfg.MAX_LAT_ACCEL/np.maximum(curvature,1e-6)))
    speeds=np.minimum(speeds,np.sqrt(2*cfg.BRAKE_DECEL*np.maximum(0.,s[-1]-s)))
    # Backward pass respects downstream curvature / endpoint braking limits.
    for i in range(len(s)-2,-1,-1):
        speeds[i]=min(speeds[i],math.sqrt(speeds[i+1]**2+2*cfg.BRAKE_DECEL*(s[i+1]-s[i])))
    ref=np.empty((cfg.H+1,4)); progress=0.
    for t in range(cfg.H+1):
        v=float(np.interp(progress,s,speeds))
        ref[t]=[np.interp(progress,s,local[:,0]),np.interp(progress,s,local[:,1]),
                np.interp(progress,s,yaw),v]
        progress=min(s[-1],progress+v*cfg.DT)
    return ref


@njit(cache=True, nogil=True)
def rollout_validity(trajectories, controls, grid, origin, res, body, wb, brake, step, vmax):
    from_dummy = 0
    valid=np.ones(len(trajectories),np.bool_)
    for k in range(len(trajectories)):
        x=trajectories[k]
        if not np.isfinite(x).all() or np.any(x[:,3]<-1e-6) or np.any(x[:,3]>vmax+1e-6):
            valid[k]=False
        elif not path_clear(x[:,:3],grid,origin,res,body): valid[k]=False
        elif not braking_clear(x[-1],controls[k,-1,1],grid,origin,res,body,wb,brake,step): valid[k]=False
    return valid


def reference_steering(reference,cfg):
    """Bicycle-model feedforward for the MPPI sampling mean, not a command."""
    distance=np.linalg.norm(np.diff(reference[:,:2],axis=0),axis=1)
    heading=wrap(np.diff(reference[:,2]))
    curvature=np.divide(heading,distance,out=np.zeros_like(heading),where=distance>1e-6)
    return np.clip(np.arctan(cfg.WB*curvature),-cfg.MAX_STEER,cfg.MAX_STEER)


def stationary_recovery_controls(state,previous,reference,cfg):
    """Two deterministic proposals for the low-speed sampling deadlock.

    Hold/brake while centering steering, then optionally accelerate straight.
    These are only proposals: the same projection, rollout, swept-body and
    terminal-braking checks decide whether either may be used.
    """
    proposals=np.zeros((2,cfg.H,2));limit=cfg.MAX_STEER_RATE*cfg.DT
    target=min(.8,max(0.,float(reference[0,3])))
    for moving in range(2):
        speed=max(0.,float(state[3]));steering=float(previous[1])
        for t in range(cfg.H):
            steering=0. if abs(steering)<=limit+1e-12 else steering-math.copysign(limit,steering)
            if moving and steering==0.:
                acceleration=float(np.clip((target-speed)/cfg.DT,-cfg.BRAKE_DECEL,cfg.MAX_ACCEL))
            else:acceleration=-min(cfg.BRAKE_DECEL,speed/cfg.DT)
            proposals[moving,t]=[acceleration,steering]
            speed=max(0.,speed+acceleration*cfg.DT)
    return proposals


class MPPI:
    """NumPy Lab8 rollout/cost, masked weights and safe final validation."""
    def __init__(self,cfg):
        self.cfg=cfg
        self.rng=np.random.default_rng(cfg.random_seed+1)
        self.U=np.zeros((cfg.H,2)); self.previous=np.zeros(2); self.steering_feedforward=None
        from dataclasses import replace
        self.lab=replace(MPPIConfig(), **{n:getattr(cfg,n) for n in
            ('T','H','DT','INTEGRATOR','LAMBDA','U_STD','Q','Qf','R','Rd','MAX_SPEED','MAX_ACCEL')},
            WB=cfg.WB,MIN_STEER=-cfg.MAX_STEER,MAX_STEER=cfg.MAX_STEER,
            MIN_ACCEL=-cfg.BRAKE_DECEL,MIN_SPEED=0.)
        self.roll=rollout
        self.score=cost
        self.last_trajectories=None; self.last_weights=None

    def reset(self):
        self.U.fill(0.)
        # The stop command holds the last published steering angle. Its
        # warm start must represent that actuator state, rather than zero.
        self.U[:,1]=self.previous[1]
        self.previous[0]=0.; self.steering_feedforward=None
        # Last steering is kept to constrain the next published transition.

    def project(self,u):
        c=self.cfg; u=np.array(u,copy=True)
        u[:,:,0]=np.clip(u[:,:,0],-c.BRAKE_DECEL,c.MAX_ACCEL)
        previous=np.full(len(u),self.previous[1])
        for t in range(c.H):
            u[:,t,1]=np.clip(u[:,t,1],-c.MAX_STEER,c.MAX_STEER)
            u[:,t,1]=np.clip(u[:,t,1],previous-c.MAX_STEER_RATE*c.DT,previous+c.MAX_STEER_RATE*c.DT)
            previous=u[:,t,1]
        return u

    def valid(self,x,u,grid,origin):
        c=self.cfg
        return rollout_validity(x,u,grid,origin,c.grid_resolution_m,c.geometry(),
                                c.WB,c.BRAKE_DECEL,c.collision_step_m,c.MAX_SPEED)

    def solve(self,state,path,speed,grid,origin):
        c=self.cfg; ref=reference_from_path(state,path,min(speed,c.MAX_SPEED),c)
        nominal=np.vstack((self.U[1:],self.U[-1:]))
        feedforward=reference_steering(ref,c)
        # Carry optimized residuals while moving the sampling mean with the
        # RRT* path curvature. Projection, Lab8 rollout/cost and body checks
        # still decide which control, if any, can actually be published.
        if self.steering_feedforward is None:
            nominal[:,1]=feedforward
        else:
            old=np.r_[self.steering_feedforward[1:],self.steering_feedforward[-1]]
            nominal[:,1]+=feedforward-old
        noise=self.rng.standard_normal((c.T,c.H,2))*np.array(c.U_STD)
        samples=nominal[None]+noise; samples[0]=nominal
        # Coast-to-stop candidate respects nonnegative speed even under Euler.
        v=state[3]
        for t in range(c.H):
            samples[1,t]=[-min(c.BRAKE_DECEL,v/c.DT),self.previous[1]]
            v=max(0.,v+samples[1,t,0]*c.DT)
        if state[3]<.1 and c.T>2:
            recovery=stationary_recovery_controls(state,self.previous,ref,c)
            samples[2:min(c.T,4)]=recovery[:min(c.T,4)-2]
        samples=self.project(samples)
        x=np.asarray(self.roll(state,samples,self.lab),dtype=float)
        valid=self.valid(x,samples,grid,origin)
        self.last_trajectories=x; self.last_weights=np.zeros((c.T,c.H))
        if not valid.any():
            self.reset(); return None,ref,None,{'valid_samples':0,'reason':'no_safe_rollout'}
        costs=np.asarray(self.score(x,samples,ref,self.lab,float(self.previous[1])))
        valid &= np.isfinite(costs).all(axis=1)
        if not valid.any():
            self.reset(); return None,ref,None,{'valid_samples':0,'reason':'nonfinite_cost'}
        remaining=np.cumsum(costs[valid,::-1],axis=1)[:,::-1]
        normalized=(remaining-remaining.min(axis=0))/(np.ptp(remaining,axis=0)+1e-6)
        w=np.exp(-normalized/c.LAMBDA); w/=w.sum(axis=0)
        self.last_weights[valid]=w
        mean=self.project(np.sum(w[:,:,None]*samples[valid],axis=0)[None])
        pred=np.asarray(self.roll(state,mean,self.lab),dtype=float)
        fallback=not self.valid(pred,mean,grid,origin)[0]
        if fallback:
            indices=np.flatnonzero(valid); k=indices[np.argmin(costs[valid].sum(axis=1))]
            chosen=samples[k]; prediction=x[k]
        else: chosen=mean[0]; prediction=pred[0]
        self.U=chosen.copy(); self.steering_feedforward=feedforward.copy()
        return chosen[0].copy(),ref,prediction,{'valid_samples':int(valid.sum()),
                'mean_rejected':fallback,'reason':'tracking','backend':'lab8_numpy'}


