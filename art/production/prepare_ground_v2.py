"""Export web-ready terrain material candidates from the preserved masters."""
from pathlib import Path
from PIL import Image
import hashlib,json
root=Path(__file__).resolve().parents[2]
items={}
for name in ['grass','asphalt','dirt']:
 src=root/'art/textures/ground-v2'/(name+'-master.png')
 dst=root/'client/assets'/(name+'-v2.webp')
 with Image.open(src) as original:
  image=original.convert('RGB');image.thumbnail((1024,1024));image.save(dst,'WEBP',quality=90,method=6)
 items[name]={'master':str(src.relative_to(root)),'runtime':str(dst.relative_to(root)),'runtime_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size}
(root/'art/textures/ground-v2/exports.json').write_text(json.dumps(items,indent=2))
print(json.dumps(items))
