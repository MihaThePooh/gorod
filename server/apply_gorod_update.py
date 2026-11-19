"""Apply an approved motion update while retaining the current world and account setup."""
from pathlib import Path
import datetime,hashlib,json,shutil,sqlite3,subprocess,time,urllib.request
home=Path.home();runtime=home/'living-town-hub';stage=runtime/'candidate-motion';web=Path('/srv/living-town');unit=Path('/etc/systemd/system/living-town-hub.service')
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=40).stdout.strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((stage/'build.json').read_text());assert manifest['type']=='living-town-gorod-v1';assert 'motion-timeline.js' in manifest['public']
assert json.loads((web/'build.json').read_text())['type']=='living-town-gorod-v1'
old_unit=unit.read_text();assert '--origin https://gorod.michaelperov.com ' in old_unit
assert '--tick-seconds' not in old_unit and '--snapshot-seconds' not in old_unit,'motion update already installed; review before rerunning'
for name,value in manifest['files'].items():assert sha(stage/name)==value,name
backup=home/'backups/living-town-hub'/('motion-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));backup.mkdir(parents=True,mode=0o700)
for name,p in [('online.py',runtime/'online.py'),('service',unit)]:shutil.copyfile(p,backup/name);assert sha(p)==sha(backup/name)
shutil.copytree(web,backup/'web')
for p in web.rglob('*'):
 if p.is_file():assert sha(p)==sha(backup/'web'/p.relative_to(web))
with sqlite3.connect(runtime/'towns.sqlite') as src,sqlite3.connect(backup/'towns.sqlite') as dst:src.backup(dst);assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
(backup/'verified.json').write_text(json.dumps({'verified':True,'database_preserved':True}));print(json.dumps({'backup':str(backup),'verified':True}),flush=True)
import re
new_unit=re.sub(r'^(ExecStart=.*)$',r'\1 --tick-seconds 0.05 --snapshot-seconds 0.1',old_unit,flags=re.M);assert new_unit!=old_unit
(runtime/'motion-service.new').write_text(new_unit)
try:
 shutil.copyfile(stage/'online.py',runtime/'online.py')
 for name in manifest['public']+['build.json']:
  p=web/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(stage/name,p);p.chmod(0o644)
 run(['sudo','-n','install','-m','644',str(runtime/'motion-service.new'),str(unit)])
 run(['sudo','-n','systemctl','daemon-reload']);run(['sudo','-n','systemctl','restart','living-town-hub.service'])
 for i in range(50):
  try:assert json.load(urllib.request.urlopen('http://127.0.0.1:8799/health',timeout=2))['ok'];break
  except Exception:
   if i==49:raise
   time.sleep(.2)
except Exception:
 shutil.copyfile(backup/'online.py',runtime/'online.py');shutil.copytree(backup/'web',web,dirs_exist_ok=True)
 run(['sudo','-n','install','-m','644',str(backup/'service'),str(unit)]);run(['sudo','-n','systemctl','daemon-reload']);run(['sudo','-n','systemctl','restart','living-town-hub.service']);raise
print(json.dumps({'service':run(['systemctl','is-active','living-town-hub.service']),'backup':str(backup),'same_database':True}))
