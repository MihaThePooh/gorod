"""Apply the same nose attachment refinement to the saved candidate."""
import bpy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
o=bpy.data.objects['Nose bridge']
if not o.get('attached_v5'):
 for v in o.data.vertices:v.co.y+=.018
 o['attached_v5']=True
bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/worker-v5.blend'))
exec(compile((R/'art/production/export_worker_model_v5.py').read_text(),str(R/'art/production/export_worker_model_v5.py'),'exec'))
