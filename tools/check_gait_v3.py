"""Check two-stride periodicity, contact and IK reach for the refined walk."""
from pathlib import Path
import sys,math,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'art/production'))
import gait_v3 as g
max_error=0
for i in range(1600):
 t=i/800;p=g.pelvis(t)
 for offset in (0,.485):
  f=g.foot(t+offset);h=(p['x'],0,.94+p['z']);a=(p['x'],f['y'],f['z']);k=g.knee(h,a)
  max_error=max(max_error,abs(math.dist(h,k)-math.hypot(.4,.015)),abs(math.dist(k,a)-math.hypot(.39,.015)))
  sole=f['z']-.138*math.cos(f['roll'])+min(-.22*math.sin(f['roll']),.11*math.sin(f['roll']))
  assert abs(sole-f['lift'])<1e-8
  for key in ('y','z','roll','lift'):assert abs(f[key]-g.foot(t+offset+2)[key])<1e-8
 for key in p:assert abs(p[key]-g.pelvis(t+2)[key])<1e-8
assert max_error<1e-8
print(json.dumps({'phases':1600,'loop':2,'legError':max_error,'speed':g.SPEED,'strideClip':2*g.STRIDE,'durationClip':2*g.CYCLE}))
