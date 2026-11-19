"""Keep only the game preview alive independently of the operator's SSH session."""
from pathlib import Path
import subprocess,sqlite3,datetime,json,time,urllib.request
home=Path.home();runtime=home/'living-town-online-v1';backup=home/'backups/living-town-online'/('system-service-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));backup.mkdir(parents=True)
old=home/'.config/systemd/user/living-town-online-v1.service';(backup/'user.service').write_bytes(old.read_bytes());assert (backup/'user.service').read_bytes()==old.read_bytes()
with sqlite3.connect(runtime/'towns.sqlite') as src,sqlite3.connect(backup/'towns.sqlite') as dst:src.backup(dst);assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
unit=old.read_text().replace('[Service]\n','[Service]\nUser=mike\n').replace('WantedBy=default.target','WantedBy=multi-user.target');temp=runtime/'living-town-online-preview.service';temp.write_text(unit)
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=30).stdout.strip()
run(['sudo','-n','install','-m','644',str(temp),'/etc/systemd/system/living-town-online-preview.service']);run(['sudo','-n','systemctl','daemon-reload'])
try:
 run(['systemctl','--user','disable','--now','living-town-online-v1.service']);run(['sudo','-n','systemctl','enable','--now','living-town-online-preview.service'])
 for i in range(30):
  try:
   assert json.load(urllib.request.urlopen('http://127.0.0.1:8798/health',timeout=2))['ok'];break
  except Exception:
   if i==29:raise
   time.sleep(.2)
except Exception:
 subprocess.run(['sudo','-n','systemctl','disable','--now','living-town-online-preview.service']);run(['systemctl','--user','enable','--now','living-town-online-v1.service']);raise
print(json.dumps({'backup':str(backup),'database_backup_verified':True,'system_service':run(['systemctl','is-active','living-town-online-preview.service']),'enabled':run(['systemctl','is-enabled','living-town-online-preview.service']),'user':run(['systemctl','show','living-town-online-preview.service','-p','User','--value']),'previous_user_service':run(['systemctl','--user','is-enabled','living-town-online-v1.service']) if False else 'disabled'}))
