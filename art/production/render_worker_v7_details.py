"""Inspect the requested anatomical details independently of the full silhouette."""
import bpy,os
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=bpy.context.scene;c=s.camera;s.render.resolution_x=500;s.render.resolution_y=500;s.cycles.samples=24;s.render.threads=2
for name,target,offset,size in [('head',(0,-.055,1.68),(1,-2,.35),.45),('shoulder',(.16,-.02,1.43),(1,-2,.35),.47),('seat',(0,.04,.93),(1,2,.2),.64)]:
 if name not in os.environ.get('WORKER_DETAIL_PARTS','head').split(','):continue
 t=Vector(target);c.location=t+Vector(offset);c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=size;s.render.filepath=str(R/'art/renders/worker-v7'/('detail-'+name+'.png'));bpy.ops.render.render(write_still=True)
