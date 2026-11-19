"""Match shell depth to the anatomical head and extend the forward-only visor."""
import bpy,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent));import export_worker_glb_lite,static_model_glb
hat=bpy.data.objects['Fitted safety helmet shell']
if not hat.get('depth_fit_v6'):
 for v in hat.data.vertices:v.co.y=-.055+(v.co.y+.055)*.132/.109
 visor=bpy.data.objects['Forward safety visor']
 for i,v in enumerate(visor.data.vertices):
  k=i//64;j=i%64;t=k/3;a=j*math.tau/64;front=max(0,-math.sin(a));extra=.005+.065*front**5
  v.co.x=(.118+extra*t)*math.cos(a);v.co.y=-.055+(.132+extra*t)*math.sin(a)
 hat['depth_fit_v6']=True
bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/worker-v6.blend'))

print('HAT_FIT_SAVED',flush=True)
