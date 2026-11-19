"""Export deterministic sprite sizes and verify alpha/pivots for the candidate."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib
root=Path(__file__).resolve().parents[2]
source=root/'art/renders/panel-v3.png'
im=Image.open(source).convert('RGBA')
a=im.getchannel('A');bounds=a.getbbox()
assert a.getextrema()==(0,255)
assert bounds and bounds[0]>2 and bounds[1]>2 and bounds[2]<im.width-2 and bounds[3]<im.height-2
meta=json.loads((root/'art/renders/panel-v3-metadata.json').read_text())
assert meta['camera']['offset']==[32,-45,51]
assert meta['camera']['ortho_scale']==43
meta['image_size']=list(im.size)
meta['alpha_bounds']=list(bounds)
meta['exports']={}
for width in (660,330):
 ratio=width/im.width;height=round(im.height*ratio)
 dest=root/'art/renders'/f'panel-v3-{width}.png'
 im.resize((width,height),Image.Resampling.LANCZOS).save(dest)
 meta['exports'][str(width)]={'file':dest.name,'size':[width,height],
 'anchor_pixel':[round(v*ratio,3) for v in meta['anchor_pixel']]}
meta['png_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
(root/'art/renders/panel-v3-metadata.json').write_text(json.dumps(meta,indent=2))
# A contact sheet makes the exact rendered sprite readable on a neutral backdrop.
canvas=Image.new('RGB',(1600,1080),'#dedfd2')
draw=ImageDraw.Draw(canvas)
big=im.copy();big.thumbnail((1120,1000),Image.Resampling.LANCZOS)
canvas.paste(big,(0,40),big)
small=Image.open(root/'art/renders/panel-v3-330.png').convert('RGBA')
canvas.paste(small,(1180,280),small)
draw.text((40,20),'PANEL v3 / orthographic 42.73 deg / review candidate',fill='#303b34')
draw.text((1180,240),'330 px export',fill='#303b34')
canvas.save(root/'art/renders/panel-v3-review.jpg',quality=94)
print(json.dumps({'alpha_bounds':bounds,'exports':list(meta['exports']),'camera_preserved':True}))
