"""Shared numerical configuration, car geometry and path safety. No ROS imports."""
from dataclasses import dataclass,fields,replace
import math
import numpy as np
from numba import njit

@dataclass(frozen=True)
class Config:
    reference_distance_m: float = 3.0
    INTEGRATOR: str = 'euler'
    track: str = 'levine'
    waypoints_path: str = ''
    map_frame: str = 'map'
    odom_topic: str = '/ego_racecar/odom'
    # Pose origin when Odometry.child_frame_id is empty (the real-car PF).
    # This names the pose origin, not the coordinate frame in its header.
    odom_pose_frame: str = ''
    scan_topic: str = '/scan'
    scan_min_valid_range_m: float = 0.05  # Discard invalid near-field returns; do not clear their rays.
    drive_topic: str = '/drive'
    # Odometry pose may be at the laser/base center rather than rear axle.
    pose_to_rear_axle_x_m: float = 0.0
    pose_to_rear_axle_y_m: float = 0.0
    car_length_m: float = 0.575
    car_width_m: float = 0.305
    car_body_center_x_m: float = 0.1651
    footprint_margin_m: float = 0.02
    WB: float = 0.3302
    MAX_STEER: float = 0.4189
    MAX_STEER_RATE: float = 1.5
    MAX_ACCEL: float = 1.5
    BRAKE_DECEL: float = 2.0
    MAX_SPEED: float = 1.5
    MAX_LAT_ACCEL: float = 1.5
    speed_scale: float = 0.4
    grid_resolution_m: float = 0.05
    grid_size_m: float = 12.0
    scan_timeout_s: float = 0.25
    odom_timeout_s: float = 0.2
    scan_pose_tolerance_s: float = 0.08
    collision_step_m: float = 0.04
    control_rate_hz: float = 20.0
    max_control_latency_s: float = 0.15
    clear_confirmations: int = 3
    T: int = 192
    H: int = 20
    DT: float = 0.05
    LAMBDA: float = 1.0
    U_STD: tuple = (0.8, 0.16)
    Q: tuple = (8.0, 8.0, 2.0, 2.0)  # x,y,yaw,v
    Qf: tuple = (16.0, 16.0, 4.0, 3.0)
    R: tuple = (0.05, 0.1)
    Rd: tuple = (0.2, 2.0)
    random_seed: int = 7
    visualize: bool = True

    def validate(self):
        for f in fields(self):
            v=getattr(self,f.name)
            if isinstance(v,(float,int,tuple)) and not np.isfinite(v).all():
                raise ValueError(f'{f.name} must be finite')
        for key in ('reference_distance_m','WB','MAX_STEER','MAX_STEER_RATE','MAX_ACCEL',
                    'BRAKE_DECEL','MAX_SPEED','MAX_LAT_ACCEL','grid_resolution_m','grid_size_m',
                    'scan_timeout_s','odom_timeout_s','scan_pose_tolerance_s','collision_step_m',
                    'control_rate_hz','max_control_latency_s','T','H','DT','LAMBDA',
                    'clear_confirmations','car_length_m','car_width_m'):
            if getattr(self,key)<=0:raise ValueError(f'{key} must be positive')
        if self.MAX_STEER>=np.pi/2:raise ValueError('Invalid steering limit')
        if self.scan_min_valid_range_m<0:raise ValueError('Invalid minimum scan range')
        if self.footprint_margin_m<0 or self.speed_scale<=0 or self.T<2:
            raise ValueError('Invalid margin, speed scale or sample count')
        for key,n in (('U_STD',2),('Q',4),('Qf',4),('R',2),('Rd',2)):
            v=np.asarray(getattr(self,key))
            if v.shape!=(n,) or np.any(v<0):raise ValueError(f'Invalid {key}')
        if min(self.U_STD)<=0:raise ValueError('Sampling std must be positive')
        if self.INTEGRATOR not in ('euler','rk4'):raise ValueError('Invalid integrator')
        return self

    def geometry(self):
        return np.array([self.car_length_m,self.car_width_m,
                         self.car_body_center_x_m,self.footprint_margin_m])


@njit(cache=True, nogil=True)
def wrap(a):
    return (a+math.pi)%(2*math.pi)-math.pi


@njit(cache=True, nogil=True)
def collides(pose, grid, origin, resolution, body, padding=0.0, padding_y=-1.0):
    c,s=math.cos(pose[2]),math.sin(pose[2])
    cx,cy=pose[0]+body[2]*c,pose[1]+body[2]*s
    py=padding if padding_y<0 else padding_y
    hl,hw=body[0]/2+body[3]+padding,body[1]/2+body[3]+py
    ex,ey=abs(c)*hl+abs(s)*hw,abs(s)*hl+abs(c)*hw
    height,width=grid.shape
    if (cx-ex<=origin[0] or cy-ey<=origin[1] or
        cx+ex>=origin[0]+width*resolution or cy+ey>=origin[1]+height*resolution):
        return True
    half=resolution/2
    # Include cells touching the boundary, including exact grid-line contact.
    c0=max(0,int(math.floor((cx-ex-origin[0])/resolution-1e-9)))
    c1=min(width-1,int(math.floor((cx+ex-origin[0])/resolution+1e-9)))
    r0=max(0,int(math.floor((cy-ey-origin[1])/resolution-1e-9)))
    r1=min(height-1,int(math.floor((cy+ey-origin[1])/resolution+1e-9)))
    projection=half*(abs(c)+abs(s))
    for row in range(r0,r1+1):
        for col in range(c0,c1+1):
            if grid[row,col]==0: continue
            dx=origin[0]+(col+0.5)*resolution-cx
            dy=origin[1]+(row+0.5)*resolution-cy
            margin = body[3] if grid[row,col]>0 else 0.0
            cell_hl=body[0]/2+margin+padding
            cell_hw=body[1]/2+margin+py
            cell_ex=abs(c)*cell_hl+abs(s)*cell_hw
            cell_ey=abs(s)*cell_hl+abs(c)*cell_hw
            if (abs(dx)<=cell_ex+half+1e-10 and abs(dy)<=cell_ey+half+1e-10 and
                abs(c*dx+s*dy)<=cell_hl+projection+1e-10 and
                abs(-s*dx+c*dy)<=cell_hw+projection+1e-10): return True
    return False


@njit(cache=True, nogil=True)
def arc(pose, distance, curvature):
    x,y,yaw=pose[0],pose[1],pose[2]
    angle=curvature*distance
    if abs(curvature)<1e-10:
        return np.array([x+distance*math.cos(yaw),y+distance*math.sin(yaw),yaw])
    return np.array([x+(math.sin(yaw+angle)-math.sin(yaw))/curvature,
                     y-(math.cos(yaw+angle)-math.cos(yaw))/curvature,wrap(yaw+angle)])


@njit(cache=True,nogil=True)
def sweep_segment_clear(a,b,grid,origin,resolution,body):
    # Refine ONLY ambiguous enclosures. Unknown cells remain unknown.
    # Dubins edges are circular; Euler rollouts interpolate linearly in XY/yaw.
    angle=wrap(b[2]-a[2]); dx=b[0]-a[0]; dy=b[1]-a[1]
    chord=math.hypot(dx,dy); mean_yaw=a[2]+angle/2
    lateral=-math.sin(mean_yaw)*dx+math.cos(mean_yaw)*dy
    circular=abs(lateral)<1e-7 and abs(angle)>1e-8 and chord>1e-9
    length=chord
    curvature=0.0
    if circular:
        length=chord*abs(angle)/(2*math.sin(abs(angle)/2))
        curvature=angle/length
    radius=math.hypot(abs(body[2])+body[0]/2+body[3],body[1]/2+body[3])
    if collides(a,grid,origin,resolution,body) or collides(b,grid,origin,resolution,body): return False
    lo=np.empty(40);hi=np.empty(40);dep=np.empty(40,np.int64)
    lo[0]=0.;hi[0]=1.;dep[0]=0;count=1
    visits=0
    while count:
        visits+=1
        if visits>256:return False
        count-=1;u=lo[count];v=hi[count];depth=dep[count];mid=(u+v)/2
        if circular:
            qa=arc(a,u*length,curvature);qb=arc(a,v*length,curvature);qm=arc(a,mid*length,curvature)
        else:
            qa=np.array([a[0]+u*dx,a[1]+u*dy,wrap(a[2]+u*angle)])
            qb=np.array([a[0]+v*dx,a[1]+v*dy,wrap(a[2]+v*angle)])
            qm=np.array([a[0]+mid*dx,a[1]+mid*dy,wrap(a[2]+mid*angle)])
        if collides(qm,grid,origin,resolution,body): return False
        c=math.cos(qm[2]);ss=math.sin(qm[2]);hx=(qb[0]-qa[0])/2;hy=(qb[1]-qa[1])/2
        da=abs(angle)*(v-u);rotation=radius*da/2
        sagitta=math.hypot(hx,hy)*math.tan(da/4) if circular else 0.
        px=abs(c*hx+ss*hy)+rotation+sagitta
        py=abs(-ss*hx+c*hy)+rotation+sagitta
        if not collides(qm,grid,origin,resolution,body,px,py):continue
        # Fail closed if precision limit is exhausted; never clear blind cells.
        if depth>=20:return False
        lo[count]=mid;hi[count]=v;dep[count]=depth+1;count+=1
        lo[count]=u;hi[count]=mid;dep[count]=depth+1;count+=1
    return True


@njit(cache=True,nogil=True)
def arc_clear(pose,distance,curvature,grid,origin,resolution,body,step):
    count=max(1,int(math.ceil(abs(distance)*(1+abs(curvature))/step)))
    for i in range(count):
        a=arc(pose,distance*i/count,curvature);b=arc(pose,distance*(i+1)/count,curvature)
        if not sweep_segment_clear(a,b,grid,origin,resolution,body):return False
    return not collides(pose,grid,origin,resolution,body)


@njit(cache=True,nogil=True)
def path_clear(path,grid,origin,resolution,body):
    if len(path)==0:return False
    for i in range(len(path)-1):
        if abs(wrap(path[i+1,2]-path[i,2]))>=math.pi/2:return False
        if not sweep_segment_clear(path[i,:3],path[i+1,:3],grid,origin,resolution,body):return False
    return not collides(path[-1,:3],grid,origin,resolution,body)


@njit(cache=True, nogil=True)
def scan_grid(ranges,angle_min,angle_increment,range_min,range_max,
              laser_pose,rear_pose,origin,size,resolution,body):
    grid=np.full((size,size),-1,np.int8)
    # Free observed rays first, mark ALL occupied endpoints afterwards.
    endpoints=np.empty((len(ranges),2),np.int64); hits=0
    limit=math.sqrt(2)*size*resolution
    for i in range(len(ranges)):
        value=ranges[i]
        if math.isnan(value) or value<range_min: continue
        distance=min(value,range_max,limit)
        if not math.isfinite(distance) or distance<=0: continue
        a=laser_pose[2]+angle_min+i*angle_increment
        c,s=math.cos(a),math.sin(a)
        count=int(math.ceil(distance/(resolution/2)))
        for j in range(count):
            d=j*resolution/2
            col=int(math.floor((laser_pose[0]+d*c-origin[0])/resolution))
            row=int(math.floor((laser_pose[1]+d*s-origin[1])/resolution))
            if 0<=row<size and 0<=col<size: grid[row,col]=0
        if math.isfinite(value) and value<range_max and value<=limit:
            col=int(math.floor((laser_pose[0]+value*c-origin[0])/resolution))
            row=int(math.floor((laser_pose[1]+value*s-origin[1])/resolution))
            if 0<=row<size and 0<=col<size:
                endpoints[hits,0]=row; endpoints[hits,1]=col; hits+=1
    # Sensor cannot see through its own body: free UNKNOWN cells only, within
    # the actual occupied body, never its safety margin and never known hits.
    c,s=math.cos(rear_pose[2]),math.sin(rear_pose[2])
    for row in range(size):
        for col in range(size):
            if grid[row,col]!=-1: continue
            dx=origin[0]+(col+0.5)*resolution-rear_pose[0]
            dy=origin[1]+(row+0.5)*resolution-rear_pose[1]
            if (abs(c*dx+s*dy-body[2])<=body[0]/2+resolution/2*(abs(c)+abs(s)) and
                abs(-s*dx+c*dy)<=body[1]/2+resolution/2*(abs(c)+abs(s))): grid[row,col]=0
    for i in range(hits): grid[endpoints[i,0],endpoints[i,1]]=100
    return grid














def csv_local_reference(waypoints, index, distance):
    """Ordered CSV geometry only; no RRT search or geometric-path veto.

    Motion is still authorized solely by the common MPPI swept-body checks.
    Wrap the global closed route once, never the local prediction horizon.
    """
    rows=[waypoints[index % len(waypoints)]]; length=0.
    for offset in range(1,len(waypoints)+1):
        q=waypoints[(index+offset)%len(waypoints)]
        length+=float(np.linalg.norm(q[:2]-rows[-1][:2]));rows.append(q)
        if length>=distance:break
    return np.asarray(rows)


