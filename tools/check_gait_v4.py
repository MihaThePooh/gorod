"""Verify analytical heel/toe contact and the reference-loop seam."""
from pathlib import Path
import sys,math,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'art/production'))
import gait_v4 as g
for key in g.foot(0):
 if isinstance(g.foot(0)[key],bool):continue
 assert abs(g.foot(0)[key]-g.foot(1)[key])<1e-9,key
contacts=[]
for a,b,pivot in [(0,.089,.11),(.41,.599,-.22)]:
 points=[]
 for i in range(100):
  p=a+(b-a)*i/99;f=g.foot(p)
  points.append(-g.SPEED*g.CYCLE*p+f['y']+pivot*math.cos(f['roll'])+.138*math.sin(f['roll']))
 error=max(points)-min(points);assert error<1e-9;contacts.append(error)
print(json.dumps({'cycle':g.CYCLE,'speed':g.SPEED,'heel_toe_contact_drift':max(contacts),'loop':True}))
