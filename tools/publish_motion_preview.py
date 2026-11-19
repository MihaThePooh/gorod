"""Publish a separate guest regression stand, never replace the live account world."""
from pathlib import Path
import subprocess,json,hashlib,urllib.request
root=Path(__file__).resolve().parents[1];source=root/'.online-client-v1';slug='living-town-smooth-v1';runtime='/home/mike/'+slug;target='/var/www/michaelperov.com/preview/'+slug;url='https://michaelperov.com/preview/'+slug+'/'
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,timeout=150).stdout.strip()
names=['index.html','style.css','game.js','surfaces.js','construction.js','online-contract.js','online-network.js','hub-session.js','motion-timeline.js']+['assets/'+n for n in ['panel.png','worker.png','grass-v2.webp','asphalt-v2.webp','dirt-v2.webp','paving.png','birch.png','panel.json','worker.json']]
files={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in names};(source/'build.json').write_text(json.dumps({'type':slug,'files':files}));(source/'.smooth-files').write_text('\n'.join(names+['build.json'])+'\n')
ssh=['ssh','spb-node'];run(ssh+['mkdir -p '+runtime+' '+target]);run(['rsync','-rt','--chmod=D755,F644','--files-from='+str(source/'.smooth-files'),str(source)+'/', 'spb-node:'+target+'/']);run(['rsync','-rt',str(root/'server/online.py'),'spb-node:'+runtime+'/online.py'])
remote=root/'server/deploy_motion_preview.py';remote.write_text('''from pathlib import Path
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
''')
run(['rsync','-rt',str(remote),'spb-node:'+runtime+'/deploy.py']);print(run(ssh+['python3 '+runtime+'/deploy.py']))
for name,value in files.items():
 r=urllib.request.urlopen(url+name+'?v='+value[:8],timeout=20)
 if name.endswith('.js'):assert 'javascript' in r.headers.get('Content-Type','')
 assert hashlib.sha256(r.read()).hexdigest()==value,name
assert json.load(urllib.request.urlopen(url+'api/health',timeout=10))['ok'];print(json.dumps({'url':url,'public_hashes':len(files),'production_changed':False}))
