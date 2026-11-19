"""Publish a cache-isolated static preview using the existing guest motion API."""
from pathlib import Path
import subprocess,shutil,json,hashlib,urllib.request
root=Path(__file__).resolve().parents[1];source=root/'.online-client-v1';out=root/'.camera-preview';out.mkdir(exist_ok=True);slug='living-town-camera-v4';target='/var/www/michaelperov.com/preview/'+slug;url='https://michaelperov.com/preview/'+slug+'/'
public=['index.html','style.css','game.js','surfaces.js','construction.js','online-contract.js','online-network.js','hub-session.js','motion-timeline.js']+['assets/'+n for n in ['panel.png','worker.png','grass-v2.webp','asphalt-v2.webp','dirt-v2.webp','paving.png','birch.png','panel.json','worker.json']]
for name in public:
 p=out/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
p=out/'online-network.js';s=p.read_text();old="new URL('api/',location.href)";assert s.count(old)==1;p.write_text(s.replace(old,"new URL('/preview/living-town-smooth-v1/api/',location.href)"))
files={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in public};(out/'build.json').write_text(json.dumps({'type':slug,'files':files}));(out/'.files').write_text('\n'.join(public+['build.json'])+'\n')
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=120).stdout.strip()
run(['ssh','spb-node','test ! -e '+target+' || test -f '+target+'/build.json']);run(['ssh','spb-node','mkdir -p '+target]);run(['rsync','-rt','--chmod=D755,F644','--files-from='+str(out/'.files'),str(out)+'/', 'spb-node:'+target+'/'])
for name,value in files.items():
 r=urllib.request.urlopen(url+name+'?v='+value[:8],timeout=20)
 if name.endswith('.js'):assert 'javascript' in r.headers.get('Content-Type','')
 assert hashlib.sha256(r.read()).hexdigest()==value,name
print(json.dumps({'url':url,'public_hashes':len(files),'existing_preview_and_production_unchanged':True}))
