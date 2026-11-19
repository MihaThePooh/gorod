"""Move the existing account world to its own HTTPS origin, preserving the database."""
from pathlib import Path
import datetime, hashlib, json, shutil, socket, sqlite3, subprocess, time, urllib.request
home=Path.home();hub=home/'hub';runtime=home/'living-town-hub';stage=runtime/'candidate-gorod';web=Path('/srv/living-town');domain='gorod.michaelperov.com'
def run(a,timeout=60):return subprocess.run(a,check=True,capture_output=True,text=True,cwd=hub,timeout=timeout).stdout.strip()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ips(name):return {i[4][0] for i in socket.getaddrinfo(name,80,family=socket.AF_INET)}
assert ips(domain)==ips('michaelperov.com'),'DNS must point to the current website server before deployment'
manifest=json.loads((stage/'build.json').read_text())
assert manifest['type']=='living-town-gorod-v1'
for name,value in manifest['files'].items():assert digest(stage/name)==value,name
backup=home/'backups/living-town-hub'/('gorod-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));backup.mkdir(parents=True,mode=0o700)
conf=Path('/etc/nginx/sites-available/michaelperov');site=Path('/etc/nginx/sites-available/living-town-gorod');enabled=Path('/etc/nginx/sites-enabled/living-town-gorod');unit=Path('/etc/systemd/system/living-town-hub.service');override=hub/'compose.override.yml'
for name,p in {'nginx-main':conf,'nginx-gorod':site,'service':unit,'override':override,'home.html':Path('/srv/hub-ui/home/index.html'),'home.csp':Path('/srv/hub-ui/home.csp.conf')}.items():
 if p.exists():shutil.copyfile(p,backup/name);assert digest(p)==digest(backup/name)
if (runtime/'towns.sqlite').exists():
 with sqlite3.connect(runtime/'towns.sqlite') as src,sqlite3.connect(backup/'towns.sqlite') as dst:src.backup(dst);assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
if web.exists():
 assert (web/'build.json').exists(),'unrecognized destination';shutil.copytree(web,backup/'web')
(backup/'verified.json').write_text(json.dumps({'verified':True,'database_preserved':True}))
print(json.dumps({'backup':str(backup),'verified':True}),flush=True)
run(['sudo','-n','install','-d','-o','mike','-g','mike','-m','755',str(web)])
for name in manifest['public']:
 p=web/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(stage/name,p);p.chmod(0o644)
shutil.copyfile(stage/'build.json',web/'build.json')
http=f'''server {{
 listen 80;
 server_name {domain};
 root {web};
 location ^~ /.well-known/acme-challenge/ {{ try_files $uri =404; }}
 location / {{ return 404; }}
}}
'''
(site_candidate:=runtime/'gorod-nginx.new').write_text(http)
run(['sudo','-n','install','-m','644',str(site_candidate),str(site)])
if not enabled.exists():run(['sudo','-n','ln','-s',str(site),str(enabled)])
run(['sudo','-n','nginx','-t']);run(['sudo','-n','systemctl','reload','nginx'])
# Certbot uses the existing ACME account. No private keys are read by this script.
run(['sudo','-n','certbot','certonly','--webroot','-w',str(web),'-d',domain,'--cert-name',domain,'--non-interactive','--agree-tos'],timeout=180)
policy="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' https://id.michaelperov.com; worker-src 'self'; manifest-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
https=f'''server {{
 listen 80;
 server_name {domain};
 root {web};
 location ^~ /.well-known/acme-challenge/ {{ try_files $uri =404; }}
 location / {{ return 301 https://{domain}$request_uri; }}
}}
server {{
 listen 443 ssl;
 server_name {domain};
 root {web};
 ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
 ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
 include /etc/letsencrypt/options-ssl-nginx.conf;
 ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
 location ^~ /api/ {{
  client_max_body_size 8k;
  proxy_pass http://127.0.0.1:8799/;
  proxy_http_version 1.1;
  proxy_set_header Connection "";
  proxy_set_header X-Real-IP $remote_addr;
  proxy_buffering off;
  proxy_cache off;
  proxy_read_timeout 60s;
  access_log off;
 }}
 location / {{
  types {{ text/html html; text/css css; application/javascript js; application/manifest+json webmanifest; application/json json; image/png png; image/webp webp; }}
  add_header Cache-Control "no-cache" always;
  add_header Content-Security-Policy "{policy}" always;
  add_header X-Content-Type-Options nosniff always;
  add_header Referrer-Policy no-referrer always;
  add_header X-Robots-Tag "noindex, nofollow" always;
  try_files $uri $uri/ =404;
  access_log off;
 }}
}}
'''
site_candidate.write_text(https)
old=conf.read_text();start=old.find('    # LivingTown account world.');end=old.find('    location / {',start)
assert start>=0 and end>start and 'location ^~ /town/api/' in old[start:end],'expected original game locations'
new=old[:start]+'''    # LivingTown moved to its own origin; keep old links usable.
    location = /town { return 301 https://gorod.michaelperov.com/; }
    location ^~ /town/ { rewrite ^/town/(.*)$ https://gorod.michaelperov.com/$1 permanent; }

'''+old[end:]
(runtime/'main-nginx.new').write_text(new)
service=unit.read_text();assert '--origin https://michaelperov.com --cookie-path /town/' in service
(runtime/'gorod-service.new').write_text(service.replace('--origin https://michaelperov.com --cookie-path /town/','--origin https://gorod.michaelperov.com --cookie-path /'))
try:
 shutil.copyfile(stage/'living-town-id.override.yml',override)
 run(['sudo','-n','docker','compose','up','-d','--no-deps','id-api'],timeout=90)
 for attempt in range(50):
  try:assert json.load(urllib.request.urlopen('http://127.0.0.1:8101/api/health',timeout=2))['ok'];break
  except Exception:
   if attempt==49:raise
   time.sleep(.2)
 run(['sudo','-n','install','-m','644',str(runtime/'gorod-service.new'),str(unit)])
 run(['sudo','-n','systemctl','daemon-reload']);run(['sudo','-n','systemctl','restart','living-town-hub.service'])
 run(['sudo','-n','install','-m','644',str(site_candidate),str(site)])
 run(['sudo','-n','install','-m','644',str(runtime/'main-nginx.new'),str(conf)])
 shutil.copyfile(stage/'hub-home.html',Path('/srv/hub-ui/home/index.html'));shutil.copyfile(stage/'home.csp.conf',Path('/srv/hub-ui/home.csp.conf'))
 run(['sudo','-n','nginx','-t']);run(['sudo','-n','systemctl','reload','nginx'])
except Exception:
 for name,p in [('nginx-main',conf),('service',unit)]:run(['sudo','-n','install','-m','644',str(backup/name),str(p)])
 for name,p in [('override',override),('home.html',Path('/srv/hub-ui/home/index.html')),('home.csp',Path('/srv/hub-ui/home.csp.conf'))]:shutil.copyfile(backup/name,p)
 run(['sudo','-n','docker','compose','up','-d','--no-deps','id-api'],timeout=90);run(['sudo','-n','systemctl','daemon-reload']);run(['sudo','-n','systemctl','restart','living-town-hub.service']);run(['sudo','-n','nginx','-t']);run(['sudo','-n','systemctl','reload','nginx']);raise
print(json.dumps({'origin':'https://'+domain,'same_database':True,'service':run(['systemctl','is-active','living-town-hub.service']),'guest':run(['systemctl','is-active','living-town-online-preview.service']),'backup':str(backup)}))
