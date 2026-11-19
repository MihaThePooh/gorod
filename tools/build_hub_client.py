"""Generate the account build separately; keep both accepted preview builds intact."""
from pathlib import Path
import json
import argparse
import shutil
import subprocess
import sys
root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(root/'tools/build_online_client.py')], check=True)
parser=argparse.ArgumentParser();parser.add_argument('--base-path',default='/town/');parser.add_argument('--out',default='.hub-client-v1');args=parser.parse_args()
assert args.base_path.startswith('/') and args.base_path.endswith('/')
source, out = root/'.online-client-v1', root/args.out
out.mkdir(exist_ok=True)
names = ['index.html','style.css','game.js','surfaces.js','construction.js','online-contract.js','online-network.js','hub-session.js','motion-timeline.js']
for name in names:
    shutil.copyfile(source/name, out/name)
shutil.copytree(source/'assets', out/'assets', dirs_exist_ok=True)
s = (out/'index.html').read_text().replace('<title>', '<meta name="town-auth" content="hub"><meta name="hub-id" content="https://id.michaelperov.com"><meta name="hub-home" content="https://hub.michaelperov.com"><link rel="manifest" href="manifest.webmanifest"><link rel="apple-touch-icon" href="icons/icon-192.png"><script src="pwa.js" defer></script><title>', 1)
s = s.replace('ПЕРВЫЙ СЕТЕВОЙ ПОСЁЛОК', 'ЖИВОЙ ГОРОД').replace('Построим вместе','Вход в город').replace('Открой посёлок и отправь ссылку напарнику. Вы будете видеть друг друга и ремонтировать одну дорогу.','Войди по почте через хаб. Персонаж и заработок сохраняются в твоём аккаунте.').replace('В этом стенде два места. Город и оплата сохраняются на сервере. Сохрани ссылку: она возвращает в тот же посёлок.','На телефоне и компьютере — один персонаж. Для совместной игры нужен отдельный аккаунт напарника.')
s=s.replace('<button id="shareTown">', '<button id="installTown" hidden>Установить</button><a class="hub-link" href="https://hub.michaelperov.com/">Хаб</a><button id="shareTown" hidden>')
s=s.replace('Для двух игроков на одном компьютере открой её в другом браузере или приватном окне.', 'Напарнику нужен свой аккаунт хаба.')
s=s.replace('</body>', '<dialog id="installHelp"><h2>Установить «Живой город»</h2><p id="installText"></p><p>Игра требует подключения к интернету. Прогресс хранится в аккаунте хаба.</p><button id="closeInstall">Закрыть</button></dialog></body>')
(out/'index.html').write_text(s)
with (out/'style.css').open('a') as f:
    f.write('\n.hub-link{color:inherit;text-align:center;padding:6px}#installHelp{max-width:360px}#installHelp p{line-height:1.6;font-size:14px}\n')
for name in ['pwa.js','sw.js','offline.html']:
    shutil.copyfile(root/'client/pwa'/name,out/name)
shutil.copytree(root/'client/pwa/icons',out/'icons',dirs_exist_ok=True)
manifest={'id':args.base_path,'name':'Живой город','short_name':'Город','lang':'ru','start_url':args.base_path,'scope':args.base_path,'display':'standalone','background_color':'#26372e','theme_color':'#26372e','icons':[{'src':f'icons/icon-{n}.png','sizes':f'{n}x{n}','type':'image/png','purpose':'any'} for n in [192,512]]}
(out/'manifest.webmanifest').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('HUB_CLIENT_BUILT')
