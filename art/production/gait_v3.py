"""Deterministic walk timing and sagittal leg IK in metres, independent of Blender."""
import math
CYCLE=1.05
STANCE=.62
HALF_STEP=.32
SPEED=2*HALF_STEP/(STANCE*CYCLE)
STRIDE=SPEED*CYCLE
FRAMES=24

def smooth(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)

def roll_at(p):
    keys=[(0,-.16),(.10,0),(.43,0),(.62,.28),(.80,.10),(.94,-.16),(1,-.16)]
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if a<=p<=b:return x+(y-x)*smooth((p-a)/(b-a))
    return -.16

def foot(phase):
    p=phase%1
    if p<STANCE:
        y=-HALF_STEP+2*HALF_STEP*p/STANCE
        lift=0.
    else:
        t=(p-STANCE)/(1-STANCE)
        y=HALF_STEP-2*HALF_STEP*smooth(t)
        lift=.105*math.sin(math.pi*t)**1.5*(1+.04*math.sin(phase*math.pi))
    roll=roll_at(p)
    # Raise the ankle so the rotated boot sole never penetrates the ground.
    ankle=.138*math.cos(roll)-min(-.22*math.sin(roll),.11*math.sin(roll))+lift
    return {'y':y,'z':ankle,'roll':roll,'stance':p<STANCE,'lift':lift}

def pelvis(phase):
    t=phase*math.tau;p=phase%1
    keys=[(0,-.070),(.10,-.095),(.27,-.045),(.40,-.025),(.515,-.068),(.615,-.093),(.785,-.047),(.915,-.027),(1,-.070)]
    z=keys[0][1]
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if a<=p<=b:
            z=x+(y-x)*smooth((p-a)/(b-a));break
    return {'x':.018*math.cos(t)+.0015*math.sin(phase*math.pi),
            'z':z+.0015*math.sin(phase*math.pi),
            'roll':.018*math.cos(t),'yaw':.025*math.sin(t)}

def knee(hip,ankle,l1=math.hypot(.4,.015),l2=math.hypot(.39,.015)):
    # Positive bend is towards the front of a worker facing -Y.
    x=ankle[1]-hip[1];z=ankle[2]-hip[2];d=math.hypot(x,z)
    if not abs(l1-l2)<d<l1+l2:
        raise ValueError(f'Unreachable leg target {d:.6f}, maximum {l1+l2:.6f}')
    uy,uz=x/d,z/d
    along=(l1*l1-l2*l2+d*d)/(2*d)
    height=math.sqrt(max(0,l1*l1-along*along))
    py,pz=uz,-uy
    if py>0:py,pz=-py,-pz
    return (hip[0],hip[1]+uy*along+py*height,hip[2]+uz*along+pz*height)
