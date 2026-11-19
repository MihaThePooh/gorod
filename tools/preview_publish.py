"""Publish only this project's isolated, new static preview on the existing host."""
from pathlib import Path
import hashlib,json,subprocess,urllib.request,sys
source=Path(sys.argv[1]).resolve();slug='living-town-v1';target='/var/www/michaelperov.com/preview/'+slug;url='https://michaelperov.com/preview/'+slug+'/'
assert source.name=='client' and source.parent.name=='living-town'
files={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file() and p.name!='build.json'}
assert 'index.html' in files and 'assets/worker.png' in files
marker={'project':'living-town','version':1,'files':files,'real_accounts':False,'game_server':False}
(source/'build.json').write_text(json.dumps(marker,indent=2))
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','-o','StrictHostKeyChecking=yes','spb-node']
def run(a):
 r=subprocess.run(a,text=True,capture_output=True,timeout=120)
 if r.returncode:raise RuntimeError(r.stderr[-1000:])
 return r.stdout.strip()
probe=run(ssh+[f'if test -e {target}; then cat {target}/build.json; else printf absent; fi'])
if probe=='absent':
 run(ssh+[f'mkdir {target}']);run(['rsync','-rt','--chmod=D755,F644',str(source)+'/',f'spb-node:{target}/'])
else:
 assert json.loads(probe)==marker,'Existing different preview; refusing overwrite without backup'
for name,sha in files.items():
 data=urllib.request.urlopen(url+name,timeout=25).read();assert hashlib.sha256(data).hexdigest()==sha,name
print(json.dumps({'url':url,'verified_files':len(files),'production_changed':False}))
