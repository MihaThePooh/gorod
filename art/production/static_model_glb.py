"""Keep a neutral inspection GLB static; the editable blend retains skin weights."""
import json,struct
from pathlib import Path
def convert(path):
 p=Path(path);raw=p.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[20+size:]
 for mesh in doc['meshes']:
  for prim in mesh['primitives']:
   prim['attributes'].pop('JOINTS_0',None);prim['attributes'].pop('WEIGHTS_0',None)
 for node in doc['nodes']:node.pop('skin',None)
 doc.pop('skins',None);doc.pop('animations',None)
 doc['nodes'][0]['children']=[i for i,n in enumerate(doc['nodes']) if 'mesh' in n]
 s=json.dumps(doc,separators=(',',':')).encode();s+=b' '*((-len(s))%4);out=struct.pack('<III',0x46546c67,2,12+8+len(s)+len(binary))+struct.pack('<II',len(s),0x4e4f534a)+s+binary;p.write_bytes(out)
