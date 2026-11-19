"""Build a rigid-weight skeletal worker and reproducible eight-direction sprites."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];out=R/'art/renders/worker-v1';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
M={}
for name,c in {'navy':(.035,.055,.09),'orange':(.90,.21,.025),'silver':(.62,.63,.56),'skin':(.45,.27,.16),'boot':(.06,.045,.03),'glove':(.31,.30,.25),'hair':(.055,.03,.02),'eye':(.025,.035,.03),'belt':(.20,.12,.055),'steel':(.24,.26,.26)}.items():
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.87;p.inputs['Specular IOR Level'].default_value=.18;M[name]=m
pieces=[]
def finish(o,name,mat,bone):
 o.name=name;o.data.materials.append(M[mat]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for f in o.data.polygons:f.use_smooth=True
 pieces.append((o,bone));return o
def ell(name,loc,scale,mat,bone):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=loc);o=bpy.context.object;o.scale=scale;return finish(o,name,mat,bone)
def cube(name,loc,scale,mat,bone):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=scale
 bevel=o.modifiers.new('Soft cloth edges','BEVEL');bevel.width=.025;bevel.segments=2
 return finish(o,name,mat,bone)
def limb(name,a,b,radius,mat,bone):
 mid=(Vector(a)+Vector(b))/2;length=(Vector(b)-Vector(a)).length
 o=ell(name,mid,(radius,radius,length/2+radius*.25),mat,bone);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
# Front of the worker faces -Y. Units are metres.
ell('trousers hips',(0,0,.95),(.20,.125,.17),'navy','hips')
# A tailored continuous vest avoids balloon-like torso silhouettes.
rings=[(.99,.18,.115),(1.07,.205,.13),(1.11,.21,.135),(1.15,.215,.137),(1.19,.22,.14),(1.23,.225,.14),(1.42,.24,.135),(1.49,.16,.10)]
verts=[]
for z,w,d in rings:
 for x,y in ((w,-d*.65),(w*.65,-d),(-w*.65,-d),(-w,-d*.65),(-w,d*.65),(-w*.65,d),(w*.65,d),(w,d*.65)):
  verts.append((x,y,z))
faces=[]
for i in range(len(rings)-1):
 for j in range(8):faces.append((i*8+j,i*8+(j+1)%8,(i+1)*8+(j+1)%8,(i+1)*8+j))
faces.extend([tuple(reversed(range(8))),tuple(range((len(rings)-1)*8,len(rings)*8))])
mesh=bpy.data.meshes.new('tailored vest');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('tailored vest',mesh);bpy.context.collection.objects.link(o)
o.data.materials.append(M['orange']);o.data.materials.append(M['silver'])
for poly in mesh.polygons:
 if poly.index//8 in (2,4):poly.material_index=1
pieces.append((o,'spine'))
cube('open vest',(0,-.146,1.28),(.065,.025,.42),'navy','spine')
for x in (-.13,.13):
 cube('reflective front stripe',(x,-.143,1.36),(.033,.018,.23),'silver','spine')
 cube('reflective rear stripe',(x,.143,1.36),(.033,.018,.23),'silver','spine')
ell('neck',(0,0,1.52),(.073,.07,.09),'skin','head')
ell('head',(0,-.005,1.66),(.115,.105,.15),'skin','head')
ell('hair',(0,.025,1.73),(.116,.090,.10),'hair','head')
ell('nose',(0,-.111,1.66),(.024,.035,.030),'skin','head')
for x in (-.045,.045):
 ell('eye',(x,-.103,1.693),(.012,.010,.012),'eye','head')
 cube('brow',(x,-.106,1.716),(.032,.013,.009),'hair','head')
 ell('ear',(math.copysign(.114,x),0,1.66),(.020,.028,.040),'skin','head')
# Helmet dome and brim form a single consistent costume.
ell('helmet dome',(0,0,1.78),(.145,.135,.105),'orange','head')
ell('helmet brim',(0,-.025,1.755),(.173,.174,.020),'orange','head')
for x in (-.055,.055):cube('helmet rib',(x,-.005,1.855),(.015,.17,.015),'orange','head')
cube('belt',(0,-.005,1.0),(.40,.26,.055),'belt','hips')
cube('tool pouch',(.18,-.13,.92),(.13,.09,.18),'belt','hips')
for side,x in [('L',-.145),('R',.145)]:
 hip=(x,0,.94);knee=(x,-.015,.54);ankle=(x,0,.15)
 limb('trouser upper '+side,hip,knee,.105,'navy','thigh.'+side)
 ell('knee '+side,knee,(.088,.085,.09),'navy','shin.'+side)
 limb('trouser lower '+side,knee,ankle,.084,'navy','shin.'+side)
 cube('knee patch '+side,(x,-.093,.53),(.13,.025,.13),'navy','shin.'+side)
 cube('boot sole '+side,(x,-.055,.045),(.19,.32,.07),'boot','foot.'+side)
 ell('boot '+side,(x,-.04,.115),(.099,.167,.095),'boot','foot.'+side)
 shoulder=(math.copysign(.235,x),0,1.45);elbow=(math.copysign(.31,x),-.015,1.18);wrist=(math.copysign(.33,x),-.055,.99)
 limb('sleeve upper '+side,shoulder,elbow,.090,'navy','upper_arm.'+side)
 ell('elbow '+side,elbow,(.074,.074,.075),'navy','forearm.'+side)
 limb('sleeve lower '+side,elbow,wrist,.075,'navy','forearm.'+side)
 ell('glove '+side,(wrist[0],wrist[1]-.015,.94),(.066,.065,.09),'glove','hand.'+side)
 ell('thumb '+side,(wrist[0]*.88,wrist[1]-.055,.96),(.025,.035,.055),'glove','hand.'+side)
# Real armature, rigid vertex groups per clothing segment.
arm=bpy.data.armatures.new('Worker skeleton');rig=bpy.data.objects.new('Worker rig',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
def bone(n,a,b,parent=None):
 e=arm.edit_bones.new(n);e.head=a;e.tail=b
 if parent:e.parent=arm.edit_bones[parent]
bone('hips',(0,0,.90),(0,0,1.02));bone('spine',(0,0,1.02),(0,0,1.49),'hips');bone('head',(0,0,1.49),(0,0,1.84),'spine')
for side,x in [('L',-.145),('R',.145)]:
 bone('thigh.'+side,(x,0,.94),(x,-.015,.54),'hips');bone('shin.'+side,(x,-.015,.54),(x,0,.15),'thigh.'+side);bone('foot.'+side,(x,0,.15),(x,-.2,.10),'shin.'+side)
 sx=math.copysign(.235,x);ex=math.copysign(.31,x);wx=math.copysign(.33,x)
 bone('upper_arm.'+side,(sx,0,1.45),(ex,-.015,1.18),'spine');bone('forearm.'+side,(ex,-.015,1.18),(wx,-.055,.99),'upper_arm.'+side);bone('hand.'+side,(wx,-.055,.99),(wx,-.065,.86),'forearm.'+side)
bpy.ops.object.mode_set(mode='OBJECT')
for o,b in pieces:
 group=o.vertex_groups.new(name=b);group.add(list(range(len(o.data.vertices))),1.0,'REPLACE');mod=o.modifiers.new('Skeleton','ARMATURE');mod.object=rig;o.parent=rig
# A removable hammer is controlled by the right hand bone.
h=cube('hammer handle',(.33,-.12,.91),(.035,.035,.36),'belt','hand.R');group=h.vertex_groups.new(name='hand.R');group.add(list(range(len(h.data.vertices))),1,'REPLACE');mod=h.modifiers.new('Skeleton','ARMATURE');mod.object=rig;h.parent=rig
hh=cube('hammer head',(.33,-.12,1.08),(.18,.07,.075),'steel','hand.R');group=hh.vertex_groups.new(name='hand.R');group.add(list(range(len(hh.data.vertices))),1,'REPLACE');mod=hh.modifiers.new('Skeleton','ARMATURE');mod.object=rig;hh.parent=rig
for p in rig.pose.bones:p.rotation_mode='XYZ'
def pose(state,t):
 for p in rig.pose.bones:p.rotation_euler=(0,0,0);p.location=(0,0,0)
 if state=='walk':
  s=math.sin(t*math.tau)
  for side,sign in [('L',1),('R',-1)]:
   rig.pose.bones['thigh.'+side].rotation_euler.x=.5*s*sign
   rig.pose.bones['shin.'+side].rotation_euler.x=max(0,-s*sign)*.6
   rig.pose.bones['upper_arm.'+side].rotation_euler.x=-.38*s*sign
  rig.pose.bones['hips'].location.y=.018*abs(s)
 if state=='work':
  rig.pose.bones['upper_arm.R'].rotation_euler.x=-.8-.45*math.sin(t*math.tau)
  rig.pose.bones['forearm.R'].rotation_euler.x=-.65
  rig.pose.bones['spine'].rotation_euler.x=.06+.06*math.sin(t*math.tau)
 h.hide_render=hh.hide_render=state!='work'
# Store separate animation actions, frame rate 12fps.
for state,count in [('idle',2),('walk',6),('work',4)]:
 rig.animation_data_create();rig.animation_data.action=None
 for frame in range(count+1):
  pose(state,frame/count);bpy.context.scene.frame_set(frame+1)
  for p in rig.pose.bones:p.keyframe_insert('rotation_euler',frame=frame+1);p.keyframe_insert('location',frame=frame+1)
 action=rig.animation_data.action;action.name='worker_'+state;action.use_fake_user=True
rig.animation_data_clear();pose('idle',0)
world=bpy.data.worlds.new('Town daylight');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[1].default_value=.55;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.80,1)
ld=bpy.data.lights.new('Sunlight','AREA');lo=bpy.data.objects.new('Sunlight',ld);bpy.context.collection.objects.link(lo);lo.location=(-3,-4,6);ld.energy=450;ld.size=4;ld.color=(1,.90,.76);lo.rotation_euler=(Vector((0,0,1))-lo.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Game camera');cam=bpy.data.objects.new('Game camera',cd);bpy.context.collection.objects.link(cam);target=Vector((0,0,.95));cam.location=target+Vector((32,-45,51))*.07;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=2.5
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=192;scene.render.resolution_y=288;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.fps=12;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.5
bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/worker-v1.blend'))
frames=[]
for direction in range(8):
 rig.rotation_euler.z=direction*math.tau/8
 for state,count in [('idle',1),('walk',6),('work',4)]:
  for f in range(count):
   pose(state,f/count);bpy.context.view_layer.update()
   name=f'{direction}-{state}-{f}.png';scene.render.filepath=str(out/name);bpy.ops.render.render(write_still=True)
   frames.append({'direction':direction,'state':state,'frame':f,'file':name})
(out/'frames.json').write_text(json.dumps({'width':192,'height':288,'fps':12,'directions':8,'frames':frames,'world_height_m':1.90},indent=2));print('WORKER_88_FRAMES_OK')
