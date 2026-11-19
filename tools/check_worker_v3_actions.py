"""Validate the saved candidate's clip timing and deform modifier order."""
import bpy,json
for name,duration in {'worker_idle':2.5,'worker_walk':2.1,'worker_work':.5}.items():
 action=bpy.data.actions[name];seconds=(action.frame_range[1]-action.frame_range[0])/24
 assert abs(seconds-duration)<.001,(name,seconds)
for name in ('Jacket sleeve L','Jacket sleeve R','Trouser leg L','Trouser leg R'):
 obj=bpy.data.objects[name];assert [m.type for m in obj.modifiers]==['ARMATURE','CORRECTIVE_SMOOTH','SUBSURF']
 assert obj.modifiers[0].use_deform_preserve_volume
print(json.dumps({'savedClipDurations':True,'modifierOrder':True,'volumePreservation':True,'bones':len(bpy.data.objects['Worker rig'].data.bones)}))
