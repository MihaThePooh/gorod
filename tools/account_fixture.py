"""Isolated browser fixture: synthetic email codes and ephemeral signing keys, never production."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from pathlib import Path
import json, jwt, mimetypes, subprocess, sys, threading, time, urllib.request, urllib.error, tempfile
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
root=Path(__file__).resolve().parents[1]
key=Ed25519PrivateKey.generate();jwk=json.loads(jwt.algorithms.OKPAlgorithm.to_jwk(key.public_key()));jwk['kid']='fixture'
sessions={}
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def reply(self,data,status=200,headers=None,kind='application/json'):
  raw=json.dumps(data).encode() if not isinstance(data,bytes) else data
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)))
  for k,v in (headers or {}).items():self.send_header(k,v)
  self.end_headers();self.wfile.write(raw)
 def auth(self):
  c=SimpleCookie(self.headers.get('Cookie',''));v=c.get('hub_access')
  try:return jwt.decode(v.value,key.public_key(),algorithms=['EdDSA'],issuer='hub-id') if v else None
  except jwt.InvalidTokenError:return None
 def do_GET(self):
  if self.path=='/api/keys':return self.reply({'keys':[jwk]})
  if self.path=='/api/me':
   claims=self.auth();return self.reply({'account':{'email':claims['sub']}} if claims else {},200 if claims else 401)
  if self.path.startswith('/town/api/'):return self.proxy()
  if self.path.split('?')[0] in ['/hub/','/']:
   page=Path('/workspace/town-hub-build/home/index.html').read_text().replace('https://id.michaelperov.com',origin).replace('https://michaelperov.com/town/',origin+'/town/').replace('content="michaelperov.com"','content="127.0.0.1"')
   # Keep the hub fixture from registering a root-scoped worker over the game fixture.
   page=page.replace("'serviceWorker' in navigator",'false')
   return self.reply(page.encode(),kind='text/html')
  if self.path.startswith('/town/'):
   name=self.path.split('?',1)[0][6:] or 'index.html';file=root/'.hub-client-v1'/name
   if not file.is_file():return self.reply({},404)
   raw=file.read_bytes()
   if name=='index.html':raw=raw.replace(b'https://id.michaelperov.com',origin.encode()).replace(b'https://hub.michaelperov.com',(origin+'/hub').encode())
   return self.reply(raw,kind=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  self.reply({},404)
 def proxy(self):
  req=urllib.request.Request(f'http://127.0.0.1:{backend_port}/'+self.path.split('/town/api/',1)[1],headers={k:v for k,v in self.headers.items() if k.lower() not in ['host','connection']},method=self.command)
  if self.command=='POST':req.data=self.rfile.read(int(self.headers.get('Content-Length',0)))
  try:r=urllib.request.urlopen(req,timeout=15)
  except urllib.error.HTTPError as e:r=e
  self.send_response(r.status)
  for k,v in r.headers.items():
   if k.lower() not in ['server','date','connection']:self.send_header(k,v)
  if self.path.startswith('/town/api/events'):
   self.close_connection=True;self.send_header('Connection','close');self.end_headers()
   try:
    while line:=r.readline():self.wfile.write(line);self.wfile.flush()
   except (BrokenPipeError,ConnectionResetError):pass
  else:self.end_headers();self.wfile.write(r.read())
 def do_POST(self):
  if self.path.startswith('/town/api/'):return self.proxy()
  b=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
  if self.path=='/api/auth/request':return self.reply({'ok':True})
  if self.path in ['/api/auth/verify','/api/auth/refresh']:
   c=SimpleCookie(self.headers.get('Cookie',''));sid=c.get('fixture_refresh');subject=b.get('email') if self.path.endswith('verify') and b.get('code')=='123456' else sessions.get(sid.value if sid else '')
   if not subject:return self.reply({},401)
   sessions[subject]=subject
   token=jwt.encode({'iss':'hub-id','sub':subject,'apps':['town'],'iat':int(time.time()),'exp':int(time.time())+int(b.get('ttl',3600))},key,algorithm='EdDSA',headers={'kid':'fixture'})
   raw=json.dumps({'account':{'email':subject}}).encode();self.send_response(200)
   for name,value in [('hub_access',token),('fixture_refresh',subject)]:self.send_header('Set-Cookie',f'{name}={value}; HttpOnly; SameSite=Lax; Path=/')
   self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
  self.reply({},404)
server=ThreadingHTTPServer(('127.0.0.1',0),H);server.daemon_threads=True;origin='http://127.0.0.1:'+str(server.server_port)
probe=ThreadingHTTPServer(('127.0.0.1',0),H);backend_port=probe.server_port;probe.server_close()
threading.Thread(target=server.serve_forever,daemon=True).start()
with tempfile.TemporaryDirectory() as tmp:
 child=subprocess.Popen([sys.executable,str(root/'server/online.py'),'--db',tmp+'/accounts.sqlite','--port',str(backend_port),'--origin',origin,'--hub-keys-url',origin+'/api/keys'])
 try:
  time.sleep(.4);print(origin,flush=True)
  while True:time.sleep(1)
 finally:child.terminate()
