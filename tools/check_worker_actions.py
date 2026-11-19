import bpy
expected={'worker_idle':60,'worker_walk':25.2,'worker_work':12}
for name,length in expected.items():
 action=bpy.data.actions[name];actual=action.frame_range[1]-action.frame_range[0]
 assert abs(actual-length)<.001,(name,actual,length)
 print(name,'seconds',round(actual/24,3))
print('BLEND_ACTION_TIMINGS_PASS')
