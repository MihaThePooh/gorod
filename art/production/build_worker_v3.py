"""Build a rigid-weight skeletal worker and reproducible eight-direction sprites."""
import bpy,math,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import gait_v3 as gait
from pathlib import Path
from mathutils import Vector, Matrix
R=Path(__file__).resolve().parents[2];out=R/'art/renders/worker-v3';out.mkdir(exist_ok=True)
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
# Smooth, weighted clothing replaces the separated primitive body parts.
for name,c in {'navyLight':(.055,.083,.128),'bootSole':(.035,.029,.022),'lace':(.28,.24,.18)}.items():
 m=bpy.data.materials.new(name);m.use_nodes=True;bsdf=m.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*c,1);bsdf.inputs['Roughness'].default_value=.9;M[name]=m
for name in ('navy','orange','glove','boot'):
 mat=M[name];nodes=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=nodes.get('Principled BSDF')
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=75;noise.inputs['Detail'].default_value=2
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.09;bump.inputs['Distance'].default_value=.004
 links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
 base=tuple(bsdf.inputs['Base Color'].default_value);tone=nodes.new('ShaderNodeTexNoise');tone.inputs['Scale'].default_value=4;tone.inputs['Detail'].default_value=2
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(c*.87 for c in base[:3]),1);ramp.color_ramp.elements[1].color=(*base[:3],1)
 links.new(tone.outputs['Fac'],ramp.inputs['Fac']);links.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
import worker_mesh_v3
worker_mesh_v3.build(M,pieces)
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
 if b:
  group=o.vertex_groups.new(name=b);group.add(list(range(len(o.data.vertices))),1.0,'REPLACE')
 mod=o.modifiers.new('Volume-preserving skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True;o.parent=rig
 if o.name.startswith(('Jacket sleeve','Trouser leg')):
  corr=o.modifiers.new('Joint corrective relaxation','CORRECTIVE_SMOOTH');corr.factor=.20;corr.iterations=3
 if o.get('subdivision_levels'):
  sub=o.modifiers.new('Smooth final surface','SUBSURF');sub.levels=o['subdivision_levels'];sub.render_levels=o['subdivision_levels']
# A removable hammer is controlled by the right hand bone.
h=cube('hammer handle',(.33,-.12,.91),(.035,.035,.36),'belt','hand.R');group=h.vertex_groups.new(name='hand.R');group.add(list(range(len(h.data.vertices))),1,'REPLACE');mod=h.modifiers.new('Skeleton','ARMATURE');mod.object=rig;h.parent=rig
hh=cube('hammer head',(.33,-.12,1.08),(.18,.07,.075),'steel','hand.R');group=hh.vertex_groups.new(name='hand.R');group.add(list(range(len(hh.data.vertices))),1,'REPLACE');mod=hh.modifiers.new('Skeleton','ARMATURE');mod.object=rig;hh.parent=rig
for p in rig.pose.bones:p.rotation_mode='XYZ'
def set_segment(name,head,tail):
 pb=rig.pose.bones[name];rest=pb.bone
 delta=Vector(tail)-Vector(head)
 q=(rest.tail_local-rest.head_local).rotation_difference(delta)
 rot=q.to_matrix().to_4x4()@rest.matrix_local.to_quaternion().to_matrix().to_4x4()
 pb.matrix=Matrix.Translation(Vector(head))@rot
 bpy.context.view_layer.update()

def pose(state,t):
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
 bpy.context.view_layer.update()
 if state=='idle':
  rig.pose.bones['spine'].scale.y=1+.003*math.sin(t*math.tau)
  rig.pose.bones['head'].rotation_euler.x=.008*math.sin(t*math.tau)
 if state=='walk':
  phase=t*2;v=gait.pelvis(phase);rest=rig.data.bones['hips']
  rot=Matrix.Rotation(v['yaw'],4,'Z')@Matrix.Rotation(v['roll'],4,'Y')
  rig.pose.bones['hips'].matrix=Matrix.Translation(rest.head_local+Vector((v['x'],0,v['z'])))@rot@rest.matrix_local.to_quaternion().to_matrix().to_4x4()
  rig.pose.bones['spine'].rotation_euler.y=-.045*math.sin(phase*math.tau)
  rig.pose.bones['spine'].rotation_euler.x=.025
  rig.pose.bones['head'].rotation_euler.y=.020*math.sin(phase*math.tau)
  rig.pose.bones['head'].rotation_euler.z=-v['roll']*.5
  bpy.context.view_layer.update()
  for side,x,offset in [('L',-.145,0),('R',.145,.485)]:
   f=gait.foot(phase+offset)
   thigh=rig.pose.bones['thigh.'+side]
   H=thigh.head.copy();A=Vector((x,f['y'],f['z']))
   l1=rig.data.bones['thigh.'+side].length;l2=rig.data.bones['shin.'+side].length
   d=(A-H).length
   if not abs(l1-l2)<d<l1+l2:raise ValueError(('leg target unreachable',phase,side,d))
   u=(A-H)/d;along=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-along*along))
   forward=Vector((0,-1,0));perp=(forward-u*forward.dot(u)).normalized()
   K=H+u*along+perp*height
   set_segment('thigh.'+side,H,K);set_segment('shin.'+side,K,A)
   restfoot=rig.data.bones['foot.'+side]
   rig.pose.bones['foot.'+side].matrix=Matrix.Translation(A)@Matrix.Rotation(f['roll'],4,'X')@restfoot.matrix_local.to_quaternion().to_matrix().to_4x4()
   swing=math.sin((phase+offset)*math.tau)
   rig.pose.bones['upper_arm.'+side].rotation_euler.x=-(.23 if side=='L' else .215)*math.sin((phase+offset)*math.tau-.08)
   rig.pose.bones['forearm.'+side].rotation_euler.x=-.13-.07*(1+math.sin((phase+offset)*math.tau-.35))
   rig.pose.bones['hand.'+side].rotation_euler.x=.025*math.sin((phase+offset)*math.tau-.65)
  bpy.context.view_layer.update()
 if state=='work':
  rig.pose.bones['upper_arm.R'].rotation_euler.x=-.8-.45*math.sin(t*math.tau)
  rig.pose.bones['forearm.R'].rotation_euler.x=-.65
  rig.pose.bones['spine'].rotation_euler.x=.06+.06*math.sin(t*math.tau)
 h.hide_render=hh.hide_render=state!='work'
# Store separate animation actions, frame rate 12fps.
for state,count in [('idle',8),('walk',48),('work',4)]:
 rig.animation_data_create();rig.animation_data.action=None
 for frame in range(count+1):
  sample_frame=1+frame/count*{'idle':2.5,'walk':gait.CYCLE*2,'work':.5}[state]*24
  bpy.context.scene.frame_set(int(sample_frame));pose(state,frame/count)
  for p in rig.pose.bones:p.keyframe_insert('rotation_euler',frame=sample_frame);p.keyframe_insert('location',frame=sample_frame);p.keyframe_insert('scale',frame=sample_frame)
 action=rig.animation_data.action;action.name='worker_'+state;action.use_fake_user=True
rig.animation_data_clear();pose('idle',0)
world=bpy.data.worlds.new('Town daylight');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[1].default_value=.55;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.80,1)
ld=bpy.data.lights.new('Sunlight','AREA');lo=bpy.data.objects.new('Sunlight',ld);bpy.context.collection.objects.link(lo);lo.location=(-3,-4,6);ld.energy=450;ld.size=4;ld.color=(1,.90,.76);lo.rotation_euler=(Vector((0,0,1))-lo.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Game camera');cam=bpy.data.objects.new('Game camera',cd);bpy.context.collection.objects.link(cam);target=Vector((0,0,.95));cam.location=target+Vector((32,-45,51))*.07;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=2.5
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=1 if '--one-thread' in sys.argv else 2
scene.render.resolution_x=160;scene.render.resolution_y=240;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.fps=24;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.5
if '--direction' not in sys.argv or sys.argv[sys.argv.index('--direction')+1]=='0':
 bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/worker-v3.blend'))
if '--model-only' in sys.argv:
 print('WORKER_ACTION_TIMINGS_SAVED');sys.exit(0)
if '--portrait-only' in sys.argv:
 scene.render.resolution_x=384;scene.render.resolution_y=576;scene.cycles.samples=24;scene.cycles.use_denoising=False
 for direction in ([int(sys.argv[sys.argv.index('--portrait-direction')+1])] if '--portrait-direction' in sys.argv else (0,3,4)):
  rig.rotation_euler.z=direction*math.tau/8;pose(sys.argv[sys.argv.index('--pose-state')+1] if '--pose-state' in sys.argv else 'idle',float(sys.argv[sys.argv.index('--pose-phase')+1]) if '--pose-phase' in sys.argv else 0);bpy.context.view_layer.update()
  scene.render.filepath=str(out/f'portrait-{direction}.png');bpy.ops.render.render(write_still=True)
 print('WORKER_PORTRAITS_OK');sys.exit(0)
frames=[]
for direction in ([int(sys.argv[sys.argv.index('--direction')+1])] if '--direction' in sys.argv else range(8)):
 rig.rotation_euler.z=direction*math.tau/8
 for state,count in [('idle',8),('walk',48),('work',4)]:
  for f in range(count):
   pose(state,f/count);bpy.context.view_layer.update()
   name=f'{direction}-{state}-{f}.png';image_path=out/name
   if image_path.exists() and image_path.read_bytes()[-8:]==bytes.fromhex('49454e44ae426082'):
    frames.append({'direction':direction,'state':state,'frame':f,'file':name});continue
   scene.render.filepath=str(image_path);bpy.ops.render.render(write_still=True)
   frames.append({'direction':direction,'state':state,'frame':f,'file':name})
frames=[{'direction':d,'state':state,'frame':f,'file':f'{d}-{state}-{f}.png'} for d in range(8) for state,count in [('idle',8),('walk',48),('work',4)] for f in range(count)]
(out/'frames.json').write_text(json.dumps({'width':160,'height':240,'fps':24,'cycle_seconds':gait.CYCLE*2,'walk_speed_m_s':gait.SPEED,'stride_m':gait.STRIDE*2,'directions':8,'frames':frames,'world_height_m':1.90},indent=2));print('WORKER_RENDER_BATCH_OK')
