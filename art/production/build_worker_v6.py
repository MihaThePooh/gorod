"""Replace primitive anatomy with CC0 MakeHuman topology and a purpose-built hardhat."""
import bpy,bmesh,math,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import export_worker_glb_lite,static_model_glb
src=R/'art/vendor/makehuman-v6';vs=[];groups={};group=''
for line in (src/'base.obj').read_text().splitlines():
 if line.startswith('v '):vs.append(Vector(tuple(map(float,line.split()[1:]))))
 elif line.startswith('g '):group=line[2:];groups.setdefault(group,[])
 elif line.startswith('f '):groups[group].append([int(s.split('/')[0])-1 for s in line.split()[1:]])
for line in (src/'caucasian-male-young.target').read_text().splitlines():
 if line and not line.startswith('#'):
  s=line.split();vs[int(s[0])]+=Vector(tuple(map(float,s[1:])))
body_ids={i for f in groups['body'] for i in f};bottom=min(vs[i].y for i in body_ids);top=max(vs[i].y for i in body_ids);scale=1.8/(top-bottom)
points=[Vector((v.x*scale,-v.z*scale,(v.y-bottom)*scale)) for v in vs]
def joint(name):
 ids={i for f in groups[name] for i in f};return sum((points[i] for i in ids),Vector())/len(ids)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear()
for p in rig.pose.bones:p.location=(0,0,0);p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0);p.scale=(1,1,1)
remove=('Head','Neck','Nose','Ear','Eye','Soft eyebrow','Mouth','Hardhat','Glove','Trouser shell','Canvas belt','Cargo','Sole tread')
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name.startswith(remove):bpy.data.objects.remove(o,do_unlink=True)
mat=next(o for o in bpy.data.objects if o.type=='MESH').data.materials[0]
# The old face and hand placeholders are gone, not hidden beneath new surfaces.
def mesh(name,verts,faces,bone='hips',sub=1,cap=True):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me)
 if cap:
  boundary=[e for e in bm.edges if e.is_boundary]
  if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 vg=o.vertex_groups.new(name=bone);vg.add(list(range(len(me.vertices))),1,'REPLACE');o.parent=rig;m=o.modifiers.new('Static inspection binding','ARMATURE');m.object=rig
 if sub:m=o.modifiers.new('Anatomical surface subdivision','SUBSURF');m.levels=sub;m.render_levels=sub
 return o
def subset(name,faces,fn=lambda i:points[i],bone='head',sub=1):
 ids=sorted({i for f in faces for i in f});mapping={i:n for n,i in enumerate(ids)};return mesh(name,[tuple(fn(i)) for i in ids],[[mapping[i] for i in f] for f in faces],bone,sub)
headfaces=[f for f in groups['body'] if min(points[i].z for i in f)>1.52]
head=subset('Anatomical head and neck',headfaces)
for name in ['helper-l-eye','helper-r-eye']:
 subset('Anatomical '+name,groups[name],bone='head')
for side,sign in [('l',1),('r',-1)]:
 wrist=joint('joint-'+side+'-hand');elbow=joint('joint-'+side+'-elbow');axis=(wrist-elbow).normalized()
 # Clip slightly inside the wrist so the sleeve covers the transition.
 faces=[f for f in groups['body'] if all((points[i]-wrist).dot(axis)>-.026 and points[i].x*sign>.25 and (points[i]-wrist).length<.23 for i in f)]
 target=Vector((sign*.285,-.057,.985));direction=Vector((sign*.04,-.08,-1)).normalized();rotation=axis.rotation_difference(direction)
 def handco(i):
  v=rotation@(points[i]-wrist)
  # A relaxed pose keeps the naturally modelled thumb and finger webbing.
  return target+v
 subset('Anatomical hand '+side,faces,handco,'hand.'+('R' if sign>0 else 'L'),2)
# Continuous pelvis and legs from the anatomical base, inflated into work trousers.
faces=[f for f in groups['body'] if min(points[i].z for i in f)>.19 and max(points[i].z for i in f)<1.025 and max(abs(points[i].x) for i in f)<.31]
def pantsco(i):
 p=points[i].copy();p.x*=.72+.28*max(0,min(1,(p.z-.85)/.175))
 # The trouser fly covers anatomy, while the seat follows rounded gluteal volumes.
 if p.z>.78:p.y=max(p.y,-.132)
 if p.z<.85:
  cx=math.copysign(.12,p.x);a=math.atan2(p.y,p.x-cx);t=max(0,min(1,(p.z-.3)/.55));rx=.058+.027*t;ry=.066+.018*t
  target=Vector((cx+rx*math.cos(a),ry*math.sin(a),p.z));p=p.lerp(target,.65)
 return p
pants=subset('Tailored trousers anatomical seat',faces,pantsco,'hips',0)
# Smooth the base before adding cloth ease; never use a capped ellipse for the seat.
bpy.context.view_layer.objects.active=pants
relax=pants.modifiers.new('Remove anatomical surface detail under fabric','SMOOTH');relax.factor=.6;relax.iterations=7;bpy.ops.object.modifier_apply(modifier=relax.name)
pants.data.update()
for v in pants.data.vertices:
 p=v.co;n=v.normal.copy();z=p.z;a=math.atan2(p.y,p.x-math.copysign(.12,p.x));ease=.030
 if z<.76:ease=.037
 # Sparse diagonal compression folds, rather than repeated bands.
 fold=0
 for height,amp,width,tilt in [(.29,.006,.012,.019),(.35,-.004,.017,-.025),(.49,.007,.015,-.024),(.55,-.004,.018,.025),(.71,.004,.026,.030)]:fold+=amp*math.exp(-((z-height-tilt*math.cos(a)) /width)**2)
 v.co+=n*(ease+fold)
sub=pants.modifiers.new('Fabric surface subdivision','SUBSURF');sub.levels=1;sub.render_levels=1
# Detailed cargo pockets are softly rounded and sit on the outer thighs.
def cube(name,loc,size,bevel=.008):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 b=o.modifiers.new('Rounded tailored edges','BEVEL');b.width=bevel;b.segments=4
 for p in o.data.polygons:p.use_smooth=True
 vg=o.vertex_groups.new(name='hips');vg.add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig;return o
for sign in [-1,1]:
 cube('Cargo pocket v6 '+str(sign),(sign*.217,-.005,.755),(.020,.105,.134),.009)
 cube('Cargo flap v6 '+str(sign),(sign*.225,-.005,.817),(.022,.111,.037),.008)
# A hardhat has a fitted shell and a forward visor, not a circular hat brim.
N=64;rings=22;verts=[];faces=[]
for k in range(rings):
 theta=.035+(math.pi/2-.035)*k/(rings-1)
 for j in range(N):
  a=j*math.tau/N;rr=math.sin(theta);z=1.716+.119*math.cos(theta);x=.119*rr*math.cos(a);y=-.055+.132*rr*math.sin(a)
  # Raised central stiffening rib is integrated with the crown.
  z+=.0035*math.exp(-(x/.012)**2)*rr
  verts.append((x,y,z))
for k in range(rings-1):
 for j in range(N):faces.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
faces.append(tuple(reversed(range(N))))
hat=mesh('Fitted safety helmet shell',verts,faces,'head',1,False);solid=hat.modifiers.new('Shell wall thickness','SOLIDIFY');solid.thickness=.003
# Narrow edge follows the head at the rear; the front projects into a short visor.
v=[];f=[]
for k in range(4):
 t=k/3
 for j in range(N):
  a=j*math.tau/N;front=max(0,-math.sin(a));extra=.005+.065*front**5
  v.append(((.118+extra*t)*math.cos(a),-.055+(.132+extra*t)*math.sin(a),1.718-.007*t+.004*front*t))
for k in range(3):
 for j in range(N):f.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
visor=mesh('Forward safety visor',v,f,'head',1,False);s=visor.modifiers.new('Visor thickness','SOLIDIFY');s.thickness=.003
scene=bpy.context.scene;scene.frame_set(1);scene.render.resolution_x=500;scene.render.resolution_y=750;scene.cycles.samples=20;scene.render.threads=2
out=R/'art/renders/worker-v6';out.mkdir(exist_ok=True);web=R/'client/worker-model-v6';web.mkdir(exist_ok=True)
cam=scene.camera;cam.location=(2.9,-5,2.25);cam.rotation_euler=(Vector((0,0,.96))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/worker-v6.blend'))
rig.animation_data_create();rig.animation_data.action=None
for p in rig.pose.bones:
 for frame in [1,2]:p.keyframe_insert('location',frame=frame);p.keyframe_insert('rotation_quaternion',frame=frame);p.keyframe_insert('scale',frame=frame)
objects=[o for o in bpy.data.objects if o.type=='MESH']
# Export the static review without pretending the newly fitted body is animation-ready.
for o in objects:
 if len(o.data.polygons)>10000:d=o.modifiers.new('Web reduction','DECIMATE');d.ratio=.35
export_worker_glb_lite.write(web/'worker-v6.glb',rig,objects,rig.animation_data.action,30,1,2);static_model_glb.convert(web/'worker-v6.glb')
for o in objects:
 for m in list(o.modifiers):
  if m.name=='Web reduction':o.modifiers.remove(m)
print('WORKER_V6_MODEL_SAVED',flush=True)
for name,pos in [('front',(0,-5,1.3)),('three-quarter',(2.9,-5,2.25)),('side',(5,0,1.3)),('back',(0,5,1.3))]:
 cam.location=pos;cam.rotation_euler=(Vector((0,0,.96))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
