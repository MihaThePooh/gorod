"""Audit the staged publication allowlist and reproduce the recorded browser build."""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path(__file__).resolve().parents[1]
files=[s for s in subprocess.check_output(['git','-C',str(root),'diff','--cached','--name-only','-z']).decode().split('\0') if s]
assert files,'no staged release files'
secret=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-proj-[A-Za-z0-9_-]{35,}')
for name in files:
 p=root/name;assert not p.is_symlink(),name
 assert not name.startswith('art/references/'),name
 assert not any(part in ['__pycache__','node_modules','.git'] for part in p.relative_to(root).parts),name
 assert p.suffix not in ['.sqlite','.db','.pem','.key','.env','.zip','.blend1'],name
 assert p.stat().st_size<90*1024*1024,name
 if p.suffix in ['.py','.js','.cjs','.mjs','.md','.json','.html','.css','.txt','.sh','']:
  assert not secret.search(p.read_bytes()),'credential-like content: '+name
version=(root/'VERSION').read_text().strip()
release=json.loads((root/'releases'/f'{version}.json').read_text())
for name,value in release['public_files'].items():
 p=root/'.gorod-client-v1'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==value,'release browser mismatch: '+name
for name,value in release['server_files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==value,'release server mismatch: '+name
print(json.dumps({'staged_files':len(files),'source_bytes':sum((root/n).stat().st_size for n in files),'largest':sorted([{'name':n,'bytes':(root/n).stat().st_size} for n in files],key=lambda v:v['bytes'],reverse=True)[:5],'private_paths_excluded':True,'release_hashes_verified':len(release['public_files'])+len(release['server_files'])}))
