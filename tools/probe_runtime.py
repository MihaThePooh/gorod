import shutil
from pathlib import Path
for name in ('node','chromium','google-chrome','rsync','ssh'):
 print(name,shutil.which(name))
print('playwright',Path('/projects/tools/uitest/node_modules/playwright').is_dir())
print('browser_cache',[(p.name) for p in (Path.home()/'.cache/ms-playwright').glob('*')])
