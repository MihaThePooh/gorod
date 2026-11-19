"""Remove a cloth crease artifact and overlap the trouser waist beneath the jacket."""
import bpy,bmesh,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent));import export_worker_glb_lite,static_model_glb
p=bpy.data.objects['Tailored trousers anatomical seat']
if not p.get('waist_finish_v7'):
 bm=bmesh.new();bm.from_mesh(p.data);verts=[v for v in bm.verts if v.co.y>0 and .85<v.co.z<1.025 and abs(v.co.x)<.14]
 for _ in range(10):bmesh.ops.smooth_vert(bm,verts=verts,factor=.25,use_axis_x=True,use_axis_y=True,use_axis_z=True)
 bm.to_mesh(p.data);bm.free()
 for v in p.data.vertices:
  t=max(0,min(1,(v.co.z-.96)/.065));v.co.z+=.035*t*t*(3-2*t)
 p['waist_finish_v7']=True
bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/worker-v7.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new('static_v7')
objects=[o for o in bpy.data.objects if o.type=='MESH']
for o in objects:
 if len(o.data.polygons)>10000:d=o.modifiers.new('Web reduction','DECIMATE');d.ratio=.35
out=R/'client/worker-model-v7/worker-v7.glb';export_worker_glb_lite.write(out,rig,objects,rig.animation_data.action,30,1,2);static_model_glb.convert(out)
for o in objects:
 for m in list(o.modifiers):
  if m.name=='Web reduction':o.modifiers.remove(m)
import os
os.environ['WORKER_DETAIL_PARTS']='seat';exec(compile((R/'art/production/render_worker_v7_details.py').read_text(),str(R/'art/production/render_worker_v7_details.py'),'exec'))
