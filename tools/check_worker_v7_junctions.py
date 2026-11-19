"""Confirm the skin actually enters the garment; do not infer contact from one render."""
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
R=Path(__file__).resolve().parents[1];deps=bpy.context.evaluated_depsgraph_get();jacket=bpy.data.objects['Jacket shell'];neck=bpy.data.objects['Anatomical head and neck'];tree=BVHTree.FromObject(jacket,deps)
def inside(p):
 direction=Vector((1,.173,.071)).normalized();point=p.copy();hits=0
 for _ in range(32):
  co,normal,index,distance=tree.ray_cast(point,direction,2)
  if co is None:break
  hits+=1;point=co+direction*.00001
 return bool(hits%2)
min_z=min(v.co.z for v in neck.data.vertices)
low=[v.co.copy() for v in neck.data.vertices if v.co.z<min_z+.015]
assert len(low)>10
count=sum(inside(v) for v in low);ratio=count/len(low);assert ratio>.95,(count,len(low),ratio)
report={'neck_lower_vertices':len(low),'inside_closed_jacket':count,'inside_ratio':ratio,'neck_min_z':min(v.co.z for v in neck.data.vertices),'jacket_max_z':max(v.co.z for v in jacket.data.vertices)}
(R/'art/renders/worker-v7/junctions.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
