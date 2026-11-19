import tempfile,unittest,sys,json,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
from online import Store,digest,PLACES
class OnlineTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'town.sqlite';self.s=Store(self.path);self.t,self.a,_=self.s.join(None,None);_,self.b,_=self.s.join(self.t,None);self.a=digest(self.a);self.b=digest(self.b)
 def tearDown(self):self.tmp.cleanup()
 def at(self,pid,place):
  with self.s.lock,self.s.db() as d:
   s=self.s.load(d,self.t);p=s['players'][pid];p['x'],p['y']=PLACES[place];self.s.save(d,self.t,s);q=self.s.touch(self.t,pid,p);q['x'],q['y']=PLACES[place];self.s.streams[(self.t,pid)]=1
 def act(self,pid,action,rid=None):return self.s.action(self.t,pid,action,rid or action+str(self.s.snapshot(self.t,pid)['revision']))
 def prepare(self):
  self.at(self.a,'board');self.act(self.a,'accept');self.at(self.a,'supplier');self.act(self.a,'buy');self.at(self.a,'site');self.act(self.a,'deliver')
 def test_position_checkpoints_do_not_delay_money_transactions(self):
  from unittest.mock import patch
  self.s.route(self.t,self.a,{'x':25,'y':-16});self.s.streams[(self.t,self.a)]=1
  with patch('online.time.monotonic',return_value=1000):
   self.s.tick(.05)
   with patch.object(self.s,'save',wraps=self.s.save) as save:
    for _ in range(8):self.s.tick(.05)
    self.assertEqual(save.call_count,0)
   with self.s.db() as d:persisted=self.s.load(d,self.t)['players'][self.a]['x']
   self.assertGreater(self.s.snapshot(self.t,self.a)['me']['x'],persisted)
  self.at(self.a,'board');self.act(self.a,'accept','durable-economy')
  restarted=Store(self.path);self.assertEqual(restarted.snapshot(self.t,self.a)['phase'],'accepted');restarted.close()
 def test_cooperative_repair_and_atomic_split(self):
  self.prepare();self.at(self.b,'site');self.act(self.a,'work');self.act(self.b,'work')
  for _ in range(30):self.s.tick(.25)
  self.assertEqual(self.s.snapshot(self.t,self.a)['phase'],'ready');self.at(self.a,'board');first=self.act(self.a,'claim','same-request');again=self.act(self.a,'claim','same-request')
  self.assertEqual(first['money']['player'],270);self.assertEqual(again['money']['player'],270);self.assertEqual(self.s.snapshot(self.t,self.b)['money']['player'],270);self.assertEqual(first['stone']['road'],20);self.assertEqual(sum(x['type']=='claim' for x in first['journal']),1)
  with self.assertRaises(ValueError):self.act(self.a,'claim','another-request')
  restarted=Store(self.path);self.assertEqual(restarted.snapshot(self.t,self.a)['phase'],'paid');self.assertEqual(restarted.snapshot(self.t,self.b)['money']['player'],270)
 def test_server_rejects_remote_actions_and_teleports(self):
  with self.assertRaises(ValueError):self.act(self.a,'buy')
  self.at(self.a,'board');self.act(self.a,'accept')
  with self.assertRaises(ValueError):self.act(self.a,'buy')
  result=self.s.move(self.t,self.a,20,-22,0);self.assertTrue(result['corrected'])
  with self.assertRaises(ValueError):self.s.move(self.t,self.a,float('nan'),-22,0)
  self.at(self.a,'site')
  with self.assertRaises(ValueError):self.act(self.a,'work')
 def test_concurrent_purchase_takes_only_one_batch(self):
  self.at(self.a,'board');self.act(self.a,'accept');self.at(self.a,'supplier');self.at(self.b,'supplier');success=[]
  def buy(pid):
   try:self.act(pid,'buy');success.append(pid)
   except ValueError:pass
  ts=[threading.Thread(target=buy,args=(p,)) for p in [self.a,self.b]]
  for t in ts:t.start()
  for t in ts:t.join()
  self.assertEqual(len(success),1)
  with self.s.db() as d:s=self.s.load(d,self.t)
  self.assertEqual(sum(p['stone'] for p in s['players'].values()),20);self.assertEqual(s['stone']['supplier'],60)
 def test_disconnect_and_restart_do_not_build_offline(self):
  self.prepare();self.act(self.a,'work');self.s.tick(.25);self.s.streams[(self.t,self.a)]=0;before=self.s.snapshot(self.t,self.a);self.s.tick(1)
  self.assertEqual(self.s.snapshot(self.t,self.a)['effort'],before['effort']);new=Store(self.path);new.tick(1);self.assertEqual(new.snapshot(self.t,self.a)['effort'],before['effort'])
 def test_route_and_presence_do_not_depend_on_client_frames(self):
  with self.s.db() as d:
   state=self.s.load(d,self.t);q=self.s.touch(self.t,self.a,state['players'][self.a])
  self.s.streams[(self.t,self.a)]=1;q['seen']-=60
  self.s.route(self.t,self.a,{'x':20,'y':-16})
  for _ in range(40):self.s.tick(.25)
  view=self.s.snapshot(self.t,self.a)
  self.assertTrue(view['me']['online']);self.assertAlmostEqual(view['me']['x'],20);self.assertFalse(view['me']['moving'])
  with self.assertRaises(ValueError):self.s.route(self.t,self.a,{'x':0,'y':0})
  self.s.route(self.t,self.a,{'x':22,'y':-16});self.s.route(self.t,self.a,None);x=self.s.snapshot(self.t,self.a)['me']['x'];self.s.tick(.25);self.assertEqual(self.s.snapshot(self.t,self.a)['me']['x'],x)
 def test_invite_room_isolation_and_two_places(self):
  with self.assertRaises(ValueError):self.s.join(self.t,None)
  other,cookie,_=self.s.join(None,None)
  with self.assertRaises(PermissionError):self.s.snapshot(other,self.a)
  self.assertNotEqual(other,self.t)
if __name__=='__main__':unittest.main()
