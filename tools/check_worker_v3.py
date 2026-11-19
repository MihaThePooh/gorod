"""Stress-check smooth clothing weights, topology and the evaluated gait."""
from pathlib import Path
import bpy,math,json
r=Path(__file__).resolve().parents[1];source=r/'art/production/build_worker_v3.py';ns={'__file__':str(source)}
exec(compile(source.read_text().split('# Store separate animation actions')[0],str(source),'exec'),ns)
rig=ns['rig'];pose=ns['pose'];max_length=0.;min_z=1.;max_edge_ratio=0.;vertices=0
for obj in bpy.data.objects:
 if obj.type!='MESH':continue
 vertices+=len(obj.data.vertices)
 if obj.vertex_groups:
  for v in obj.data.vertices:
   assert v.groups and len(v.groups)<=4,(obj.name,v.index,'weights')
   assert abs(sum(g.weight for g in v.groups)-1)<1e-5,(obj.name,v.index,'normalization')
for t in [i/48 for i in range(48)]:
 pose('walk',t);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 for side in ('L','R'):
  for name in ('thigh.','shin.'):
   p=rig.pose.bones[name+side];max_length=max(max_length,abs((p.tail-p.head).length-p.bone.length))
  obj=bpy.data.objects['Rounded boot sole '+side].evaluated_get(deps);m=obj.to_mesh();z=min((obj.matrix_world@v.co).z for v in m.vertices);obj.to_mesh_clear();min_z=min(min_z,z)
assert max_length<1e-5
assert min_z>-.008,min_z
# Test elbows/knees across unusually strong bends for invalid or exploding geometry.
for state,t in [('work',0),('work',.25),('walk',.42),('walk',.76)]:
 pose(state,t);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 for name in ('Jacket sleeve L','Jacket sleeve R','Trouser leg L','Trouser leg R'):
  obj=bpy.data.objects[name].evaluated_get(deps);m=obj.to_mesh()
  assert all(math.isfinite(c) for v in m.vertices for c in v.co)
  longest=max((m.vertices[e.vertices[0]].co-m.vertices[e.vertices[1]].co).length for e in m.edges);max_edge_ratio=max(max_edge_ratio,longest)
  assert longest<.18,(name,longest)
  obj.to_mesh_clear()
print(json.dumps({'vertices':vertices,'weightsNormalized':True,'maxInfluences':4,'poses':48,'maxLegError':max_length,'minimumSoleZ':min_z,'maxEvaluatedClothingEdge':max_edge_ratio}))
