"""Pack two-stride clothing revision into a mobile-safe 30-column atlas."""
from pathlib import Path
from PIL import Image
import json,math
root=Path(__file__).resolve().parents[2];r=root/'art/renders/worker-v3';m=json.loads((r/'frames.json').read_text());w,h=m['width'],m['height']
states={'idle':{'start':0,'count':8,'fps':3.2},'walk':{'start':8,'count':48,'fps':48/m['cycle_seconds']},'work':{'start':56,'count':4,'fps':8}}
a=Image.new('RGBA',(w*30,h*16))
for f in m['frames']:
 im=Image.open(r/f['file']).convert('RGBA');b=im.getchannel('A').getbbox();assert b and b[0]>0 and b[1]>0 and b[2]<w and b[3]<h,(f,b)
 i=states[f['state']]['start']+f['frame'];a.paste(im,((i%30)*w,(f['direction']*2+i//30)*h))
assert len(m['frames'])==480
a.save(root/'client/assets/worker.png')
meta={'frameWidth':w,'frameHeight':h,'columns':30,'rows':16,'directionRows':2,'fps':24,'anchor':[w/2,h/2+.95*math.cos(math.radians(42.72606346))*h/2.5],'states':states,'worldHeight':1.90,'walkSpeed':m['walk_speed_m_s'],'strideMeters':m['stride_m'],'cycleSeconds':m['cycle_seconds'],'modelStatus':'smooth-clothing-gait-review'}
(root/'client/assets/worker.json').write_text(json.dumps(meta,indent=2));(r/'atlas.json').write_text(json.dumps(meta,indent=2));print('PACK_480_ALPHA_UNCLIPPED_PASS')
