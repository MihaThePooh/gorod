from pathlib import Path
import subprocess,datetime,shutil,json,sqlite3
home=Path.home();runtime=home/'living-town-smooth-v1';conf=Path('/etc/nginx/sites-available/michaelperov');unit=Path('/etc/systemd/system/living-town-motion-preview.service');backup=home/'backups/living-town-hub'/('motion-preview-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));backup.mkdir(parents=True)
old=conf.read_bytes();(backup/'nginx').write_bytes(old);assert (backup/'nginx').read_bytes()==old
if unit.exists():shutil.copyfile(unit,backup/'service')
if (runtime/'towns.sqlite').exists():
 with sqlite3.connect(runtime/'towns.sqlite') as src,sqlite3.connect(backup/'towns.sqlite') as dst:src.backup(dst);assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=30).stdout.strip()
(runtime/'service.new').write_text("""[Unit]
Description=LivingTown motion regression preview
After=network.target
[Service]
User=mike
WorkingDirectory=/home/mike/living-town-smooth-v1
ExecStart=/usr/bin/python3 /home/mike/living-town-smooth-v1/online.py --db /home/mike/living-town-smooth-v1/towns.sqlite --port 8800 --origin https://michaelperov.com --cookie-path /preview/living-town-smooth-v1/ --tick-seconds 0.05 --snapshot-seconds 0.1
Restart=on-failure
UMask=0077
NoNewPrivileges=yes
MemoryMax=256M
TasksMax=80
[Install]
WantedBy=multi-user.target
""")
run(['sudo','-n','install','-m','644',str(runtime/'service.new'),str(unit)]);run(['sudo','-n','systemctl','daemon-reload']);run(['sudo','-n','systemctl','enable','--now','living-town-motion-preview.service']);run(['sudo','-n','systemctl','restart','living-town-motion-preview.service'])
block="""    # Separate motion regression stand, no account data.
    location ^~ /preview/living-town-smooth-v1/api/ {
        proxy_pass http://127.0.0.1:8800/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 60s;
        access_log off;
    }

"""
if b'location ^~ /preview/living-town-smooth-v1/api/' not in old:
 assert old.count(b'    location / {')==1
 (runtime/'nginx.new').write_bytes(old.replace(b'    location / {',block.encode()+b'    location / {'))
 try:
  run(['sudo','-n','install','-m','644',str(runtime/'nginx.new'),str(conf)]);run(['sudo','-n','nginx','-t']);run(['sudo','-n','systemctl','reload','nginx'])
 except Exception:
  run(['sudo','-n','install','-m','644',str(backup/'nginx'),str(conf)]);run(['sudo','-n','nginx','-t']);run(['sudo','-n','systemctl','reload','nginx']);raise
print(json.dumps({'backup':str(backup),'service':run(['systemctl','is-active','living-town-motion-preview.service'])}))
