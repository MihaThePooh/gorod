"""Publish our reconstructed model only, never the user's reference video."""
from pathlib import Path
import subprocess,json,hashlib,urllib.request
root=Path(__file__).resolve().parents[1];source=root/'client/worker-motion';slug='living-town-worker-motion-v1';target='/var/www/michaelperov.com/preview/'+slug;url='https://michaelperov.com/preview/'+slug+'/'
files={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file() and p.name!='build.json'}
assert not any(name.endswith(('.mp4','.jpg')) for name in files)
marker={'project':'living-town','type':'motion-reference-v4','files':files,'reference_video_published':False,'production_changed':False}
(source/'build.json').write_text(json.dumps(marker,indent=2));ssh=['ssh','-o','BatchMode=yes','spb-node']
def run(argv):return subprocess.run(argv,check=True,capture_output=True,text=True,timeout=180).stdout.strip()
probe=run(ssh+['test -d '+target+' && echo exists || echo absent'])
if probe=='absent':run(ssh+['mkdir '+target])
else:assert json.loads(run(ssh+['cat '+target+'/build.json']))==marker,'different preview already exists'
run(['rsync','-rt','--chmod=D755,F644',str(source)+'/','spb-node:'+target+'/'])
for name,sha in files.items():assert hashlib.sha256(urllib.request.urlopen(url+name,timeout=30).read()).hexdigest()==sha,name
print(json.dumps({'url':url,'hashes_verified':len(files),'reference_video_published':False,'production_changed':False}))
