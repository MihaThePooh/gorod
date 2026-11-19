"""Minimal glTF2 skin/animation exporter without NumPy or optional addons."""
import bpy,struct,json,math
from mathutils import Quaternion

def write(path,rig,objects,action,fps,start,end):
 data=bytearray();views=[];accessors=[]
 def acc(values,kind,component=5126,target=None,limits=False):
  width={'SCALAR':1,'VEC3':3,'VEC4':4,'MAT4':16}[kind];flat=[v for row in values for v in (row if isinstance(row,(tuple,list)) else [row])]
  while len(data)%4:data.append(0)
  offset=len(data);fmt={5126:'f',5125:'I',5123:'H'}[component];data.extend(struct.pack('<'+str(len(flat))+fmt,*flat));view={'buffer':0,'byteOffset':offset,'byteLength':len(data)-offset}
  if target:view['target']=target
  views.append(view);a={'bufferView':len(views)-1,'componentType':component,'count':len(flat)//width,'type':kind}
  if limits:
   a['min']=[min(flat[i::width]) for i in range(width)];a['max']=[max(flat[i::width]) for i in range(width)]
  accessors.append(a);return len(accessors)-1
 bones=list(rig.data.bones);mapping={b.name:i for i,b in enumerate(bones)}
 nodes=[{'name':'Blender Z-up conversion','rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)],'children':[]}]
 def trs(matrix):
  loc,q,scale=matrix.decompose();return {'translation':list(loc),'rotation':[q.x,q.y,q.z,q.w],'scale':list(scale)}
 for b in bones:
  local=b.parent.matrix_local.inverted()@b.matrix_local if b.parent else b.matrix_local
  node={'name':b.name,**trs(local)}
  if b.children:node['children']=[mapping[c.name]+1 for c in b.children]
  nodes.append(node)
  if not b.parent:nodes[0]['children'].append(mapping[b.name]+1)
 ibm=[]
 for b in bones:
  m=b.matrix_local.inverted();ibm.append([m[row][col] for col in range(4) for row in range(4)])
 skin={'joints':[i+1 for i in range(len(bones))],'inverseBindMatrices':acc(ibm,'MAT4'),'skeleton':next(i+1 for i,b in enumerate(bones) if not b.parent)}
 mats=[];meshes=[]
 for obj in objects:
  if 'hammer' in obj.name.lower():continue
  mods=[]
  for mod in obj.modifiers:
   if mod.type in ('ARMATURE','CORRECTIVE_SMOOTH'):mods.append((mod,'show_viewport',mod.show_viewport));mod.show_viewport=False
   if mod.type=='SUBSURF':mods.append((mod,'levels',mod.levels));mod.levels=min(1,mod.levels)
  bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(deps);mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=deps);mesh.calc_loop_triangles();normal=obj.matrix_world.to_3x3().inverted().transposed();positions=[];normals=[];joints=[];weights=[]
  for v in mesh.vertices:
   positions.append(list(obj.matrix_world@v.co));normals.append(list((normal@v.normal).normalized()))
   pairs=[]
   for g in v.groups:
    name=obj.vertex_groups[g.group].name
    if name in mapping and g.weight>1e-7:pairs.append((mapping[name],g.weight))
   pairs=sorted(pairs,key=lambda x:-x[1])[:4] or [(0,1)]
   total=sum(w for j,w in pairs);pairs += [(0,0)]*(4-len(pairs));joints.append([j for j,w in pairs]);weights.append([w/total for j,w in pairs])
  attrs={'POSITION':acc(positions,'VEC3',target=34962,limits=True),'NORMAL':acc(normals,'VEC3',target=34962),'JOINTS_0':acc(joints,'VEC4',5123,34962),'WEIGHTS_0':acc(weights,'VEC4',target=34962)}
  primitives=[]
  for mi,slot in enumerate(obj.material_slots):
   indices=[i for tri in mesh.loop_triangles if tri.material_index==mi for i in tri.vertices]
   if not indices:continue
   mat=slot.material;node=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if mat and mat.use_nodes else None
   color=list(node.inputs['Base Color'].default_value) if node else list(mat.diffuse_color) if mat else [.5,.5,.5,1]
   mats.append({'name':mat.name if mat else 'default','pbrMetallicRoughness':{'baseColorFactor':color,'roughnessFactor':.86,'metallicFactor':0},'doubleSided':True})
   primitives.append({'attributes':attrs,'indices':acc(indices,'SCALAR',5125,34963),'material':len(mats)-1})
  ev.to_mesh_clear()
  for mod,key,value in mods:setattr(mod,key,value)
  meshes.append({'name':obj.name,'primitives':primitives});nodes.append({'name':obj.name,'mesh':len(meshes)-1,'skin':0});nodes[0]['children'].append(len(nodes)-1)
 rig.animation_data_create();rig.animation_data.action=action;scene=bpy.context.scene;scene.render.fps=fps
 frames=list(range(start,end+1));time=acc([(f-start)/fps for f in frames],'SCALAR',limits=True);channels=[];samplers=[]
 transforms={b.name:{k:[] for k in ['translation','rotation','scale']} for b in bones}
 for f in frames:
  scene.frame_set(f);bpy.context.view_layer.update()
  for b in bones:
   pb=rig.pose.bones[b.name];local=pb.parent.matrix.inverted()@pb.matrix if pb.parent else pb.matrix
   for k,value in trs(local).items():transforms[b.name][k].append(value)
 for b in bones:
  for k,values in transforms[b.name].items():
   samplers.append({'input':time,'output':acc(values,'VEC4' if k=='rotation' else 'VEC3'),'interpolation':'LINEAR'});channels.append({'sampler':len(samplers)-1,'target':{'node':mapping[b.name]+1,'path':k}})
 doc={'asset':{'version':'2.0','generator':'LivingTown minimal exporter'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':nodes,'meshes':meshes,'skins':[skin],'materials':mats,'animations':[{'name':action.name,'samplers':samplers,'channels':channels}],'buffers':[{'byteLength':len(data)}],'bufferViews':views,'accessors':accessors}
 raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);data+=b'\0'*((-len(data))%4)
 path.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(raw)+8+len(data))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(data),0x004e4942)+data)
 rig.animation_data_clear();print('GLB_EXPORTED',path.name,len(data))
