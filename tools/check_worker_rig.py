"""Evaluate the actual Blender skeleton and deformed soles at every walk frame."""
from pathlib import Path
import bpy,math,json
root=Path(__file__).resolve().parents[1];source=root/'art/production/build_worker_v2.py'
ns={'__file__':str(source)}
exec(compile(source.read_text().split('# Store separate animation actions')[0],str(source),'exec'),ns)
rig=ns['rig'];gait=ns['gait'];pose=ns['pose'];max_length_error=0;min_z=1;max_ground_error=0
for i in range(24):
 t=i/24;pose('walk',t);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 for side,off in [('L',0),('R',.5)]:
  for name in ('thigh.','shin.'):
   p=rig.pose.bones[name+side];max_length_error=max(max_length_error,abs((p.tail-p.head).length-p.bone.length))
  obj=bpy.data.objects['boot sole '+side].evaluated_get(deps);mesh=obj.to_mesh()
  z=min((obj.matrix_world@v.co).z for v in mesh.vertices);obj.to_mesh_clear();min_z=min(min_z,z)
  max_ground_error=max(max_ground_error,abs(z-gait.foot(t+off)['lift']))
assert max_length_error<1e-5
assert min_z>-.003
assert max_ground_error<.012
print(json.dumps({'frames':24,'legLengthError':max_length_error,'minimumSoleZ':min_z,'soleGroundVsTargetMaxError':max_ground_error}))
