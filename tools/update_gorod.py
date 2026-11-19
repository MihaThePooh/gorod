"""Publish the reviewed motion candidate; requires explicit approval of its preview."""
from pathlib import Path
import subprocess,hashlib,json,shutil,urllib.request,urllib.error
root=Path(__file__).resolve().parents[1];source=root/'.gorod-client-v1';stage=root/'.gorod-motion-release';stage.mkdir(exist_ok=True)
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=180).stdout.strip()
public=['index.html','style.css','game.js','surfaces.js','construction.js','online-contract.js','online-network.js','hub-session.js','motion-timeline.js','manifest.webmanifest','pwa.js','sw.js','offline.html','icons/icon-192.png','icons/icon-512.png']+['assets/'+n for n in ['panel.png','worker.png','grass-v2.webp','asphalt-v2.webp','dirt-v2.webp','paving.png','birch.png','panel.json','worker.json']]
for name in public:
 p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
for name,p in {'online.py':root/'server/online.py','apply.py':root/'server/apply_gorod_update.py'}.items():shutil.copyfile(p,stage/name)
files={n:hashlib.sha256((stage/n).read_bytes()).hexdigest() for n in public+['online.py','apply.py']}
(stage/'build.json').write_text(json.dumps({'type':'living-town-gorod-v1','files':files,'public':public},indent=2))
ssh=['ssh','spb-node'];target='/home/mike/living-town-hub/candidate-motion'
run(ssh+['mkdir -p '+target]);run(['rsync','-rt','--chmod=D755,F644',str(stage)+'/', 'spb-node:'+target+'/']);print(run(ssh+['python3 '+target+'/apply.py']))
url='https://gorod.michaelperov.com/'
for name in public:
 r=urllib.request.urlopen(url+name+'?v='+files[name][:8],timeout=20)
 if name.endswith('.js'):assert 'javascript' in r.headers.get('Content-Type','')
 assert hashlib.sha256(r.read()).hexdigest()==files[name],name
try:urllib.request.urlopen(url+'api/session',timeout=10);raise AssertionError('anonymous accepted')
except urllib.error.HTTPError as e:assert e.code==401
print(json.dumps({'url':url,'public_hashes':len(public),'anonymous_rejected':True}))
