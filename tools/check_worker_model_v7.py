"""Check the actual candidate mesh, independent of visual approval."""
import bpy,bmesh,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');report={'bones':len(rig.data.bones),'meshes':[]};coords=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 item={'name':o.name,'vertices':len(bm.verts),'triangles':sum(len(f.verts)-2 for f in bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'finite':all(math.isfinite(c) for v in bm.verts for c in v.co)}
 coords.extend([tuple(o.matrix_world@v.co) for v in o.data.vertices]);bm.free();report['meshes'].append(item)
assert all(x['finite'] and x['zero_area_faces']==0 for x in report['meshes'])
report['bounds']=[[min(v[i] for v in coords),max(v[i] for v in coords)] for i in range(3)]
report['unweighted_vertices']=sum(not v.groups for o in bpy.data.objects if o.type=='MESH' for v in o.data.vertices)
assert report['unweighted_vertices']==0
assert report['bounds'][0][1]-report['bounds'][0][0]<.8, 'Detached geometry outside body silhouette'
report['triangles']=sum(x['triangles'] for x in report['meshes']);(R/'art/renders/worker-v7/qa.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='meshes'}))
