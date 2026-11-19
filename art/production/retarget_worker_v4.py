"""Reconstruct the observed gait on our own mesh; never import the service's asset."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix,Euler
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import gait_v4 as gait
out=R/'client/worker-motion';out.mkdir(exist_ok=True)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
for o in bpy.context.selected_objects:o.select_set(False)
rig.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=rig
# Procedural colour/noise remains in the blend; the review exports base colours.
def export(path,action,fps,start,end):
 import export_worker_glb_lite
 export_worker_glb_lite.write(path,rig,meshes,action,fps,start,end)
old=bpy.data.actions.get('worker_walk')
if not (out/'worker-before.glb').exists():export(out/'worker-before.glb',old,24,1,52)
rig.animation_data_clear()
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode='EDIT');eb=rig.data.edit_bones

def add(name,head,tail,parent=None):
 b=eb.new(name);b.head=head;b.tail=tail
 if parent:b.parent=eb[parent]
 return b
add('root',(0,0,0),(0,0,.15));eb['hips'].parent=eb['root']
eb['spine'].tail=(0,0,1.28)
add('chest',(0,0,1.28),(0,0,1.49),'spine');add('neck',(0,0,1.49),(0,0,1.58),'chest');eb['head'].parent=eb['neck']
for side,sign in [('L',-1),('R',1)]:
 add('clavicle.'+side,(0,0,1.43),(sign*.235,0,1.45),'chest');eb['upper_arm.'+side].parent=eb['clavicle.'+side]
 add('toe.'+side,(sign*.145,-.16,.05),(sign*.145,-.26,.05),'foot.'+side)
bpy.ops.object.mode_set(mode='OBJECT')
# Split the old torso weighting over the newly articulated chest.
for obj in meshes:
 spine=obj.vertex_groups.get('spine')
 if not spine:continue
 chest=obj.vertex_groups.get('chest') or obj.vertex_groups.new(name='chest')
 for vertex in obj.data.vertices:
  w=next((g.weight for g in vertex.groups if g.group==spine.index),0)
  if w<=0:continue
  z=(obj.matrix_world@vertex.co).z;t=max(0,min(1,(z-1.16)/.23));t=t*t*(3-2*t)
  if t>0:chest.add([vertex.index],w*t,'REPLACE')
  spine.add([vertex.index],w*(1-t),'REPLACE')
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'

def segment(name,head,tail):
 pb=rig.pose.bones[name];rest=pb.bone
 q=(rest.tail_local-rest.head_local).rotation_difference(Vector(tail)-Vector(head))
 pb.matrix=Matrix.Translation(Vector(head))@q.to_matrix().to_4x4()@rest.matrix_local.to_quaternion().to_matrix().to_4x4()
 bpy.context.view_layer.update()
def pose(phase):
 for pb in rig.pose.bones:pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
 v=gait.pelvis(phase);rest=rig.data.bones['hips']
 rig.pose.bones['hips'].matrix=Matrix.Translation(rest.head_local+Vector((v['x'],0,v['z'])))@Matrix.Rotation(v['yaw'],4,'Z')@Matrix.Rotation(v['roll'],4,'Y')@rest.matrix_local.to_quaternion().to_matrix().to_4x4()
 rig.pose.bones['spine'].rotation_quaternion=Euler((.025,-v['roll']*.35,-v['yaw']*.25)).to_quaternion()
 rig.pose.bones['chest'].rotation_quaternion=Euler((-.009,-v['roll']*.45,-v['yaw']*.35)).to_quaternion()
 rig.pose.bones['neck'].rotation_quaternion=Euler((-.009,v['roll']*.5,v['yaw']*.35)).to_quaternion()
 bpy.context.view_layer.update()
 metrics=[]
 for side,sign,offset in [('L',-1,0),('R',1,.5)]:
  f=gait.foot(phase+offset);H=rig.pose.bones['thigh.'+side].head.copy();A=Vector((sign*.115,f['y'],f['z']))
  l1=rig.data.bones['thigh.'+side].length;l2=rig.data.bones['shin.'+side].length;u=A-H;dist=u.length
  if not abs(l1-l2)<dist<l1+l2:raise ValueError(('unreachable leg',phase,side,dist))
  u.normalize();along=(l1*l1-l2*l2+dist*dist)/(2*dist);h=math.sqrt(max(0,l1*l1-along*along));forward=Vector((0,-1,0));perp=(forward-u*forward.dot(u)).normalized();K=H+u*along+perp*h
  segment('thigh.'+side,H,K);segment('shin.'+side,K,A)
  foot=rig.pose.bones['foot.'+side];rest=foot.bone
  foot.matrix=Matrix.Translation(A)@Matrix.Rotation(f['roll'],4,'X')@rest.matrix_local.to_quaternion().to_matrix().to_4x4();bpy.context.view_layer.update()
  # Arms counter the opposite leg; forearm flex increases toward the front.
  theta=-.34*math.cos((phase+offset)*math.tau-.18);bend=.26+.13*max(0,math.sin(theta)*2)
  S=rig.pose.bones['upper_arm.'+side].head.copy()
  arm=Vector((sign*.065,-math.sin(theta)*.27,-math.cos(theta)*.27)).normalized()*rig.data.bones['upper_arm.'+side].length
  E=S+arm;fore=Vector((sign*.018,-math.sin(theta+bend)*.19,-math.cos(theta+bend)*.19)).normalized()*rig.data.bones['forearm.'+side].length;W=E+fore
  segment('upper_arm.'+side,S,E);segment('forearm.'+side,E,W)
  hand=Vector((sign*.006,-math.sin(theta+bend+.04)*.12,-math.cos(theta+bend+.04)*.12)).normalized()*rig.data.bones['hand.'+side].length
  segment('hand.'+side,W,W+hand)
  metrics.append({'side':side,'ankle_error':(rig.pose.bones['shin.'+side].tail-A).length,'reach':dist})
 return metrics
rig.animation_data_create();rig.animation_data.action=None
checks=[];count=33
for i in range(count+1):
 scene.frame_set(i+1);checks.extend(pose(i/count))
 for pb in rig.pose.bones:
  pb.keyframe_insert('location',frame=i+1);pb.keyframe_insert('rotation_quaternion',frame=i+1);pb.keyframe_insert('scale',frame=i+1)
action=rig.animation_data.action;action.name='walk_reference_v4';action.use_fake_user=True
scene.render.fps=30;scene.frame_start=1;scene.frame_end=34
# Deformation/weight checks run on the actual newly keyed rig.
max_weight_error=0;minimum_sole=100
for obj in meshes:
 for vertex in obj.data.vertices:
  total=sum(group.weight for group in vertex.groups);max_weight_error=max(max_weight_error,abs(1-total))
for frame in range(1,35,2):
 scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 for obj in meshes:
  if not obj.name.startswith('Rounded boot sole'):continue
  evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();minimum_sole=min(minimum_sole,min((evaluated.matrix_world@v.co).z for v in mesh.vertices));evaluated.to_mesh_clear()
assert max_weight_error<1e-5,max_weight_error
assert max(x['ankle_error'] for x in checks)<1e-5
assert minimum_sole>-.005,minimum_sole
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/worker-v4.blend'))
export(out/'worker-v4.glb',action,30,1,34)
meta={'source_video':'art/references/worker-motion-v4/reference.mp4','method':'manual reference reconstruction, not extraction of original 3D or exact mocap','reference_interval_seconds':[10,12.6],'cycle_seconds':gait.CYCLE,'speed_metres_per_second':gait.SPEED,'stride_metres':gait.STRIDE,'bones':len(rig.data.bones),'bone_names':list(rig.data.bones.keys()),'max_ankle_error':max(x['ankle_error'] for x in checks),'max_weight_error':max_weight_error,'minimum_boot_sole_z':minimum_sole,'mesh_geometry':'worker-v3 unchanged','clip':action.name}
(out/'motion.json').write_text(json.dumps(meta,indent=2));print('REFERENCE_GAIT_V4_OK '+json.dumps(meta))
