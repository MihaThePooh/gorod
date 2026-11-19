"""Render a small birch in the same orthographic pipeline as the buildings."""
import bpy,math,random
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];rng=random.Random(53)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
M={}
for n,c in {'bark':(.62,.59,.45),'dark':(.08,.09,.06),'leaf':(.15,.23,.045),'leafLight':(.27,.32,.065),'leafDeep':(.09,.15,.035)}.items():
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.95;M[n]=m

def rod(a,b,r,mat):
 vec=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=vec.length,location=(Vector(a)+Vector(b))/2);o=bpy.context.object;o.rotation_euler=vec.to_track_quat('Z','Y').to_euler();o.data.materials.append(M[mat])
rod((0,0,0),(.12,0,5.6),.095,'bark')
for z in (.7,1.3,2.1,2.7,3.2,4.1):
 rod((0,0,z),(0,0,z+.04),.099,'dark')
for i in range(14):
 angle=i*2.4;z=2.8+i*.19;length=1.7*(1-(z-2.8)/5);end=(math.cos(angle)*length,math.sin(angle)*length,z+.65)
 rod((.05,0,z),end,.035,'bark')
 for j in range(3):
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(end[0]+rng.uniform(-.5,.5),end[1]+rng.uniform(-.5,.5),end[2]+rng.uniform(-.2,.6)))
  o=bpy.context.object;o.scale=(rng.uniform(.6,1),rng.uniform(.65,1.0),rng.uniform(.45,.75));o.data.materials.append(M[['leaf','leafLight','leafDeep'][rng.randrange(3)]])
world=bpy.data.worlds.new('Day');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;bpy.context.scene.world=world
ld=bpy.data.lights.new('Sun','AREA');lo=bpy.data.objects.new('Sun',ld);bpy.context.collection.objects.link(lo);lo.location=(-8,-12,20);ld.energy=4500;ld.size=8;ld.color=(1,.9,.7);lo.rotation_euler=(Vector((0,0,3))-lo.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);bpy.context.collection.objects.link(cam);target=Vector((0,0,3));cam.location=target+Vector((32,-45,51));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=8.5
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=256;s.render.resolution_y=384;s.render.resolution_percentage=100;s.render.film_transparent=True;s.view_settings.exposure=.5;s.render.image_settings.color_mode='RGBA';s.render.filepath=str(R/'client/assets/birch.png')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/models/birch-v1.blend'));bpy.ops.render.render(write_still=True)
print('BIRCH_RENDER_OK')
