"""Deploy a separate loopback preview service and route, preserving the existing nginx site."""
from pathlib import Path
import subprocess,json,hashlib,urllib.request,datetime,shlex
root=Path(__file__).resolve().parents[1];source=root/'.online-client-v1';slug='living-town-online-v1';target='/var/www/michaelperov.com/preview/'+slug;runtime='/home/mike/'+slug;url='https://michaelperov.com/preview/'+slug+'/'
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=180).stdout.strip()
ssh=['ssh','-o','BatchMode=yes','spb-node'];names=['index.html','style.css','game.js','surfaces.js','construction.js','online-contract.js','online-network.js','hub-session.js','motion-timeline.js']+['assets/'+n for n in ['panel.png','worker.png','grass-v2.webp','asphalt-v2.webp','dirt-v2.webp','paving.png','birch.png','panel.json','worker.json']]
files={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in names};marker={'project':'living-town','type':slug,'files':files,'real_accounts':False,'shared_server':True};(source/'build.json').write_text(json.dumps(marker,indent=2));(source/'.files').write_text('\n'.join(names+['build.json'])+'\n')
probe=run(ssh+['test -e '+target+' && cat '+target+'/build.json || echo absent'])
if probe!='absent':
 old=json.loads(probe);assert old.get('type')==slug
 for n,h in old['files'].items():assert hashlib.sha256(urllib.request.urlopen(url+n,timeout=30).read()).hexdigest()==h,'preview differs: '+n
run(ssh+['mkdir -p '+target+' '+runtime]);run(['rsync','-rt','--chmod=D755,F644','--files-from='+str(source/'.files'),str(source)+'/', 'spb-node:'+target+'/']);run(['rsync','-rt',str(root/'server/online.py'),'spb-node:'+runtime+'/online.py'])
assert run(ssh+['sha256sum '+runtime+'/online.py']).split()[0]==hashlib.sha256((root/'server/online.py').read_bytes()).hexdigest(),'backend hash differs'
remote=root/'server/deploy_preview.py'
remote.write_text('''from pathlib import Path
import subprocess,datetime,hashlib,json,urllib.request,sqlite3
home=Path.home();runtime=home/'living-town-online-v1';unit=Path('/etc/systemd/system/living-town-online-preview.service');candidate=runtime/'living-town-online-preview.service';backup=home/'backups/living-town-online'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup.mkdir(parents=True)
conf=Path('/etc/nginx/sites-available/michaelperov');old=conf.read_bytes();(backup/'nginx.conf').write_bytes(old);assert (backup/'nginx.conf').read_bytes()==old
if unit.exists():(backup/'service').write_bytes(unit.read_bytes())
db=runtime/'towns.sqlite'
if db.exists():
 with sqlite3.connect(db) as src,sqlite3.connect(backup/'towns.sqlite') as dst:src.backup(dst);assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
candidate.write_text("""[Unit]
Description=LivingTown isolated two-player preview
After=network.target
[Service]
User=mike
Type=simple
WorkingDirectory="""+str(runtime)+"""
ExecStart=/usr/bin/python3 """+str(runtime)+"""/online.py --db """+str(db)+""" --port 8798 --origin https://michaelperov.com --cookie-path /preview/living-town-online-v1/
Restart=on-failure
RestartSec=3
UMask=0077
NoNewPrivileges=yes
MemoryMax=256M
TasksMax=80
LimitNOFILE=256
[Install]
WantedBy=multi-user.target
""")
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=30).stdout.strip()
run(['sudo','-n','install','-m','644',str(candidate),str(unit)]);run(['sudo','-n','systemctl','daemon-reload']);run(['sudo','-n','systemctl','enable','--now','living-town-online-preview.service']);run(['sudo','-n','systemctl','restart','living-town-online-preview.service'])
import time
for i in range(30):
 try:
  assert json.load(urllib.request.urlopen('http://127.0.0.1:8798/health',timeout=2))['ok'];break
 except Exception:
  if i==29:raise
  time.sleep(.2)
block="""    # LivingTown: isolated two-player preview, not the hub API.
    location ^~ /preview/living-town-online-v1/api/ {
        client_max_body_size 8k;
        proxy_pass http://127.0.0.1:8798/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
        proxy_cache off;
        proxy_connect_timeout 3s;
        proxy_read_timeout 60s;
        access_log off;
    }
    location /preview/living-town-online-v1/ {
        try_files $uri $uri/ =404;
        access_log off;
    }

"""
if b'location ^~ /preview/living-town-online-v1/api/' not in old:
 assert old.count(b'    location / {')==1
 new=old.replace(b'    location / {',block.encode()+b'    location / {');tmp=runtime/'nginx.new';tmp.write_bytes(new)
 try:
  assert conf.read_bytes()==old
  run(['sudo','-n','install','-m','644',str(tmp),str(conf)]);run(['sudo','-n','nginx','-t']);run(['sudo','-n','systemctl','reload','nginx'])
 except Exception:
  run(['sudo','-n','install','-m','644',str(backup/'nginx.conf'),str(conf)]);run(['sudo','-n','nginx','-t']);run(['sudo','-n','systemctl','reload','nginx']);raise
print(json.dumps({'backup':str(backup),'backup_verified':True,'service':run(['systemctl','is-active','living-town-online-preview.service']),'loopback_health':True,'existing_apps_changed':False}))
''')
run(['rsync','-rt',str(remote),'spb-node:'+runtime+'/deploy_preview.py']);result=json.loads(run(ssh+['python3 '+runtime+'/deploy_preview.py']))
for n,h in files.items():
 r=urllib.request.urlopen(url+n+'?check='+h[:8],timeout=30)
 if n.endswith('.js'):assert 'javascript' in r.headers.get('Content-Type','')
 assert hashlib.sha256(r.read()).hexdigest()==h,n
assert json.load(urllib.request.urlopen(url+'api/health',timeout=10))['ok'];result.update(url=url,public_hashes=len(files),public_health=True);(root/'art/renders/online-deployment.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
