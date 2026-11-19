"""Build a new static worker candidate from the user's multi-view video."""
import bpy,math,sys,json,bmesh
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import worker_mesh_v5,export_worker_glb_lite
scene=bpy.context.scene
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear()
for p in rig.pose.bones:p.location=(0,0,0);p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0);p.scale=(1,1,1)
for o in list(bpy.data.objects):
 if o!=rig:bpy.data.objects.remove(o,do_unlink=True)
M={}
for name in ['navy','orange','silver','skin','boot','glove','hair','eye','belt','steel','navyLight','bootSole','lace']:
 m=bpy.data.materials.new('v5 clay '+name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.49,.52,.51,1);bs.inputs['Roughness'].default_value=.75;M[name]=m
pieces=[];worker_mesh_v5.build(M,pieces)
# Details are weighted to their garment, not floating screen-space overlays.
def mesh(name,verts,faces,bone,sub=1):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(M['navy']);vg=o.vertex_groups.new(name=bone);vg.add(list(range(len(verts))),1,'REPLACE')
 for p in me.polygons:p.use_smooth=True
 if sub:o['subdivision_levels']=sub
 pieces.append((o,None));return o
def patch(name,points,bone,thick=.004):
 n=len(points);normal=(Vector(points[1])-Vector(points[0])).cross(Vector(points[2])-Vector(points[0])).normalized();verts=[tuple(Vector(p)+normal*thick) for p in points]+[tuple(Vector(p)-normal*thick) for p in points];faces=[tuple(range(n)),tuple(reversed(range(n,n*2)))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=mesh(name,verts,faces,bone,0);b=o.modifiers.new('Rounded stitched edge','BEVEL');b.width=.003;b.segments=3;return o
def seam(name,points,bone,r=.0015):
 v=[];f=[];n=8
 for k,p in enumerate(points):
  tangent=Vector(points[min(k+1,len(points)-1)])-Vector(points[max(k-1,0)]);tangent.normalize();u=tangent.cross(Vector((0,1,0))).normalized()
  if u.length<.1:u=Vector((1,0,0))
  w=tangent.cross(u).normalized()
  for j in range(n):v.append(tuple(Vector(p)+r*(u*math.cos(j*math.tau/n)+w*math.sin(j*math.tau/n))))
 for k in range(len(points)-1):
  for j in range(n):f.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 f+=[tuple(reversed(range(n))),tuple(range((len(points)-1)*n,len(points)*n))];return mesh(name,v,f,bone,1)
for side,sign in [('L',-1),('R',1)]:
 patch('Folded jacket collar '+side,[(sign*.018,-.079,1.526),(sign*.084,-.072,1.53),(sign*.126,-.102,1.472),(sign*.064,-.145,1.426),(sign*.030,-.119,1.478)],'chest',.005)
 # Cargo pockets wrap around the outer thighs, matching the reference silhouette.
 x=sign*.205
 patch('Cargo pocket '+side,[(x,-.067,.84),(x,-.070,.68),(x,.047,.68),(x,.053,.84)],'thigh.'+side,.004)
 patch('Cargo flap '+side,[(x+sign*.003,-.071,.85),(x+sign*.003,-.072,.812),(x+sign*.003,-.012,.798),(x+sign*.003,.056,.814),(x+sign*.003,.054,.85)],'thigh.'+side,.006)
 # Slanted hand pockets and tailored jacket hem.
 seam('Jacket pocket opening '+side,[(sign*.103,-.143,1.16),(sign*.148,-.139,1.103)],'spine',.0025)
 seam('Jacket hem '+side,[(sign*.008,-.130,1.031),(sign*.12,-.129,1.031),(sign*.176,-.095,1.031)],'spine',.002)
 for z in [.33,.40,.49]:
  pass
 # Sole tread is rounded, separated from the upper; no square slab.
 for i in range(7):
  y=-.19+i*.043;cx=sign*.12;width=.063*(.85 if i==0 else 1)
  patch('Sole tread '+side+str(i),[(cx-width,y-.009,.015),(cx+width,y-.009,.015),(cx+width,y+.009,.015),(cx-width,y+.009,.015)],'foot.'+side,.002)
seam('Zipper piping',[(0,-.130,1.037),(0,-.147,1.15),(0,-.147,1.29),(0,-.139,1.39),(0,-.105,1.474)],'spine',.0022)
patch('Zipper pull',[(-.005,-.151,1.395),(.005,-.151,1.395),(.004,-.154,1.371),(-.004,-.154,1.371)],'chest',.002)
# Jacket shoulder seam curves, not rigid spheres at the joints.
for sign,side in [(-1,'L'),(1,'R')]:
 seam('Shoulder seam '+side,[(sign*.17,-.094,1.48),(sign*.224,-.079,1.44),(sign*.241,-.025,1.426),(sign*.223,.074,1.44)],'chest',.0014)
# Apply anatomical shape refinements before subdivision.
for o,_ in pieces:
 if o.name=='Nose bridge':
  for v in o.data.vertices:v.co.y+=.018
 if o.name.startswith('Hardhat brim'):
  for v in o.data.vertices:
   v.co.x*=.87
   # A forward visor; the rear and sides hug the skull.
   if v.co.y>-.04:v.co.y*=.76
 if o.name.startswith('Hardhat dome'):
  for v in o.data.vertices:v.co.x*=.9;v.co.y*=.94;v.co.z=1.76+(v.co.z-1.76)*.86
 if o.name.startswith('Hardhat rib'):
  for v in o.data.vertices:v.co.x*=.9;v.co.y*=.94;v.co.z=1.76+(v.co.z-1.76)*.86
 if o.name.startswith('Soft eyebrow') or o.name=='Mouth':
  for v in o.data.vertices:v.co.y+=.001
 # Remove the old belt pouch; keep the rest pose but normalize blended chest weights.
 spine=o.vertex_groups.get('spine')
 if spine:
  chest=o.vertex_groups.get('chest') or o.vertex_groups.new(name='chest')
  for v in o.data.vertices:
   w=next((g.weight for g in v.groups if g.group==spine.index),0);t=max(0,min(1,(v.co.z-1.17)/.25));t=t*t*(3-2*t)
   if w and t:chest.add([v.index],w*t,'REPLACE');spine.add([v.index],w*(1-t),'REPLACE')
 mod=o.modifiers.new('Skin binding','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True;o.parent=rig
 if o.get('subdivision_levels'):
  m=o.modifiers.new('Surface refinement','SUBSURF');m.levels=1;m.render_levels=2
# Fuse garment panels and soften their junctions. Preserve source weights spatially.
from mathutils.kdtree import KDTree
for label,prefixes in [('Jacket shell',('Tailored jacket','Jacket sleeve')),('Trouser shell',('Trouser seat','Trouser leg'))]:
 selected=[o for o,_ in pieces if o.name.startswith(prefixes)]
 selected_ptrs={o.as_pointer() for o in selected}
 samples=[]
 for o in selected:
  for v in o.data.vertices:samples.append((v.co.copy(),{o.vertex_groups[g.group].name:g.weight for g in v.groups}))
 tree=KDTree(len(samples))
 for i,(co,w) in enumerate(samples):tree.insert(co,i)
 tree.balance()
 pieces=[(o,b) for o,b in pieces if o.as_pointer() not in selected_ptrs]
 for o in bpy.context.selected_objects:o.select_set(False)
 for o in selected:
  o.select_set(True)
  for m in list(o.modifiers):o.modifiers.remove(m)
 bpy.context.view_layer.objects.active=selected[0];bpy.ops.object.join();obj=selected[0];obj.name=label
 rem=obj.modifiers.new('Unified garment surface','REMESH');rem.mode='VOXEL';rem.voxel_size=.004;rem.use_smooth_shade=True
 bpy.ops.object.modifier_apply(modifier=rem.name)
 relax=obj.modifiers.new('Soften garment transitions','SMOOTH');relax.factor=.65;relax.iterations=5;bpy.ops.object.modifier_apply(modifier=relax.name)
 obj.vertex_groups.clear()
 for v in obj.data.vertices:
  mix={}
  for co,idx,d in tree.find_n(v.co,4):
   for name,w in samples[idx][1].items():mix[name]=mix.get(name,0)+w/(d+.001)**2
  total=sum(mix.values());mix={k:w for k,w in mix.items() if w/total>1e-5};total=sum(mix.values())
  for name,w in mix.items():
   (obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)).add([v.index],w/total,'REPLACE')
 skin=obj.modifiers.new('Skin binding','ARMATURE');skin.object=rig;skin.use_deform_preserve_volume=True
 pieces.append((obj,None))

# Studio lighting makes the geometry itself inspectable.
world=bpy.data.worlds.new('Neutral studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.08,.09,.105,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
for name,pos,power,size in [('Key',(-3,-4,5),500,3),('Fill',(3,-2,3),260,3),('Rim',(0,3,4),600,2)]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;d.energy=power;d.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Review');cam=bpy.data.objects.new('Review',cd);bpy.context.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=2.13
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=520;scene.render.resolution_y=780;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='AgX'
scene.frame_set(1);scene.render.fps=30
out=R/'art/renders/worker-v5';out.mkdir(exist_ok=True);web=R/'client/worker-model-v5';web.mkdir(exist_ok=True)
rig.animation_data_create();rig.animation_data.action=None
for p in rig.pose.bones:
 for f in [1,2]:p.keyframe_insert('location',frame=f);p.keyframe_insert('rotation_quaternion',frame=f);p.keyframe_insert('scale',frame=f)
act=rig.animation_data.action;act.name='static_model_review_v5'
meshes=[o for o,_ in pieces];max_error=max(abs(sum(g.weight for g in v.groups)-1) for o in meshes for v in o.data.vertices);assert max_error<1e-5
cam.location=(2.9,-5,2.25);cam.rotation_euler=(Vector((0,0,.96))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/worker-v5.blend'))
export_worker_glb_lite.write(web/'worker-v5.glb',rig,meshes,act,30,1,2)
import static_model_glb
static_model_glb.convert(web/'worker-v5.glb')
meta={'candidate':5,'method':'manual procedural reconstruction from reference video, not recovered source mesh','meshes':len(meshes),'base_vertices':sum(len(o.data.vertices) for o in meshes),'base_triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),'bones':len(rig.data.bones),'max_weight_error':max_error}
(out/'model.json').write_text(json.dumps(meta,indent=2));print('WORKER_V5_MODEL '+json.dumps(meta),flush=True)
for name,pos in [('front',(0,-5,1.3)),('three-quarter',(2.9,-5,2.25)),('side',(5,0,1.3)),('back',(0,5,1.3))]:
 cam.location=pos;cam.rotation_euler=(Vector((0,0,.96))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
