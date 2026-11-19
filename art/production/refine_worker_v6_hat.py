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
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');objects=[o for o in bpy.data.objects if o.type=='MESH']
for o in objects:
 if len(o.data.polygons)>10000:d=o.modifiers.new('Web reduction','DECIMATE');d.ratio=.35
p=R/'client/worker-model-v6/worker-v6.glb';export_worker_glb_lite.write(p,rig,objects,rig.animation_data.action if rig.animation_data else None,30,1,2);static_model_glb.convert(p)
for o in objects:
 for m in list(o.modifiers):
  if m.name=='Web reduction':o.modifiers.remove(m)
s=bpy.context.scene;c=s.camera;t=Vector((0,0,.96));c.location=(2.9,-5,2.25);c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(R/'art/renders/worker-v6/three-quarter.png');bpy.ops.render.render(write_still=True)
# Reuse the same close-up setup after modifying only the helmet.
exec(compile((R/'art/production/render_worker_v6_details.py').read_text(),str(R/'art/production/render_worker_v6_details.py'),'exec'))
