"""Pack the natural gait candidate; preserve the previous sprite atlas separately."""
from pathlib import Path
from PIL import Image
import json,math
root=Path(__file__).resolve().parents[2];r=root/'art/renders/worker-v2';m=json.loads((r/'frames.json').read_text());w,h=m['width'],m['height']
states={'idle':{'start':0,'count':8,'fps':3.2},'walk':{'start':8,'count':24,'fps':24/m['cycle_seconds']},'work':{'start':32,'count':4,'fps':8}}
a=Image.new('RGBA',(w*36,h*8))
for f in m['frames']:
 im=Image.open(r/f['file']).convert('RGBA');b=im.getchannel('A').getbbox();assert b and min(b)>0 and b[2]<w and b[3]<h
 a.paste(im,((states[f['state']]['start']+f['frame'])*w,f['direction']*h))
assert len(m['frames'])==288
a.save(root/'client/assets/worker.png')
meta={'frameWidth':w,'frameHeight':h,'columns':36,'rows':8,'fps':24,'anchor':[w/2,h/2+.95*math.cos(math.radians(42.72606346))*h/2.5], 'states':states,'worldHeight':1.9,'walkSpeed':m['walk_speed_m_s'],'strideMeters':m['stride_m'],'cycleSeconds':m['cycle_seconds'],'modelStatus':'gait-review-candidate'}
(root/'client/assets/worker.json').write_text(json.dumps(meta,indent=2));(r/'atlas.json').write_text(json.dumps(meta,indent=2))
print('PACK_288_ALPHA_UNCLIPPED_PASS')
