"""Two-player preview: authoritative transactions, bounded movement and durable towns."""
from contextlib import contextmanager
from collections import deque
import argparse,hashlib,json,math,os,sqlite3,threading,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlsplit,parse_qs
from pathlib import Path
PLACES={'board':(8,-19),'supplier':(20,-22),'site':(18,-14)}
def blocked(x,y):return not(-62<=x<=62 and -62<=y<=62) or any(abs(x-a)<15.45 and abs(y-b)<5.45 for a,b in [(0,0),(-38,27),(34,32)])
def token():return os.urandom(24).hex()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def initial():return {'version':1,'revision':0,'phase':'available','progress':0,'effort':0.,'money':{'treasury':1000,'supplier':400,'escrow':0},'stone':{'supplier':80,'site':0,'road':0},'players':{},'journal':[]}
class Store:
 def __init__(self,path,max_players=2,render_delay=.7):
  self.motion_clock=time.monotonic();self.render_delay=render_delay;self.max_players=max_players;self.boot=str(time.time_ns());self.path=str(path);self.lock=threading.RLock();self.live={};self.streams={};self.rates={};self.position_saved={}
  self.connection=sqlite3.connect(self.path,timeout=10,check_same_thread=False)
  with self.db() as d:d.executescript('PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS towns(id TEXT PRIMARY KEY,state TEXT NOT NULL); CREATE TABLE IF NOT EXISTS receipts(town TEXT,player TEXT,id TEXT,PRIMARY KEY(town,player,id));')
 @contextmanager
 def db(self):
  # Keep WAL open: closing the final connection checkpoints on every frame.
  with self.lock:
   with self.connection:yield self.connection
 def close(self):
  with self.lock:self.connection.close()
 def load(self,d,town):
  row=d.execute('SELECT state FROM towns WHERE id=?',(town,)).fetchone()
  if not row:raise ValueError('Посёлок не найден. Создай новый или проверь ссылку.')
  return json.loads(row[0])
 def save(self,d,town,s):
  assert sum(s['money'].values())+sum(p['balance'] for p in s['players'].values())==1400+180*len(s['players'])
  assert sum(s['stone'].values())+sum(p['stone'] for p in s['players'].values())==80
  assert all(v>=0 for v in s['money'].values()) and all(p['balance']>=0 for p in s['players'].values())
  d.execute('UPDATE towns SET state=? WHERE id=?',(json.dumps(s),town))
 def join(self,town,cookie,ip='local'):
  raw=cookie or token();pid=digest(raw)
  if town is not None and (not isinstance(town,str) or len(town)!=48 or any(c not in '0123456789abcdef' for c in town)):raise ValueError('Некорректная ссылка посёлка.')
  with self.lock,self.db() as d:
   if not town:
    now=time.monotonic();history=[t for t in self.rates.get(ip,[]) if now-t<3600]
    if len(history)>=20 or d.execute('SELECT COUNT(*) FROM towns').fetchone()[0]>=200:raise ValueError('Лимит новых посёлков на стенде. Попробуй позже.')
    self.rates[ip]=history+[now];town=token();s=initial();d.execute('INSERT INTO towns VALUES(?,?)',(town,json.dumps(s)))
   else:s=self.load(d,town)
   if pid not in s['players']:
    if len(s['players'])>=self.max_players:raise ValueError('В посёлке пока нет свободных мест.')
    n=len(s['players'])+1;s['players'][pid]={'name':'Строитель '+str(n),'balance':180,'stone':0,'spent':0,'work':0.,'x':11+n,'y':-16,'direction':0};s['revision']+=1;self.save(d,town,s)
   self.touch(town,pid,s['players'][pid]);return town,raw,self.view(town,s,pid)
 def join_account(self,subject):
  # A stable world and subject-derived identity survive new devices and restarts.
  town=digest('living-town-account-world-v1')[:48]
  with self.lock,self.db() as d:
   d.execute('INSERT OR IGNORE INTO towns VALUES(?,?)',(town,json.dumps(initial())))
  _,_,view=self.join(town,'hub:'+subject)
  return view
 def touch(self,town,pid,p):
  k=(town,pid)
  if k not in self.live:self.live[k]={'x':p['x'],'y':p['y'],'direction':p['direction'],'seen':time.monotonic(),'stamp':time.monotonic(),'credit':.5,'working':False,'saved':time.monotonic(),'route':[],'disconnected':time.monotonic()}
  return self.live[k]
 def member(self,s,pid):
  if pid not in s['players']:raise PermissionError('Сначала войди в посёлок.')
  return s['players'][pid]
 def near(self,town,pid,p,place):
  q=self.touch(town,pid,p);a,b=PLACES[place]
  if math.hypot(q['x']-a,q['y']-b)>2.8:raise ValueError('Сначала подойди к месту действия.')
 def move(self,town,pid,x,y,direction):
  if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in [x,y,direction]) or not 0<=direction<=7:raise ValueError('Некорректное движение.')
  with self.lock,self.db() as d:
   s=self.load(d,town);p=self.member(s,pid);q=self.touch(town,pid,p);now=time.monotonic();q['seen']=now
   credit=min(1.5,q['credit']+max(0,now-q['stamp'])*1.6);q['stamp']=now;dist=math.hypot(x-q['x'],y-q['y'])
   if dist>credit+.03 or blocked(x,y):return {'position':{'x':q['x'],'y':q['y']},'corrected':True}
   # Check the segment too, so repeated small moves cannot cut through a house.
   if any(blocked(q['x']+(x-q['x'])*t/4,q['y']+(y-q['y'])*t/4) for t in range(1,5)):return {'position':{'x':q['x'],'y':q['y']},'corrected':True}
   q.update(x=x,y=y,direction=int(direction),credit=max(0,credit-dist))
   if now-q['saved']>=1:p.update(x=x,y=y,direction=int(direction));self.save(d,town,s);q['saved']=now
   return {'corrected':False}
 def present(self,town,pid):
  q=self.live.get((town,pid))
  return bool(q and (self.streams.get((town,pid),0)>0 or time.monotonic()-q.get('disconnected',q['seen'])<30))
 def route(self,town,pid,target):
  with self.lock,self.db() as d:
   s=self.load(d,town);p=self.member(s,pid);q=self.touch(town,pid,p);q['working']=False
   if target is None:q['route']=[];return self.view(town,s,pid)
   if not isinstance(target,dict) or not all(isinstance(target.get(k),(int,float)) and not isinstance(target.get(k),bool) and math.isfinite(target[k]) for k in ['x','y']):raise ValueError('Некорректная цель.')
   tx,ty=round(target['x']),round(target['y'])
   if blocked(tx,ty):raise ValueError('Здесь пройти нельзя.')
   start=(round(q['x']),round(q['y']));queue=deque([start]);prev={start:None}
   while queue and len(prev)<18000:
    x,y=queue.popleft()
    if (x,y)==(tx,ty):break
    for a,b in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]:
     nxt=(x+a,y+b)
     if nxt in prev or blocked(*nxt) or blocked(x+a,y) or blocked(x,y+b):continue
     prev[nxt]=(x,y);queue.append(nxt)
   if (tx,ty) not in prev:raise ValueError('Путь не найден.')
   path=[];v=(tx,ty)
   while prev[v] is not None:path.append(v);v=prev[v]
   path.reverse();q['route']=path
   return self.view(town,s,pid)
 def action(self,town,pid,kind,rid):
  if not isinstance(rid,str) or not 1<=len(rid)<=80:raise ValueError('Нет идентификатора операции.')
  with self.lock,self.db() as d:
   d.execute('BEGIN IMMEDIATE');s=self.load(d,town);p=self.member(s,pid);q=self.touch(town,pid,p)
   if d.execute('SELECT 1 FROM receipts WHERE town=? AND player=? AND id=?',(town,pid,rid)).fetchone():return self.view(town,s,pid)
   text=None
   if kind=='stop':q['working']=False;q['route']=[];return self.view(town,s,pid)
   if kind=='accept':
    self.near(town,pid,p,'board')
    if s['phase']!='available':raise ValueError('Общий заказ уже принят.')
    s['money']['treasury']-=300;s['money']['escrow']=300;s['phase']='accepted';text=p['name']+' принял общий заказ. В резерве 300 монет.'
   elif kind=='buy':
    self.near(town,pid,p,'supplier')
    if s['phase']!='accepted' or any(v['stone'] for v in s['players'].values()):raise ValueError('Щебень уже куплен или пока не нужен.')
    if p['balance']<120 or s['stone']['supplier']<20:raise ValueError('Не хватает денег или щебня.')
    p['balance']-=120;p['spent']+=120;p['stone']=20;s['money']['supplier']+=120;s['stone']['supplier']-=20;text=p['name']+' купил 20 ед. щебня за 120 монет.'
   elif kind=='deliver':
    self.near(town,pid,p,'site')
    if s['phase']!='accepted' or p['stone']!=20:raise ValueError('Материалы сейчас у другого строителя или ещё не куплены.')
    p['stone']=0;s['stone']['site']=20;s['phase']='delivered';text=p['name']+' доставил щебень на участок.'
   elif kind=='work':
    self.near(town,pid,p,'site')
    if s['phase'] not in ['delivered','building']:raise ValueError('Участок пока не готов к работе или уже отремонтирован.')
    q['seen']=time.monotonic();q['working']=True;q['route']=[];return self.view(town,s,pid)
   elif kind=='claim':
    self.near(town,pid,p,'board')
    if s['phase']!='ready' or s['money']['escrow']!=300:raise ValueError('Работа ещё не готова или уже оплачена.')
    workers=[k for k,v in s['players'].items() if v['work']>=.5]
    if not workers:raise ValueError('Не найден вклад строителей.')
    profit=300-sum(v['spent'] for v in s['players'].values());base,remainder=divmod(profit,len(workers))
    for k,v in s['players'].items():v['balance']+=v['spent']+(base+(workers.index(k)<remainder) if k in workers else 0)
    s['money']['escrow']=0;s['phase']='paid';text='Посёлок принял дорогу. Затраты возвращены покупателю, прибыль разделена между работавшими строителями.'
   else:raise ValueError('Неизвестное действие.')
   s['revision']+=1;s['journal'].append({'id':s['revision'],'type':kind,'text':text});self.save(d,town,s);d.execute('INSERT INTO receipts VALUES(?,?,?)',(town,pid,rid));return self.view(town,s,pid)
 def tick(self,dt):
  with self.lock,self.db() as d:
   self.motion_clock=time.monotonic()
   for town,raw in d.execute("SELECT id,state FROM towns"):
    s=json.loads(raw)
    moved=False
    for pid,p in s['players'].items():
     q=self.live.get((town,pid))
     if not q or not q.get('route'):continue
     if not self.present(town,pid):q['route']=[];continue
     budget=1.075*dt
     while q['route'] and budget>0:
      x,y=q['route'][0];dx=x-q['x'];dy=y-q['y'];dist=math.hypot(dx,dy)
      if dist<.001:q['route'].pop(0);continue
      step=min(budget,dist);q['x']+=dx/dist*step;q['y']+=dy/dist*step;budget-=step;q['direction']=round(math.atan2(dx,-dy)/(math.pi/4))%8;moved=True
      if step==dist:q['route'].pop(0)
     p.update(x=q['x'],y=q['y'],direction=q['direction'])
    if moved and time.monotonic()-self.position_saved.get(town,0)>=.5:
     self.save(d,town,s);self.position_saved[town]=time.monotonic()
    if s['phase'] not in ['delivered','building']:continue
    workers=[]
    for pid,p in s['players'].items():
     q=self.live.get((town,pid));a,b=PLACES['site']
     if q and q['working'] and self.present(town,pid) and self.streams.get((town,pid),0)>0 and math.hypot(q['x']-a,q['y']-b)<=2.8:workers.append(pid)
     elif q:q['working']=False
    if not workers:continue
    for pid in workers:s['players'][pid]['work']+=dt
    s['phase']='building';s['effort']+=dt*len(workers)
    if s['effort']>=5:
     s['effort']-=5;s['progress']+=1;s['journal'].append({'id':s['revision']+1,'type':'stage','text':['Подготовлено основание.','Уложено покрытие.','Участок отремонтирован. Можно сдавать работу.'][s['progress']-1]})
     if s['progress']==3:
      s['phase']='ready';s['effort']=0;s['stone']['site']=0;s['stone']['road']=20
      for pid in s['players']:self.live.get((town,pid),{}).update(working=False)
    s['revision']+=1;self.save(d,town,s)
 def view(self,town,s,pid):
  p=self.member(s,pid);now=time.monotonic();members=[]
  for k,v in s['players'].items():
   q=self.live.get((town,k),v);active=self.present(town,k)
   members.append({'id':k[:12],'me':k==pid,'name':v['name'],'x':q['x'],'y':q['y'],'direction':q['direction'],'working':bool(q.get('working') and active),'online':active,'moving':bool(q.get('route')),'balance':v['balance'],'work':round(v['work'],1)})
  phase=s['phase'];o=None
  if phase=='accepted' and not p['stone'] and any(v['stone'] for v in s['players'].values()):o={'place':'site','action':None,'title':'Встреть напарника на участке','body':'Щебень уже куплен. Подожди доставку и помоги с ремонтом.','button':'Материалы в пути'}
  result={k:s[k] for k in ['version','revision','phase','progress','effort','journal']};result.update(motionClock=self.motion_clock,renderDelay=self.render_delay,capacity=self.max_players,boot=self.boot,clock=time.monotonic(),town=town,money={**s['money'],'player':p['balance']},stone={**s['stone'],'player':p['stone']},members=members,me=next(v for v in members if v['me']),onlineCount=sum(v['online'] for v in members))
  if o:result['objective']=o
  if phase=='paid':result['objective']={'place':'site','action':None,'title':'Общая дорога готова','body':'Оплата сохранена на сервере. Дорога останется после выхода игроков.','button':'Посмотреть дорогу'}
  return result
 def snapshot(self,town,pid):
  with self.lock,self.db() as d:return self.view(town,self.load(d,town),pid)
class Handler(BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def setup(self):
  super().setup();self.connection.settimeout(12)
 def log_message(self,*a):pass
 def send_json(self,body,code=200,cookie=None):
  raw=json.dumps(body,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
  if cookie:self.send_header('Set-Cookie',f'lt_town_session={cookie}; Path={self.server.cookie_path}; HttpOnly; SameSite=Lax; Max-Age=31536000'+('; Secure' if self.server.secure else ''))
  self.end_headers();self.wfile.write(raw)
 def identity(self):
  c=SimpleCookie();c.load(self.headers.get('Cookie',''))
  if getattr(self.server,'auth',None):
   raw=c.get('hub_access');self.claims=self.server.auth.verify(raw.value if raw else '')
   return '',digest('hub:'+self.claims['sub'])
  raw=c.get('lt_town_session');value=raw.value if raw else ''
  if value and (len(value)!=48 or any(c not in '0123456789abcdef' for c in value)):raise PermissionError('Некорректная сессия.')
  return value,digest(value) if value else ''
 def do_POST(self):
  try:
   origin=self.headers.get('Origin')
   if origin and origin!=self.server.origin:raise PermissionError('Чужой источник запроса.')
   if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('Нужен JSON.')
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<=8192:raise ValueError('Слишком большой запрос.')
   b=json.loads(self.rfile.read(n))
   if not isinstance(b,dict):raise ValueError('Нужен объект JSON.')
   raw,pid=self.identity();path=urlsplit(self.path).path
   if path=='/join' and getattr(self.server,'auth',None):
    self.send_json(self.server.store.join_account(self.claims['sub']));return
   if path=='/join':
    town,cookie,s=self.server.store.join(b.get('town'),raw,self.headers.get('X-Real-IP',self.client_address[0]));self.send_json(s,cookie=cookie);return
   if not pid:raise PermissionError('Нужно войти в посёлок.')
   if path=='/route':self.send_json(self.server.store.route(b['town'],pid,b.get('target')))
   elif path=='/move':self.send_json(self.server.store.move(b['town'],pid,b['x'],b['y'],b['direction']))
   elif path=='/action':self.send_json(self.server.store.action(b['town'],pid,b['type'],b['id']))
   else:self.send_json({'error':'Маршрут не найден'},404)
  except PermissionError as e:self.send_json({'error':str(e)},getattr(e,'status',403))
  except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:self.send_json({'error':str(e)},400)
 def do_GET(self):
  p=urlsplit(self.path)
  if p.path=='/health':self.send_json({'ok':True,'version':1});return
  try:
   _,pid=self.identity()
   if p.path=='/session':self.send_json({'account':pid,'expires':getattr(self,'claims',{}).get('exp')});return
   town=parse_qs(p.query).get('town',[''])[0];self.server.store.snapshot(town,pid)
   if p.path=='/state':self.send_json(self.server.store.snapshot(town,pid));return
   if p.path!='/events':self.send_json({'error':'Маршрут не найден'},404);return
   key=(town,pid)
   with self.server.store.lock:
    if self.server.store.streams.get(key,0)>=3 or sum(self.server.store.streams.values())>=32:raise ValueError('Слишком много вкладок посёлка.')
    self.server.store.streams[key]=self.server.store.streams.get(key,0)+1
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Connection','close');self.close_connection=True;self.send_header('Cache-Control','no-store');self.send_header('X-Accel-Buffering','no');self.end_headers()
   try:
    while True:
     if getattr(self.server,'auth',None) and time.time()>=self.claims['exp']:
      self.wfile.write(b'event: auth\ndata: {}\n\n');self.wfile.flush();break
     s=self.server.store.snapshot(town,pid);self.wfile.write(('data: '+json.dumps(s,ensure_ascii=False)+'\n\n').encode());self.wfile.flush();time.sleep(getattr(self.server,'snapshot_seconds',.4))
   except (BrokenPipeError,ConnectionResetError,TimeoutError):pass
   finally:
    with self.server.store.lock:
     self.server.store.streams[key]=max(0,self.server.store.streams.get(key,1)-1)
     if not self.server.store.streams[key]:self.server.store.live.get(key,{}).update(working=False,disconnected=time.monotonic())
  except PermissionError as e:self.send_json({'error':str(e)},getattr(e,'status',403))
  except (ValueError,KeyError) as e:self.send_json({'error':str(e)},400)
def main():
 a=argparse.ArgumentParser();a.add_argument('--db',required=True);a.add_argument('--port',type=int,default=8798);a.add_argument('--origin',default='https://michaelperov.com');a.add_argument('--cookie-path',default='/preview/living-town-online-v1/');a.add_argument('--hub-keys-url');a.add_argument('--tick-seconds',type=float,default=.25);a.add_argument('--snapshot-seconds',type=float,default=.4);args=a.parse_args();assert .02<=args.tick_seconds<=1 and .05<=args.snapshot_seconds<=1;Path(args.db).parent.mkdir(parents=True,exist_ok=True)
 server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.daemon_threads=True;server.store=Store(args.db,max_players=10 if args.hub_keys_url else 2,render_delay=args.tick_seconds+args.snapshot_seconds+.15);server.auth=None;server.snapshot_seconds=args.snapshot_seconds
 if args.hub_keys_url:
  from hub_auth import HubAuth
  server.auth=HubAuth(args.hub_keys_url)
 server.origin=args.origin;server.cookie_path=args.cookie_path;server.secure=args.origin.startswith('https:')
 def clock():
  last=time.monotonic()
  while True:
   time.sleep(max(0,last+args.tick_seconds-time.monotonic()));now=time.monotonic()
   server.store.tick(min(now-last,.25));last=now
 threading.Thread(target=clock,daemon=True).start();server.serve_forever()
if __name__=='__main__':main()
