"""Export a lighter static review; leave the high-resolution source untouched."""
import bpy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import export_worker_glb_lite,static_model_glb
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');objects=[o for o in bpy.data.objects if o.type=='MESH']
for o in objects:
 if len(o.data.polygons)>1000:
  d=o.modifiers.new('Web review reduction','DECIMATE');d.ratio=.22
out=R/'client/worker-model-v5/worker-v5.glb';export_worker_glb_lite.write(out,rig,objects,rig.animation_data.action,30,1,2);static_model_glb.convert(out)
