from pathlib import Path
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
