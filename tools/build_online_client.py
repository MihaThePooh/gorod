"""Build a separate online preview from the accepted solo client without replacing it."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1];source=root/'client';out=root/'.online-client-v1';out.mkdir(exist_ok=True)
files=['index.html','style.css','game.js','surfaces.js','construction.js','online-network.js','hub-session.js','motion-timeline.js']
for n in files:shutil.copyfile(source/n,out/n)
shutil.copytree(source/'assets',out/'assets',dirs_exist_ok=True)
s=(source/'contract-ui.js').read_text().replace('valid,apply,objective','valid,apply,objective as soloObjective')
s=s.replace("const KEY=", "import {network} from './online-network.js';\nconst objective=s=>s.objective||soloObjective(s);\nconst KEY=",1)
a=s.index(' try{const raw=localStorage');b=s.index(' function distance',a)
s=s[:a]+" const backend=network({player,camera,toast,setWorking});\n"+s[b:]
s=s.replace("function stop(){running=false;elapsed=0;setWorking(false)}", "function stop(){if(backend.ready&&state.me?.working)backend.action('stop').catch(()=>{});running=false;elapsed=0;setWorking(false)}")
s=s.replace('busy||storageError||running','busy||storageError||running||!backend.ready').replace("storageError?'Сохранение недоступно'", "!backend.ready?'Подключение к посёлку…':storageError?'Сохранение недоступно'")
s=s.replace("state.progress+(running?elapsed/ORDER.stageSeconds:0)", "state.progress+(state.effort||0)/5")
s=s.replace("'Прогресс сохраняется на этом устройстве.'", "'Город и расчёты сохраняются на сервере. Затраты на щебень возвращаются покупателю, общая прибыль делится между работавшими строителями.'")
s=s.replace("state.phase!=='available'&&(state.stone.player===20||!['accepted','available'].includes(state.phase))", "state.stone.supplier<80")
a=s.index(' async function dispatch(');b=s.index(" $('nextAction').onclick",a)
s=s[:a]+''' async function dispatch(type){
  if(busy||!backend.ready)return false;busy=true;refresh();
  try{state=await backend.action(type);return true}catch(e){toast(e.message);return false}finally{busy=false;refresh()}
 }
'''+s[b:]
s=s.replace("if(next.action==='work'){running=true;elapsed=0;setWorking(true);refresh();return}", "if(next.action==='work'){await dispatch('work');return}")
a=s.index(" $('resetOrder').onclick");b=s.index(' function update(dt)',a)
s=s[:a]+" $('resetOrder').onclick=()=>{location.href=new URL('.',location.href)};\n"+s[b:]
a=s.index(' function update(dt)');b=s.index(' function mapTap',a)
s=s[:a]+''' function update(dt){backend.tick(dt);uiClock+=dt;if(running&&distance('site')>=2.8)stop();if(uiClock>.2){refresh();uiClock=0}}
'''+s[b:]
s=s.replace(" refresh();return {update", " backend.subscribe(next=>{state=next;const working=backend.ready&&next.me.working;if(working!==running)setWorking(working);running=working;refresh()});\n refresh();return {get me(){return backend.me},routeIntent:target=>backend.route(target),steer:(x,y)=>backend.steer(x,y),get canMove(){return backend.ready},get others(){return backend.others},update")
# A completed shared order belongs in the archive, not in the active objective HUD.
s=s.replace(" function refresh(){", " function refresh(){\n  const paid=state.phase==='paid';$('contractHud').hidden=paid;$('finishedNotice').hidden=!paid;\n  $('orderDetails').textContent='Заказы';$('orderDialogTitle').textContent=paid?'Выполненный заказ':'Ремонт дороги';\n  $('orderDescription').textContent=paid?'Дорога отремонтирована и принята посёлком. Оплата сохранена.':'Восстановить покрытие на ограждённом участке. Заказчик — посёлок.';")
s=s.replace(" $('nextAction').onclick=async()=>{", " $('nextAction').onclick=async()=>{\n  if(state.phase==='paid'){details();$('orderDialog').showModal();return}")
s=s.replace("function mapTap(x,y){for(const [name,p] of Object.entries(PLACES)){", "function mapTap(x,y){for(const [name,p] of Object.entries(PLACES)){if(state.phase==='paid'&&name==='site')continue;")
s=s.replace("ctx.strokeStyle=state.phase==='paid'?'#7b9d7c':'#edc160';ctx.lineWidth=.10;ctx.strokeRect(14,-17,8,6);", "if(state.phase!=='paid'){ctx.strokeStyle='#edc160';ctx.lineWidth=.10;ctx.strokeRect(14,-17,8,6);}")
s=s.replace(" function landmark(ctx,name,scale){", " function landmark(ctx,name,scale){\n  if(state.phase==='paid'&&name==='site')return;")
s=s.replace("backend.subscribe(next=>{state=next;", "backend.subscribe(next=>{const completed=!!state.me&&state.phase!=='paid'&&next.phase==='paid';state=next;if(completed)toast('Заказ выполнен. Оплата сохранена. История — в «Заказах».');")
(out/'online-contract.js').write_text(s)
s=(out/'game.js').read_text().replace("from './contract-ui.js'", "from './online-contract.js'")
s=s.replace("function route(target){", "function route(target){\n if(construction&&!construction.canMove){toast('Подожди подключения к посёлку.');return false}")
s=s.replace("function update(dt){", "function update(dt){\n if(construction&&!construction.canMove){path=[];keys.clear();work=false;return}")
s=s.replace('function worker(){','function worker(who=player,color=\'#f0c776\'){')
a=s.index('function worker(');b=s.index('function draw()',a);chunk=s[a:b].replace('player.','who.').replace("ctx.strokeStyle='#f0c776'","ctx.strokeStyle=color")
chunk=chunk.replace("\n}\n", "\n if(who.name){ctx.font='600 11px system-ui';ctx.fillStyle='#1f392e';const w=ctx.measureText(who.name).width;ctx.fillRect(p.x-w/2-4,p.y-2.6*s-12,w+8,17);ctx.fillStyle='#c2f0ed';ctx.textAlign='center';ctx.fillText(who.name,p.x,p.y-2.6*s)}\n}\n")
s=s[:a]+chunk+s[b:]
s=s.replace("const objects=[...Object.entries", "const objects=[...(construction.others||[]).map(p=>({depth:dx*p.x+dy*p.y,draw:()=>worker(p,'#88d5dd')})),...Object.entries")
a=s.index('function route(target){');b=s.index('function updateWork()',a)
s=s[:a]+"""function route(target){
 if(!construction?.canMove){toast('Подожди подключения к посёлку.');return false}
 if(blocked(target.x,target.y)){toast('Здесь пройти нельзя.');return false}
 construction.routeIntent(target);path=[target];camera.follow=true;return true;
}
"""+s[b:]
a=s.index('function update(dt){');b=s.index('async function makeGround()',a)
s=s[:a]+"""function update(dt){
 const before={x:player.x,y:player.y};construction.update(dt);
 let vx=0,vy=0;
 if(keys.has('w')||keys.has('ц')||keys.has('arrowup'))vy-=1;if(keys.has('s')||keys.has('ы')||keys.has('arrowdown'))vy+=1;
 if(keys.has('a')||keys.has('ф')||keys.has('arrowleft'))vx-=1;if(keys.has('d')||keys.has('в')||keys.has('arrowright'))vx+=1;
 const det=rx*dy-ry*dx,a=(dy*vx-ry*vy)/det,b=(-dx*vx+rx*vy)/det,len=Math.hypot(a,b);
 construction.steer(len?a/len:0,len?b/len:0);
 const moved=Math.hypot(player.x-before.x,player.y-before.y),me=construction.me;
 // The route flag leads the interpolation buffer; animate only rendered displacement.
 player.walkDistance+=moved;const state=me?.working?'work':moved>.00001?'walk':'idle';
 if(state!==player.state){player.time=0;player.state=state}player.time+=dt;
 if(!me?.moving)path=[];ui.state.textContent=state==='work'?'Ремонтирует дорогу':state==='walk'?'Идёт к месту':'Готов к работе';
 if(camera.follow){const t=1-Math.exp(-dt*7);camera.x+=(player.x-camera.x)*t;camera.y+=(player.y-camera.y)*t}
}
"""+s[b:]
(out/'game.js').write_text(s)
s=(out/'index.html').read_text().replace('Живой город — первый заказ','Живой город — совместная стройка').replace('Первый строительный заказ','Общий посёлок · совместный ремонт').replace('<b>Строитель</b>','<b id="playerLabel">Строитель</b>').replace('Чистый заработок','Общая прибыль').replace('Начать пробу заново','Другой посёлок')
s=s.replace('<div class="day">14:30 <span class="weather">ясно</span></div>', '<div class="day online-day"><span id="onlineStatus">Подключение…</span><button id="shareTown">Пригласить</button></div>')
s=s.replace('<script type="module"', '''<dialog id="townLobby" aria-labelledby="lobbyTitle"><span class="task-label">ПЕРВЫЙ СЕТЕВОЙ ПОСЁЛОК</span><h2 id="lobbyTitle">Построим вместе</h2><p>Открой посёлок и отправь ссылку напарнику. Вы будете видеть друг друга и ремонтировать одну дорогу.</p><p class="muted">В этом стенде два места. Город и оплата сохраняются на сервере. Сохрани ссылку: она возвращает в тот же посёлок.</p><button id="newTown" class="primary-action">Открыть новый посёлок</button><p id="lobbyError" role="status"></p></dialog><dialog id="inviteDialog"><h2>Приглашение в посёлок</h2><p>Отправь эту ссылку напарнику. Для двух игроков на одном компьютере открой её в другом браузере или приватном окне.</p><input id="inviteLink" readonly aria-label="Ссылка приглашения"><button id="closeInvite">Закрыть</button></dialog><script type="module"''')
s=s.replace('<p class="muted">Восстановить покрытие', '<p id="orderDescription" class="muted">Восстановить покрытие')
s=s.replace('<p id="orderPhase">', '<section id="finishedNotice" hidden><b>Доступные работы выполнены</b><p>Новых заказов пока нет. Можно свободно исследовать посёлок. История ремонта и расчёты сохранены ниже.</p></section><p id="orderPhase">')
(out/'index.html').write_text(s)
with (out/'style.css').open('a') as f:f.write('''\n#contractHud[hidden],#finishedNotice[hidden]{display:none}#finishedNotice{padding:12px;margin:12px 0;background:#d9e3c9;border-left:3px solid #46664b;color:#273f31}#finishedNotice p{margin:6px 0 0;font-size:13px;line-height:1.5}.online-day{display:flex;align-items:center;gap:10px;pointer-events:auto;font-size:12px}.online-day button{font-size:11px;padding:7px;border-radius:3px}#inviteLink{width:100%;padding:10px;color:#273f31;background:#fff8e5;border:1px solid #a6b49b;margin-bottom:16px}#townLobby p{font-size:13px;line-height:1.6}#townLobby h2{font:normal 26px Georgia,serif}#lobbyError{color:#904b30}@media(max-width:600px){.online-day{position:fixed;right:12px;top:105px;flex-direction:column;align-items:stretch;padding:6px;font-size:10px;width:86px;gap:5px}#contractHud{width:calc(100vw - 120px);max-width:290px}#contractHud h2{font-size:16px}#contractHud p{font-size:11px}}\n''')
print('ONLINE_CLIENT_BUILT')
