"""Apply a staged account build with verified backups, without touching the guest service."""
from pathlib import Path
import datetime, hashlib, json, shutil, sqlite3, subprocess, time, urllib.request
home=Path.home();runtime=home/'living-town-hub';candidate=runtime/'candidate';web=Path('/var/www/michaelperov.com/town');hub=home/'hub';conf=Path('/etc/nginx/sites-available/michaelperov');unit=Path('/etc/systemd/system/living-town-hub.service')
def run(args,timeout=60):return subprocess.run(args,check=True,capture_output=True,text=True,cwd=hub,timeout=timeout).stdout.strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def health(url):
 for i in range(50):
  try:
   assert json.load(urllib.request.urlopen(url,timeout=2))['ok'];return
  except Exception:
   if i==49:raise
   time.sleep(.2)
manifest=json.loads((candidate/'build.json').read_text())
assert manifest['type']=='living-town-hub-v1'
for name,value in manifest['files'].items():assert sha(candidate/name)==value,name
assert not web.exists() or (web/'build.json').exists(),'unrecognized existing web directory'
override=hub/'compose.override.yml'
assert not override.exists() or override.read_bytes()==(candidate/'living-town-id.override.yml').read_bytes(),'unrelated compose override'
backup=home/'backups/living-town-hub'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup.mkdir(parents=True,mode=0o700)
paths={'nginx.conf':conf,'hub-home.html':Path('/srv/hub-ui/home/index.html'),'home.csp.conf':Path('/srv/hub-ui/home.csp.conf'),'compose.override.yml':override,'service':unit,'online.py':runtime/'online.py','hub_auth.py':runtime/'hub_auth.py'}
saved={}
for label,p in paths.items():
 if p.exists():shutil.copyfile(p,backup/label);assert sha(p)==sha(backup/label);saved[label]=str(p)
if web.exists():shutil.copytree(web,backup/'web')
if (runtime/'towns.sqlite').exists():
 with sqlite3.connect(runtime/'towns.sqlite') as src,sqlite3.connect(backup/'towns.sqlite') as dst:src.backup(dst);assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
with (backup/'id.pgdump').open('wb') as f:
 subprocess.run(['sudo','-n','docker','compose','exec','-T','id-db','pg_dump','-Fc','-U','id','id'],cwd=hub,stdout=f,stderr=subprocess.PIPE,check=True,timeout=60)
with (backup/'id.pgdump').open('rb') as f:
 subprocess.run(['sudo','-n','docker','compose','exec','-T','id-db','pg_restore','--list'],cwd=hub,stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True,timeout=30)
(backup/'backup.json').write_text(json.dumps({'saved':saved,'id_dump_sha256':sha(backup/'id.pgdump'),'verified':True},indent=2))
print(json.dumps({'backup':str(backup),'verified':True}),flush=True)
# The guest build and its SQLite file are intentionally not among the targets.
for name in ['online.py','hub_auth.py']:shutil.copyfile(candidate/name,runtime/name)
web.mkdir(parents=True,exist_ok=True)
for name in manifest['public']:
 p=web/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate/name,p);p.chmod(0o644)
shutil.copyfile(candidate/'build.json',web/'build.json')
service='''[Unit]
Description=LivingTown hub-account world
After=network.target
[Service]
User=mike
WorkingDirectory=/home/mike/living-town-hub
ExecStart=/usr/bin/python3 /home/mike/living-town-hub/online.py --db /home/mike/living-town-hub/towns.sqlite --port 8799 --origin https://michaelperov.com --cookie-path /town/ --hub-keys-url http://127.0.0.1:8101/api/keys
Restart=on-failure
RestartSec=3
UMask=0077
NoNewPrivileges=yes
MemoryMax=256M
TasksMax=80
LimitNOFILE=256
[Install]
WantedBy=multi-user.target
'''
(runtime/'living-town-hub.service').write_text(service)
shutil.copyfile(candidate/'living-town-id.override.yml',override)
run(['sudo','-n','docker','compose','up','-d','--no-deps','id-api'],timeout=90)
health('http://127.0.0.1:8101/api/health')
run(['sudo','-n','install','-m','644',str(runtime/'living-town-hub.service'),str(unit)])
run(['sudo','-n','systemctl','daemon-reload']);run(['sudo','-n','systemctl','enable','--now','living-town-hub.service']);run(['sudo','-n','systemctl','restart','living-town-hub.service'])
health('http://127.0.0.1:8799/health')
old=conf.read_text()
block='''    # LivingTown account world. Guest preview remains on its own service/database.
    location = /town { return 302 /town/; }
    location ^~ /town/api/ {
        client_max_body_size 8k;
        proxy_pass http://127.0.0.1:8799/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 60s;
        access_log off;
    }
    location ^~ /town/ {
        types { text/html html; text/css css; application/javascript js; application/manifest+json webmanifest; application/json json; image/png png; image/webp webp; }
        add_header Cache-Control "no-cache" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' https://id.michaelperov.com; worker-src 'self'; manifest-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'" always;
        add_header X-Content-Type-Options nosniff always;
        add_header Referrer-Policy no-referrer always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        try_files $uri $uri/ =404;
        access_log off;
    }

'''
if 'location ^~ /town/' not in old:
 assert old.count('    location / {')==1
 (runtime/'nginx.new').write_text(old.replace('    location / {',block+'    location / {'))
 run(['sudo','-n','install','-m','644',str(runtime/'nginx.new'),str(conf)])
shutil.copyfile(candidate/'hub-home.html',Path('/srv/hub-ui/home/index.html'))
shutil.copyfile(candidate/'home.csp.conf',Path('/srv/hub-ui/home.csp.conf'))
try:
 run(['sudo','-n','nginx','-t']);run(['sudo','-n','systemctl','reload','nginx'])
except Exception:
 run(['sudo','-n','install','-m','644',str(backup/'nginx.conf'),str(conf)])
 shutil.copyfile(backup/'hub-home.html',Path('/srv/hub-ui/home/index.html'));shutil.copyfile(backup/'home.csp.conf',Path('/srv/hub-ui/home.csp.conf'))
 run(['sudo','-n','nginx','-t']);run(['sudo','-n','systemctl','reload','nginx']);raise
assert run(['systemctl','is-active','living-town-online-preview.service'])=='active'
assert run(['systemctl','is-active','living-town-hub.service'])=='active'
print(json.dumps({'backup':str(backup),'service':'active','guest_service':'active','new_accounts_world':True}),flush=True)
