"""Validate the saved asset and export integration metadata without rendering."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[2]
CONFIG=json.loads(Path(__file__).with_name('panel-config.json').read_text())
scene=bpy.context.scene;cam=scene.camera
assert cam.data.type=='ORTHO'
assert abs(cam.data.ortho_scale-43)<.0001
expected=Vector(CONFIG['camera']['target'])+Vector(CONFIG['camera']['offset'])
assert (cam.location-expected).length<.0001
assert all(all(math.isfinite(v) for v in vertex.co) for obj in scene.objects if obj.type=='MESH' for vertex in obj.data.vertices)
frame=bpy.data.objects['frame']
coords=[v.co for v in frame.data.vertices]
assert min(v.x for v in coords)<-15.1 and max(v.x for v in coords)>15.1
assert min(v.y for v in coords)<-5.1 and max(v.y for v in coords)>5.1
assert not any(im.filepath and im.source=='FILE' and not im.packed_file for im in bpy.data.images)
bpy.context.view_layer.update()
def pixel(world):
 p=world_to_camera_view(scene,cam,Vector(world))
 return [round(p.x*scene.render.resolution_x,3),round((1-p.y)*scene.render.resolution_y,3)]
metadata={
 'asset_id':CONFIG['asset_id'],'status':'accepted-initial-asset',
 'floors':5,'entrances':2,'world_units':'metres',
 'footprint':[[-15,-5],[15,-5],[15,5],[-15,5]],
 'entry_points':[[-7.5,-6.65,0],[7.5,-6.65,0]],
 'anchor_world':[0,0,0],'anchor_pixel':pixel((0,0,0)),
 'footprint_pixel':[pixel((x,y,0)) for x,y in ((-15,-5),(15,-5),(15,5),(-15,5))],
 'camera':CONFIG['camera'],'seed':CONFIG['seed'],'render':CONFIG['render'],
 'material_count':len(bpy.data.materials),'object_count':len(scene.objects),
 'all_facades':True,'textures':'procedural packed in blend; no external images',
 'variants':'palette/seed/render in panel-config.json; dimensions fixed',
 'collision_note':'footprint is wall rectangle; balconies/canopies project outside it; entry_points are approach points'
}
(ROOT/'art/renders/panel-v3-metadata.json').write_text(json.dumps(metadata,indent=2))
print('SAVED_BLEND_CAMERA_GEOMETRY_DEPENDENCIES_PASS')
