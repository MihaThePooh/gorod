"""Check the exported clip, skin weights, loop and preserved mesh geometry."""
from pathlib import Path
import struct,json,hashlib
root=Path(__file__).resolve().parents[1]/'client/worker-motion'
def read(name):
 raw=(root/name).read_bytes();magic,version,size=struct.unpack_from('<III',raw);assert magic==0x46546c67 and version==2 and size==len(raw)
 n,t=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n]);bsize,btype=struct.unpack_from('<II',raw,20+n);blob=raw[28+n:];assert len(blob)==bsize
 def accessor(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);w={'SCALAR':1,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];fmt={5126:'f',5125:'I',5123:'H'}[a['componentType']];values=struct.unpack_from('<'+str(a['count']*w)+fmt,blob,offset);return [values[j:j+w] for j in range(0,len(values),w)]
 return doc,accessor
before,old=read('worker-before.glb');doc,get=read('worker-v4.glb');assert len(doc['skins'][0]['joints'])==22
for a,b in zip(before['meshes'],doc['meshes']):
 assert a['name']==b['name']
 for x,y in zip(a['primitives'],b['primitives']):assert old(x['attributes']['POSITION'])==get(y['attributes']['POSITION']),a['name']
maximum=0
for mesh in doc['meshes']:
 for primitive in mesh['primitives']:
  maximum=max(maximum,max(abs(sum(weights)-1) for weights in get(primitive['attributes']['WEIGHTS_0'])))
  assert max(max(j) for j in get(primitive['attributes']['JOINTS_0']))<22
assert maximum<1e-5
seam=0
for sampler in doc['animations'][0]['samplers']:
 values=get(sampler['output']);a,b=values[0],values[-1];delta=sum((x-y)**2 for x,y in zip(a,b))**.5
 if len(a)==4:delta=min(delta,sum((x+y)**2 for x,y in zip(a,b))**.5)
 seam=max(seam,delta)
assert seam<1e-5,seam
print(json.dumps({'glb':True,'bones':22,'mesh_geometry_unchanged':True,'weight_error':maximum,'loop_seam':seam,'sha256':hashlib.sha256((root/'worker-v4.glb').read_bytes()).hexdigest()}))
