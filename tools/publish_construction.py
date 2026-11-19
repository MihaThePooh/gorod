"""Publish only the isolated playable contract and its required assets."""
from pathlib import Path
import hashlib,json,subprocess,urllib.request
root=Path(__file__).resolve().parents[1];source=root/'client';stage=root/'.preview-contract-v1';stage.mkdir(exist_ok=True)
names=['index.html','style.css','game.js','contract-ui.js','construction.js','surfaces.js']
names+=['assets/'+n for n in ['panel.png','worker.png','grass-v2.webp','asphalt-v2.webp','dirt-v2.webp','paving.png','birch.png','panel.json','worker.json']]
import shutil
for name in names:
 p=stage/name;p.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(source/name,p)
files={n:hashlib.sha256((stage/n).read_bytes()).hexdigest() for n in names};marker={'project':'living-town','type':'construction-contract-v1','files':files,'real_accounts':False,'game_server':False,'production_changed':False}
(stage/'build.json').write_text(json.dumps(marker,indent=2));slug='living-town-contract-v1';target='/var/www/michaelperov.com/preview/'+slug;url='https://michaelperov.com/preview/'+slug+'/'
ssh=['ssh','-o','BatchMode=yes','spb-node']
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=180).stdout.strip()
probe=run(ssh+['test -e '+target+' && cat '+target+'/build.json || echo absent'])
if probe=='absent':run(ssh+['mkdir '+target])
else:
 previous=json.loads(probe);assert previous.get('type')==marker['type'] and previous.get('project')=='living-town' and previous.get('production_changed') is False
 for name,sha in previous['files'].items():assert hashlib.sha256(urllib.request.urlopen(url+name,timeout=30).read()).hexdigest()==sha,'preview baseline differs: '+name
(stage/'.deploy-files.txt').write_text('\n'.join(names+['build.json'])+'\n')
run(['rsync','-rt','--files-from='+str(stage/'.deploy-files.txt'),'--chmod=D755,F644',str(stage)+'/','spb-node:'+target+'/'])
for name,sha in files.items():
 response=urllib.request.urlopen(url+name+'?check='+sha[:8],timeout=30)
 if name.endswith('.js'):assert 'javascript' in response.headers.get('Content-Type',''),'Wrong module MIME: '+name
 assert hashlib.sha256(response.read()).hexdigest()==sha,name
record={'url':url,'verified_files':len(files),'game_server':False,'real_accounts':False,'production_changed':False};(root/'art/renders/construction-deploy.json').write_text(json.dumps(record));print(json.dumps(record))
