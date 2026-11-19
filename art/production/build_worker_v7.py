"""Fix the anatomical/garment junctions and construct a cap-style industrial hardhat."""
import bpy,bmesh,math,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import export_worker_glb_lite,static_model_glb
scene=bpy.context.scene;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear()
for p in rig.pose.bones:p.location=(0,0,0);p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0);p.scale=(1,1,1)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
neck=bpy.data.objects['Anatomical head and neck'];old_low=min(v.co.z for v in neck.data.vertices)
# Extend the skin beneath the collar and flare into a concealed upper chest.
for v in neck.data.vertices:
 w=smooth((1.59-v.co.z)/.07)
 if w:
  v.co.x*=1+.75*w;v.co.y=-.025+(v.co.y+.025)*(1+.65*w);v.co.z-=.10*w
neck.data.update()
# Correct the inflated hip volume while opening the pinched waist transition.
pants=bpy.data.objects['Tailored trousers anatomical seat']
for v in pants.data.vertices:
 z=v.co.z;w=math.exp(-((z-.91)/.105)**4)
 v.co.x*=1-.04*w
 if v.co.y>0:
  v.co.y*=1-.24*w
  # Loose fabric bridges the anatomical cleft instead of tracing the buttocks.
  fill=math.exp(-(v.co.x/.085)**4)*smooth((z-.825)/.055)*smooth((1.015-z)/.05)
  v.co.y+=max(0,.090-v.co.y)*fill
 # A slight waist allowance makes the upper/lower garment transition gradual.
 v.co.x*=1+.10*smooth((z-.945)/.08)
pants.data.update()
for o in bpy.data.objects:
 if o.name.startswith(('Cargo pocket v6','Cargo flap v6')):o.location.x*=.94
# Replace rectangular shoulder caps with a deltoid-shaped envelope.
jacket=bpy.data.objects['Jacket shell'];moved=0
for v in jacket.data.vertices:
 p=v.co.copy();w=smooth((abs(p.x)-.105)/.07)*smooth((p.z-1.34)/.065)
 if not w:continue
 c=Vector((math.copysign(.17,p.x),0,1.39));r=Vector((.112,.113,.108));d=p-c;q=math.sqrt(sum((d[i]/r[i])**2 for i in range(3)))
 if q>1:
  target=c+d/q;delta=(target-p)*w
  if delta.length>.035:delta*=.035/delta.length
  v.co+=delta;moved+=1
jacket.data.update()
# Local relaxation blends the projected shoulder into the original sleeve.
bm=bmesh.new();bm.from_mesh(jacket.data);sel=[v for v in bm.verts if v.co.z>1.34 and abs(v.co.x)>.12]
for _ in range(12):bmesh.ops.smooth_vert(bm,verts=sel,factor=.45,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(jacket.data);bm.free()
for o in list(bpy.data.objects):
 if o.name.startswith(('Fitted safety helmet','Forward safety visor','Shoulder seam')):bpy.data.objects.remove(o,do_unlink=True)
clay=jacket.data.materials[0]
helmet=bpy.data.materials.new('Industrial helmet neutral shell');helmet.use_nodes=True;bs=helmet.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.49,.52,.51,1);bs.inputs['Roughness'].default_value=.40
band=bpy.data.materials.new('Helmet inner suspension');band.use_nodes=True;band.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.075,.08,.085,1)
def mesh(name,vertices,faces,material=helmet,sub=0,thickness=None):
 me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(material)
 for p in me.polygons:p.use_smooth=True
 vg=o.vertex_groups.new(name='head');vg.add(list(range(len(me.vertices))),1,'REPLACE');o.parent=rig
 if sub:s=o.modifiers.new('Rounded moulded shell','SUBSURF');s.levels=sub;s.render_levels=sub
 if thickness:s=o.modifiers.new('Moulded plastic thickness','SOLIDIFY');s.thickness=thickness
 return o
# A lower-profile shell has vertical lower walls, a broad crown ridge and side ribs.
N=80;K=26;v=[];f=[];cy=-.052;rx=.119;ry=.143;base=1.716;h=.121
for k in range(K):
 t=.025+(math.pi/2-.025)*k/(K-1);rr=math.sin(t)
 for j in range(N):
  a=j*math.tau/N;x=rx*rr*math.cos(a);y=cy+ry*rr*math.sin(a);z=base+h*max(0,math.cos(t))**.72
  ridge=(.008*math.exp(-(x/.018)**4)+.004*math.exp(-((abs(x)-.055)/.009)**4))*smooth((z-base)/.025)
  v.append((x,y,z+ridge))
for k in range(K-1):
 for j in range(N):f.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
f.append(tuple(reversed(range(N))))
mesh('Construction hardhat ribbed crown',v,f,sub=1,thickness=.003)
# Only a narrow bead runs around the rear and sides.
v=[];f=[]
for k in range(3):
 for j in range(N):
  a=j*math.tau/N;t=k/2;v.append(((rx+.004*t)*math.cos(a),cy+(ry+.004*t)*math.sin(a),base+.001-.004*t))
for k in range(2):
 for j in range(N):f.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
mesh('Construction hardhat edge bead',v,f,sub=1,thickness=.003)
# The bill is a broad forward-facing, near-trapezoidal moulding, not a circular brim.
v=[];f=[];nx=32;ny=7
for row in range(ny):
 t=row/(ny-1)
 for col in range(nx):
  u=-1+2*col/(nx-1);x=u*(.098+.010*t);inner=cy-ry*math.sqrt(max(.01,1-(u*.098/rx)**2));outer=-.281+.018*abs(u)**4
  y=inner*(1-t)+outer*t;z=base+.002-.009*t+.006*(1-u*u)*t;v.append((x,y,z))
for row in range(ny-1):
 for col in range(nx-1):i=row*nx+col;f.append((i,i+1,i+nx+1,i+nx))
mesh('Construction hardhat forward peak',v,f,sub=1,thickness=.004)
# An internal headband and accessory sockets make the construction explicit.
v=[];f=[]
for z in [base-.010,base+.009]:
 for j in range(N):a=j*math.tau/N;v.append((.105*math.cos(a),cy+.127*math.sin(a),z))
for j in range(N):f.append((j,(j+1)%N,N+(j+1)%N,N+j))
mesh('Construction hardhat inner suspension',v,f,band,thickness=.003)
def box(name,loc,size,material=helmet):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);b=o.modifiers.new('Rounded moulding','BEVEL');b.width=.0025;b.segments=3
 for p in o.data.polygons:p.use_smooth=True
 vg=o.vertex_groups.new(name='head');vg.add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig;return o
for sign in [-1,1]:
 box('Hardhat accessory mounting socket '+str(sign),(sign*.119,cy+.020,base+.012),(.007,.031,.018))
 box('Hardhat accessory socket recess '+str(sign),(sign*.123,cy+.020,base+.015),(.002,.019,.005),band)
box('Hardhat rear adjuster',(0,cy+.131,base-.004),(.040,.016,.018),band)
out=R/'art/renders/worker-v7';out.mkdir(exist_ok=True);web=R/'client/worker-model-v7';web.mkdir(exist_ok=True)
scene.frame_set(1);scene.render.resolution_x=500;scene.render.resolution_y=750;scene.cycles.samples=16;scene.render.threads=2
cam=scene.camera;cam.location=(2.9,-5,2.25);cam.rotation_euler=(Vector((0,0,.96))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/worker-v7.blend'))
rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new('static_model_v7')
objects=[o for o in bpy.data.objects if o.type=='MESH']
for o in objects:
 if len(o.data.polygons)>10000:d=o.modifiers.new('Web reduction','DECIMATE');d.ratio=.35
export_worker_glb_lite.write(web/'worker-v7.glb',rig,objects,rig.animation_data.action,30,1,2);static_model_glb.convert(web/'worker-v7.glb')
for o in objects:
 for m in list(o.modifiers):
  if m.name=='Web reduction':o.modifiers.remove(m)
meta={'neck_base_before':old_low,'neck_base_after':min(v.co.z for v in neck.data.vertices),'shoulder_vertices_reshaped':moved,'helmet_reference':'3M H-700 cap-style construction, own geometry without branding','game_integration':False}
(out/'changes.json').write_text(json.dumps(meta,indent=2));print('WORKER_V7_EXPORTED '+json.dumps(meta),flush=True)
for name,pos in [('three-quarter',(2.9,-5,2.25)),('back',(0,5,1.3)),('side',(5,0,1.3))]:
 cam.location=pos;cam.rotation_euler=(Vector((0,0,.96))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
