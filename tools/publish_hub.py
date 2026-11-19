"""Stage only public assets and application code, then apply the authorized hub integration."""
from pathlib import Path
import hashlib,json,subprocess,urllib.request,urllib.error
root=Path(__file__).resolve().parents[1];hub=root.parents[1]/'tools/hub';source=root/'.hub-client-v1';stage=root/'.hub-release';stage.mkdir(exist_ok=True)
def run(a,timeout=60):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=timeout).stdout.strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
public=['index.html','style.css','game.js','surfaces.js','construction.js','online-contract.js','online-network.js','hub-session.js','motion-timeline.js','manifest.webmanifest','pwa.js','sw.js','offline.html','icons/icon-192.png','icons/icon-512.png']+['assets/'+n for n in ['panel.png','worker.png','grass-v2.webp','asphalt-v2.webp','dirt-v2.webp','paving.png','birch.png','panel.json','worker.json']]
files={n:sha(source/n) for n in public}
import shutil
for n in public:
 p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/n,p)
for name,p in {'online.py':root/'server/online.py','hub_auth.py':root/'server/hub_auth.py','deploy_hub.py':root/'server/deploy_hub.py','hub-home.html':root/'.hub-ui-build/home/index.html','home.csp.conf':root/'.hub-ui-build/home.csp.conf','living-town-id.override.yml':hub/'deploy/living-town-id.override.yml'}.items():
 shutil.copyfile(p,stage/name);files[name]=sha(stage/name)
(stage/'build.json').write_text(json.dumps({'type':'living-town-hub-v1','files':files,'public':public},indent=2))
ssh=['ssh','-o','BatchMode=yes','spb-node'];runtime='/home/mike/living-town-hub'
guest='https://michaelperov.com/preview/living-town-online-v1/'
guest_manifest=urllib.request.urlopen(guest+'build.json',timeout=15).read()
run(ssh+['mkdir -p '+runtime+'/candidate']);run(['rsync','-rt','--chmod=D755,F644',str(stage)+'/', 'spb-node:'+runtime+'/candidate/'])
result=run(ssh+['python3 '+runtime+'/candidate/deploy_hub.py'],timeout=180);print(result,flush=True)
url='https://michaelperov.com/town/'
for name in public:
 r=urllib.request.urlopen(url+name+'?check='+files[name][:8],timeout=20)
 if name.endswith('.js'):assert 'javascript' in r.headers.get('Content-Type',''),name
 assert hashlib.sha256(r.read()).hexdigest()==files[name],name
assert json.load(urllib.request.urlopen(url+'api/health',timeout=10))['ok']
try:urllib.request.urlopen(url+'api/session',timeout=10);raise AssertionError('anonymous session accepted')
except urllib.error.HTTPError as e:assert e.code==401
assert urllib.request.urlopen(guest+'build.json',timeout=15).read()==guest_manifest
assert hashlib.sha256(urllib.request.urlopen('https://hub.michaelperov.com/',timeout=15).read()).hexdigest()==files['hub-home.html']
(root/'art/renders/hub-deployment.json').write_text(json.dumps({'url':url,'public_hashes':len(public),'anonymous_rejected':True,'guest_unchanged':True,'result':result},indent=2))
print(json.dumps({'url':url,'public_hashes':len(public),'anonymous_rejected':True,'guest_unchanged':True}))
