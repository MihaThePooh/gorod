"""Validate hub access tokens using public Ed25519 keys only."""
import json
import threading
import time
import urllib.request

import jwt


class AuthError(PermissionError):
    def __init__(self, detail, status=401):
        super().__init__(detail)
        self.status = status


class HubAuth:
    def __init__(self, keys_url):
        self.keys_url = keys_url
        self.keys = {}
        self.fetched = -60.0
        self.lock = threading.Lock()

    def verify(self, token):
        if not token:
            raise AuthError('not_authenticated')
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            if header.get('alg') != 'EdDSA' or not isinstance(kid, str):
                raise AuthError('token_invalid')
            with self.lock:
                if kid not in self.keys and time.monotonic() - self.fetched >= 60:
                    self.fetched = time.monotonic()
                    try:
                        with urllib.request.urlopen(self.keys_url, timeout=5) as response:
                            data = json.load(response)
                        fresh = {k['kid']: jwt.PyJWK(k).key for k in data['keys']
                                 if k.get('kty') == 'OKP' and k.get('crv') == 'Ed25519' and isinstance(k.get('kid'), str)}
                        if fresh:
                            self.keys = fresh
                    except Exception:
                        if not self.keys:
                            raise AuthError('keys_unavailable', 503)
                key = self.keys.get(kid)
            if key is None:
                raise AuthError('token_invalid' if self.keys else 'keys_unavailable', 401 if self.keys else 503)
            claims = jwt.decode(token, key, algorithms=['EdDSA'], issuer='hub-id',
                                options={'require': ['sub', 'exp', 'iat']})
            if not isinstance(claims['sub'], str) or not claims['sub']:
                raise AuthError('token_invalid')
            if not isinstance(claims.get('apps'), list) or 'town' not in claims['apps']:
                raise AuthError('app_not_enabled', 403)
            return claims
        except jwt.ExpiredSignatureError:
            raise AuthError('token_expired')
        except jwt.InvalidTokenError:
            raise AuthError('token_invalid')
