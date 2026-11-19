"""Pack rendered animation frames and export the matching camera anchor."""
from pathlib import Path
from PIL import Image
import json,math,hashlib
root=Path(__file__).resolve().parents[2];r=root/'art/renders/worker-v1';m=json.loads((r/'frames.json').read_text());w,h=m['width'],m['height']
atlas=Image.new('RGBA',(w*11,h*8));bounds=[]
for item in m['frames']:
 im=Image.open(r/item['file']).convert('RGBA');b=im.getchannel('A').getbbox();assert b and b[0]>0 and b[1]>0 and b[2]<w and b[3]<h
 col={'idle':0,'walk':1,'work':7}[item['state']]+item['frame'];atlas.paste(im,(col*w,item['direction']*h));bounds.append(b)
assert len(m['frames'])==88
atlas.save(root/'client/assets/worker.png')
meta={'frameWidth':w,'frameHeight':h,'columns':11,'rows':8,'fps':12,'anchor':[w/2,h/2+.95*math.cos(math.radians(42.72606346))*h/2.5],'states':{'idle':{'start':0,'count':1},'walk':{'start':1,'count':6},'work':{'start':7,'count':4}},'worldHeight':1.90,'approvedConcept':'worker-v1.png','modelStatus':'first-playable-prototype'}
(root/'client/assets/worker.json').write_text(json.dumps(meta,indent=2));(r/'atlas.json').write_text(json.dumps(meta,indent=2))
preview=Image.new('RGB',(w*4,h*2),'#d6d5c6')
for d in range(8):
 im=Image.open(r/f'{d}-idle-0.png').convert('RGBA');preview.paste(im,(d%4*w,d//4*h),im)
preview.save(r/'directions.jpg',quality=93)
print('PACK_88_FRAMES_ALPHA_UNCLIPPED_PASS')
