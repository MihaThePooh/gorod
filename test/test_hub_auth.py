"""Account identity and signature checks without using real accounts or signing keys."""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
from hub_auth import HubAuth, AuthError
from online import Store, digest

class AccountTests(unittest.TestCase):
 def setUp(self):
  self.key=Ed25519PrivateKey.generate();self.auth=HubAuth('http://unused/keys');self.auth.keys={'test':self.key.public_key()}
 def signed(self,**kw):
  return jwt.encode({'sub':'synthetic-account-a','iss':'hub-id','iat':int(time.time()),'exp':int(time.time())+60,'apps':['town'],**kw},self.key,algorithm='EdDSA',headers={'kid':'test'})
 def test_valid_expired_wrong_issuer_and_permissions(self):
  self.assertEqual(self.auth.verify(self.signed())['sub'],'synthetic-account-a')
  for args,detail in [({'exp':int(time.time())-1},'token_expired'),({'iss':'other'},'token_invalid'),({'apps':['todo']},'app_not_enabled')]:
   with self.assertRaises(AuthError) as e:self.auth.verify(self.signed(**args))
   self.assertEqual(str(e.exception),detail)
 def test_forged_and_unsigned_tokens_rejected(self):
  forged=jwt.encode({'sub':'x','iss':'hub-id','iat':int(time.time()),'exp':int(time.time())+30,'apps':['town']},Ed25519PrivateKey.generate(),algorithm='EdDSA',headers={'kid':'test'})
  for raw in ['', 'junk',forged,jwt.encode({'sub':'x'},'not-a-key',algorithm='HS256',headers={'kid':'test'})]:
   with self.assertRaises(AuthError):self.auth.verify(raw)
 def test_keys_outage_has_503_not_login_failure(self):
  self.auth.keys={}
  with patch('urllib.request.urlopen',side_effect=OSError('unavailable')):
   with self.assertRaises(AuthError) as e:self.auth.verify(self.signed())
  self.assertEqual(e.exception.status,503)
 def test_device_recovery_shared_world_and_limit(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'accounts.sqlite';s=Store(path,max_players=10)
   first=s.join_account('a');second=s.join_account('b');self.assertEqual(first['town'],second['town']);self.assertNotEqual(first['me']['id'],second['me']['id'])
   with s.db() as d:
    state=s.load(d,first['town']);state['players'][digest('hub:a')]['x']=23;s.save(d,first['town'],state)
   recovered=Store(path,max_players=10).join_account('a');self.assertEqual(recovered['me']['id'],first['me']['id']);self.assertEqual(recovered['me']['x'],23);self.assertEqual(len(recovered['members']),2)
   for i in range(8):s.join_account('more-'+str(i))
   with self.assertRaises(ValueError):s.join_account('eleventh')
   self.assertEqual(len(s.join_account('a')['members']),10)
if __name__=='__main__':unittest.main()
