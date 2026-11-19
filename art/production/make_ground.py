"""Generate repeatable native ground textures from the approved road categories."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import random
r=Path(__file__).resolve().parents[2]/'client/assets'
for name,base in {'grass':(103,119,68),'asphalt':(75,79,77),'broken':(100,98,86),'dirt':(151,129,95),'paving':(155,151,130)}.items():
 rng=random.Random(name);im=Image.new('RGB',(128,128));pix=im.load()
 for y in range(128):
  for x in range(128):
   n=rng.randrange(-12,13);pix[x,y]=tuple(max(0,min(255,c+n)) for c in base)
 d=ImageDraw.Draw(im)
 if name=='grass':
  for _ in range(220):
   x,y=rng.randrange(128),rng.randrange(128);d.line((x,y,x+rng.randrange(-2,3),y-3),fill=(117,131,76),width=1)
 if name=='broken':
  for _ in range(4):
   x,y=rng.randrange(128),rng.randrange(128);pts=[(x,y)]
   for _ in range(7):x+=rng.randrange(-12,13);y+=rng.randrange(3,16);pts.append((x,y))
   d.line(pts,fill=(52,54,48),width=2)
  d.ellipse((40,55,85,80),fill=(62,67,64));d.arc((42,55,85,80),180,350,fill=(130,132,111),width=2)
 if name=='dirt':
  for _ in range(90):
   x,y=rng.randrange(128),rng.randrange(128);d.ellipse((x,y,x+2,y+1),fill=(126,113,86))
 if name=='paving':
  for y in range(0,129,32):
   d.line((0,y,128,y),fill=(117,117,101),width=2)
   for x in range(-16,129,32):d.line((x+(y//32%2)*16,y,x+(y//32%2)*16,y+32),fill=(117,117,101),width=1)
 im.save(r/(name+'.png'))
print('GROUND_TEXTURES_5_OK')
