"""Prepare fair-size before/after frames and a close model contact sheet."""
from pathlib import Path
from PIL import Image,ImageDraw
import math
r=Path(__file__).resolve().parents[1];out=Path('/workspace/worker-v3-review-frames');out.mkdir(exist_ok=True)
# Identical orthographic world scale for both render resolutions.
for i in range(72):
 t=i/24;c=Image.new('RGB',(960,560),'#dad8c9');d=ImageDraw.Draw(c);d.text((165,20),'PREVIOUS MODEL',fill='#293b30');d.text((640,20),'NEW MODEL',fill='#293b30')
 for x,version,h,frame in [(240,'worker-v2',288,int(t/1.05*24)%24),(720,'worker-v3',240,int(t/2.1*48)%48)]:
  p=r/f'art/renders/{version}/3-walk-{frame}.png'
  im=Image.open(p).convert('RGBA');scale=1.6*288/h;w=im.width;anchor=h/2+.95*math.cos(math.radians(42.72606346))*h/2.5
  im=im.resize((round(w*scale),round(h*scale)),Image.Resampling.LANCZOS);c.paste(im,(round(x-w/2*scale),round(430-anchor*scale)),im)
 c.save(out/f'{i:03}.jpg',quality=91)
board=Image.new('RGB',(384*3,576),'#dad8c9')
for i,d in enumerate((0,3,4)):
 im=Image.open(r/f'art/renders/worker-v3/portrait-{d}.png').convert('RGBA');board.paste(im,(i*384,0),im)
board.save(r/'art/renders/worker-v3/model-review.jpg',quality=94)
print('MODEL_AND_MOTION_REVIEW_PREPARED')
