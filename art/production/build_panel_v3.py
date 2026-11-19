"""Build a deterministic modular five-storey apartment and render a sprite."""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
CONFIG=json.loads(Path(__file__).with_name('panel-config.json').read_text())
rng=random.Random(CONFIG['seed'])
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
materials={}; batches={}
def material(name,color,rough=.8,noise=False,metal=0):
 color=tuple(CONFIG['palette'].get(name,color))
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 p.inputs['Specular IOR Level'].default_value=.18
 if noise:
  n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=9;n.inputs['Detail'].default_value=2
  ramp=m.node_tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(*(c*.70 for c in color),1);ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(*color,1)
  bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.025
  m.node_tree.links.new(n.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
  m.node_tree.links.new(n.outputs['Fac'],ramp.inputs['Fac']);m.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
 materials[name]=m;batches[name]=([],[])
for name,col in [('joint',(.27,.29,.28)),('panel',(.65,.65,.57)),('panel_light',(.72,.71,.62)),('panel_cool',(.60,.63,.60)),('plinth',(.35,.32,.28)),('roof',(.23,.25,.24)),('frame',(.78,.78,.68)),('reveal',(.20,.24,.23)),('glass',(.16,.25,.28)),('glass_light',(.29,.38,.39)),('door',(.23,.30,.27)),('rail',(.32,.38,.35)),('balcony',(.54,.60,.55)),('rust',(.40,.25,.17)),('concrete',(.57,.56,.49)),('white',(.84,.81,.68))]:material(name,col,noise=name in ('panel','panel_light','panel_cool','roof','plinth','concrete'))
def box(mat,c,s):
 vs,fs=batches[mat];i=len(vs);x,y,z=c;a,b,d=(v/2 for v in s)
 vs.extend([(x-a,y-b,z-d),(x+a,y-b,z-d),(x+a,y+b,z-d),(x-a,y+b,z-d),(x-a,y-b,z+d),(x+a,y-b,z+d),(x+a,y+b,z+d),(x-a,y+b,z+d)])
 fs.extend([tuple(i+j for j in face) for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
W,D,H=30,10,15.4
box('joint',(0,0,H/2+.6),(W,D,H))
box('plinth',(0,0,.45),(W+.08,D+.08,.9))
# Panels are separate shallow blocks on a regular architectural grid.
for f in range(5):
 z=.85+f*2.95+1.45
 for bay in range(10):
  x=-13.5+bay*3
  for side in (-1,1):box(rng.choice(['panel','panel','panel_light','panel_cool']),(x,side*5.015,z),(2.97,.12,2.91))
 for side in (-1,1):
  for bay in range(4):box('panel',(side*15.015,-3.75+bay*2.5,z),(.12,2.47,2.91))
def window(x,y,z,w=1.6,h=1.55):
 box('reveal',(x,y,z),(w+.19,.08,h+.18));box('glass_light' if rng.random()<.25 else 'glass',(x,y-.055,z),(w,.04,h))
 for dx in (-w/2,w/2):box('frame',(x+dx,y-.09,z),(.075,.09,h+.1))
 for dz in (-h/2,h/2):box('frame',(x,y-.09,z+dz),(w+.08,.09,.075))
 box('frame',(x+w*.12,y-.10,z),(.06,.10,h));box('frame',(x,y-.10,z+h*.17),(w,.10,.05))
 box('concrete',(x,y-.16,z-h/2-.04),(w+.25,.28,.09))
for f in range(5):
 z=2.23+f*2.95
 for bay in range(10):
  x=-13.5+bay*3
  if bay in (2,7):
   if f==0:continue
   window(x,-5.12,z,1.05,1.6)
  else:window(x,-5.12,z)
# Rear facade has its own complete window grid, without copied balconies.
for f in range(5):
 for bay in range(10):
  before={name:len(data[0]) for name,data in batches.items()}
  window(-13.5+bay*3,-5.12,2.23+f*2.95,1.3 if bay in (2,7) else 1.6)
  for name,(verts,faces) in batches.items():
   start=before[name]
   for j in range(start,len(verts)):
    x,y,z=verts[j];verts[j]=(x,-y,z)
   for j,face in enumerate(faces):
    if face[0]>=start:faces[j]=tuple(reversed(face))
# Side facade, sparse windows, no copied front balconies.
for f in range(5):
 for y in (-2.4,2.4):
  z=2.23+f*2.95
  box('reveal',(15.12,y,z),(.08,1.65,1.75));box('glass',(15.18,y,z),(.05,1.49,1.59))
  for dy in (-.78,0,.78):box('frame',(15.23,y+dy,z),(.08,.065,1.7))
  for dz in (-.82,.82):box('frame',(15.23,y,z+dz),(.08,1.62,.07))
# Copy only the right-end window geometry to the opposite end.
for name,(verts,faces) in batches.items():
 copied={}
 for j,(x,y,z) in enumerate(list(verts)):
  if x>15.07 and name in ('reveal','glass','frame'):
   copied[j]=len(verts);verts.append((-x,y,z))
 for face in list(faces):
  if all(j in copied for j in face):faces.append(tuple(copied[j] for j in reversed(face)))
for bay in (0,3,6,9):
 x=-13.5+bay*3
 for f in range(1,5):
  base=.85+f*2.95
  box('concrete',(x,-5.78,base+.05),(2.38,1.52,.16))
  box('balcony',(x,-6.48,base+.62),(2.3,.10,1.05))
  for dx in (-1.12,1.12):box('balcony',(x+dx,-5.80,base+.62),(.10,1.4,1.05))
  box('rail',(x,-6.52,base+1.18),(2.4,.10,.09))
  if (bay+f)%3!=0:
   box('glass_light',(x,-6.5,base+1.92),(2.20,.055,1.42))
   for dx in (-1.12,-.38,.38,1.12):box('frame',(x+dx,-6.55,base+1.94),(.055,.08,1.53))
   for dz in (1.18,2.69):box('frame',(x,-6.55,base+dz),(2.32,.08,.07))
   for dx in (-1.12,1.12):
    box('glass',(x+dx,-5.8,base+1.94),(.055,1.35,1.42))
    box('frame',(x+dx,-5.8,base+2.69),(.07,1.45,.07))
   box('roof',(x,-5.8,base+2.78),(2.47,1.58,.12))
# Two entrances, landings, steps and flat canopies.
for x in (-7.5,7.5):
 box('reveal',(x,-5.13,1.55),(1.65,.12,2.3));box('door',(x,-5.22,1.5),(1.43,.09,2.16))
 box('frame',(x,-5.29,1.5),(.04,.06,2.1));box('glass',(x,-5.29,2.05),(1.10,.05,.55))
 box('white',(x+.44,-5.35,1.35),(.05,.08,.23))
 for i in range(3):box('concrete',(x,-5.55-i*.32,.55-i*.16),(2.25,.85,.32))
 box('concrete',(x,-5.75,2.95),(2.65,1.55,.17))
# Roof parapets and ventilation volumes.
roofz=H+.65
box('roof',(0,0,roofz),(W,D,.18))
for y in (-4.94,4.94):box('concrete',(0,y,roofz+.25),(W,.15,.45))
for x in (-14.94,14.94):box('concrete',(x,0,roofz+.25),(.15,D,.45))
for x in (-11,-4,4,11):
 box('concrete',(x,.5,roofz+.55),(1.1,1.35,.9));box('roof',(x,.5,roofz+1.04),(1.3,1.55,.12))
# Recessed panel details, service fittings and restrained roof weathering.
material('roof_seam',(.055,.06,.05))
material('curtain',(.38,.30,.18))
material('repair',(.29,.28,.22),noise=True)
material('drain',(.12,.15,.13),metal=.25)
for x in (-12,-6,0,6,12):
 box('roof_seam',(x,0,roofz+.098),(.025,9.7,.012))
for y in (-3.3,-1.65,0,1.65,3.3):
 box('roof_seam',(0,y,roofz+.098),(29.7,.025,.012))
for i in range(35):
 x=rng.uniform(-14.5,14.5);y=rng.uniform(-4.5,4.5)
 box('roof_seam',(x,y,roofz+.10),(rng.uniform(.10,.65),rng.uniform(.05,.25),.012))
for x in (-14.65,14.65):
 for y in (-5.20,5.20):
  box('drain',(x,y,8),(.12,.14,15.2))
  for z in (2,5,8,11,14):box('rail',(x,y,z),(.23,.23,.07))
# Modest plinth vents, entry lights, handrails and number plates.
for bay in range(10):
 x=-13.5+bay*3
 if bay not in (2,7):
  box('reveal',(x,-5.085,.42),(.7,.05,.28))
  for dx in (-.25,-.125,0,.125,.25):box('rail',(x+dx,-5.12,.42),(.026,.035,.24))
for i,x in enumerate((-7.5,7.5)):
 box('door',(x+.99,-5.20,2.15),(.38,.06,.20))
 box('white',(x+.99,-5.24,2.15),(.035,.025,.12))
 box('rail',(x,-5.25,2.76),(.35,.18,.13))
 for side in (-1,1):
  box('rail',(x+side*1.03,-5.86,.97),(.045,1.18,.045))
  for y in (-5.4,-6.3):box('rail',(x+side*1.03,y,.62),(.045,.045,.72))
# Ground-floor security bars and a few distinguishable curtains.
for bay in (1,4,5,8):
 x=-13.5+bay*3
 for dx in (-.55,0,.55):box('rail',(x+dx,-5.26,2.23),(.035,.05,1.50))
for f,bay in ((1,1),(2,4),(3,8),(4,5)):
 x=-13.5+bay*3;z=2.23+f*2.95
 box('curtain',(x-.5,-5.185,z),(.35,.015,1.35))
# Small repairs occur in a deliberate grid, never deform the architecture.
for f,bay in ((0,1),(1,5),(3,8)):
 box('repair',(-13.5+bay*3+.95,-5.081,1.0+f*2.95),(.28,.01,.16))
for name,(verts,faces) in batches.items():
 if not verts:continue
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(materials[name])
 bevel=obj.modifiers.new('Small manufactured edges','BEVEL');bevel.width=.025;bevel.segments=1
 obj.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
# Neutral lighting, a fixed overhead camera and a transparent output.
world=bpy.data.worlds.new('Soft sky');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.77,.87,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
ld=bpy.data.lights.new('Afternoon sun','AREA');lo=bpy.data.objects.new('Afternoon sun',ld);bpy.context.collection.objects.link(lo);lo.location=(-18,-25,45);ld.energy=16000;ld.color=(1.0,.85,.64);ld.shape='DISK';ld.size=12
lo.rotation_euler=(Vector((0,0,6))-lo.location).to_track_quat('-Z','Y').to_euler()
camd=bpy.data.cameras.new('Game camera');cam=bpy.data.objects.new('Game camera',camd);bpy.context.collection.objects.link(cam)
target=Vector(CONFIG['camera']['target']);cam.location=target+Vector(CONFIG['camera']['offset']);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=CONFIG['camera']['ortho_scale']
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=CONFIG['render']['samples'];scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=CONFIG['render']['threads']
scene.render.resolution_x=CONFIG['render']['width'];scene.render.resolution_y=CONFIG['render']['height'];scene.render.resolution_percentage=100;scene.render.film_transparent=True
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.55;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.filepath=str(ROOT/'art/renders/panel-v3.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/models/panel-v3.blend'))
bpy.ops.render.render(write_still=True)

from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update()
def pixel(world):
 p=world_to_camera_view(scene,cam,Vector(world))
 return [round(p.x*scene.render.resolution_x,3),round((1-p.y)*scene.render.resolution_y,3)]
metadata={
 'asset_id':CONFIG['asset_id'],'status':'accepted-initial-asset',
 'floors':5,'entrances':2,'world_units':'metres','footprint':[[-15,-5],[15,-5],[15,5],[-15,5]],
 'entry_points':[[-7.5,-6.65,0],[7.5,-6.65,0]],
 'anchor_world':[0,0,0],'anchor_pixel':pixel((0,0,0)),
 'footprint_pixel':[pixel((x,y,0)) for x,y in ((-15,-5),(15,-5),(15,5),(-15,5))],
 'camera':CONFIG['camera'],'seed':CONFIG['seed'],'render':CONFIG['render'],
 'material_count':len(materials),'object_count':len(scene.objects),
 'all_facades':True,'textures':'procedural packed in blend; no external images',
 'variants':'palette/seed/render in panel-config.json; dimensions are fixed in this prototype'
}
(ROOT/'art/renders/panel-v3-metadata.json').write_text(json.dumps(metadata,indent=2))
print('PANEL_V3_BUILD_RENDER_OK')
