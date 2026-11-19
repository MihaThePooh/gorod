"""Check the actual gait source for periodicity, contact and reachable leg lengths."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'art/production'))
import gait
max_error=0;max_slip=0
for i in range(1000):
 t=i/1000;p=gait.pelvis(t)
 for offset in (0,.5):
  f=gait.foot(t+offset);hip=(p['x'],0,.94+p['z']);ankle=(p['x'],f['y'],f['z']);k=gait.knee(hip,ankle)
  lengths=[math.dist(hip,k),math.dist(k,ankle)]
  max_error=max(max_error,abs(lengths[0]-math.hypot(.4,.015)),abs(lengths[1]-math.hypot(.39,.015)))
  minsole=f['z']-.14*math.cos(f['roll'])+min(-.215*math.sin(f['roll']),.105*math.sin(f['roll']))
  assert abs(minsole-f['lift'])<1e-8
 for key in ('y','z','roll'):
  assert abs(gait.foot(t)[key]-gait.foot(t+1)[key])<1e-8
 # Constant backwards motion relative to the body cancels forward travel in stance.
 if .001<t<gait.STANCE-.001:
  e=.00001;v=(gait.foot(t+e)['y']-gait.foot(t-e)['y'])/(2*e*gait.CYCLE)
  max_slip=max(max_slip,abs(v-gait.SPEED))
assert max_error<1e-8 and max_slip<1e-7
print(json.dumps({'samples':1000,'legLengthError':max_error,'stanceAnkleSlip_m_s':max_slip,'cycle_seconds':gait.CYCLE,'speed_m_s':gait.SPEED,'stride_m':gait.STRIDE}))
