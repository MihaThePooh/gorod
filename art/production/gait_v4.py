"""Approximate key poses measured from the user's multi-angle screen recording."""
import math
CYCLE=1.10
STANCE=.60
HALF_STEP=.32
SPEED=2*HALF_STEP/(STANCE*CYCLE)
STRIDE=SPEED*CYCLE

def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def curve(p,keys):
 p=p%1
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if a<=p<=b:return x+(y-x)*smooth((p-a)/(b-a))
 return keys[-1][1]
def contact_offset(roll):
 pivot=.11 if roll<0 else -.22
 return pivot-(pivot*math.cos(roll)+.138*math.sin(roll))
def foot(phase):
 p=phase%1
 if p<STANCE:
  y=-HALF_STEP+2*HALF_STEP*p/STANCE;lift=0
 else:
  t=(p-STANCE)/(1-STANCE);a=HALF_STEP+contact_offset(.48);b=-HALF_STEP+contact_offset(-.23);y=a+(b-a)*smooth(t);lift=.155*math.sin(math.pi*t)**1.35
 roll=curve(p,[(0,-.23),(.09,0),(.40,0),(.50,.16),(.60,.48),(.69,.55),(.81,.08),(.95,-.23),(1,-.23)])
 if p<STANCE:y+=contact_offset(roll)
 ankle=.138*math.cos(roll)-min(-.22*math.sin(roll),.11*math.sin(roll))+lift
 return {'y':y,'z':ankle,'roll':roll,'stance':p<STANCE,'lift':lift}
def pelvis(phase):
 p=phase%1;t=p*math.tau
 z=curve(p,[(0,-.075),(.10,-.095),(.25,-.028),(.40,-.045),(.50,-.075),(.60,-.095),(.75,-.028),(.90,-.045),(1,-.075)])
 return {'x':.020*math.cos(t),'z':z,'roll':.026*math.cos(t),'yaw':.047*math.sin(t)}
