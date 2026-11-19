import {MotionTimeline} from './motion-timeline.js';
import {accountMode,hubFetch,login} from './hub-session.js';
// The server advances walking and work; rendering may pause without pausing the town.
export function network({player,camera,toast,setWorking}){
 let reconnecting=false,identity=null;
 let state=null,connected=false,town=new URL(location.href).searchParams.get('town'),source=null,listener=()=>{},lastSteer=0,steering=false,initialized=false;
 const timeline=new MotionTimeline();const peers=new Map();const endpoint=new URL('api/',location.href);
 async function post(path,body){const c=new AbortController(),timer=setTimeout(()=>c.abort(),7000);try{const r=await (accountMode?hubFetch:fetch)(new URL(path,endpoint),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:c.signal});const data=await r.json();if(!r.ok)throw Error(data.error||'Сервер не принял действие.');return data}finally{clearTimeout(timer)}}
 function receive(next){
  if(accountMode&&identity&&identity!==next.me.id){location.reload();return}identity=next.me.id;
  if(state&&(next.revision<state.revision||(next.boot===state.boot&&next.clock<state.clock)))return;state=next;timeline.push(next,performance.now()/1000);
  if(!initialized||Math.hypot(player.x-next.me.x,player.y-next.me.y)>1.8){player.x=next.me.x;player.y=next.me.y;camera.x=player.x;camera.y=player.y;setWorking(false);initialized=true}
  for(const p of next.members.filter(p=>!p.me&&p.online)){
   const peer=peers.get(p.id)||{...p,time:0,walkDistance:0,state:'idle'};peer.target={x:p.x,y:p.y};peer.working=p.working;peer.direction=p.direction;peer.name=p.name;peer.seen=performance.now();peers.set(p.id,peer)
  }
  for(const [id] of peers)if(!next.members.some(p=>p.id===id&&p.online))peers.delete(id);
  document.querySelector('#shareTown').disabled=false;document.querySelector('#onlineStatus').textContent=`В посёлке: ${next.onlineCount} / ${next.capacity||2}`;document.querySelector('#playerLabel').textContent=next.me.name;
  listener(next);
 }
 async function join(create=false){
  const button=document.querySelector('#newTown');button.disabled=true;
  try{const next=await post('join',{town:create?null:town});town=next.town;const u=new URL(location.href);u.searchParams.set('town',town);history.replaceState(null,'',u);receive(next);document.querySelector('#townLobby').close();
   source?.close();source=new EventSource(new URL('events?town='+town,endpoint));source.onmessage=e=>{connected=true;receive(JSON.parse(e.data))};source.addEventListener('auth',()=>recover());source.onerror=()=>{connected=false;setWorking(false);document.querySelector('#onlineStatus').textContent='Связь прервана · подключаюсь…';listener(state);if(accountMode)recover()};
  }catch(e){document.querySelector('#lobbyError').textContent=e.name==='AbortError'?'Сервер не ответил. Попробуй ещё раз.':e.message;document.querySelector('#townLobby').showModal()}finally{button.disabled=false}
 }
 async function recover(){
  if(reconnecting||!accountMode)return;reconnecting=true;source?.close();connected=false;setWorking(false);
  try{const r=await hubFetch(new URL('session',endpoint));if(!r.ok)throw Error('Сервис входа временно недоступен.');const session=await r.json();if(identity&&session.account.slice(0,12)!==identity){location.reload();return}await join()}
  catch(e){document.querySelector('#onlineStatus').textContent='Нет связи · повторяю…';setTimeout(recover,5000)}finally{reconnecting=false}
 }
 const api={get ready(){return connected&&!!state},get me(){return state?.me},get state(){return state},get others(){return [...peers.values()]},subscribe(fn){listener=fn;if(state)fn(state)},async route(target){if(!connected||!town)return;steering=false;try{receive(await post('route',{town,target}))}catch(e){toast(e.message)}},steer(x,y){if(!connected)return;if(x||y){if(performance.now()-lastSteer<220)return;lastSteer=performance.now();steering=true;post('route',{town,target:{x:player.x+x*2,y:player.y+y*2}}).then(receive).catch(()=>{})}else if(steering){steering=false;post('route',{town,target:null}).then(receive).catch(()=>{})}},async action(type){
  if(!connected||!town)throw Error('Нет связи с посёлком. Подожди переподключения.');const body={town,type,id:crypto.randomUUID()};let last;
  for(let attempt=0;attempt<2;attempt++){try{const next=await post('action',body);receive(next);return next}catch(e){last=e;if(e.name!=='AbortError'&&!(e instanceof TypeError))break}}
  throw Error(last?.name==='AbortError'?'Сервер не ответил. Состояние обновится после подключения.':last?.message||'Нет связи с сервером.');
 },tick(dt){
  const rendered=timeline.sample(performance.now()/1000);
  for(const peer of peers.values()){
   const p=rendered?.find(p=>p.id===peer.id);if(!p)continue;
   const d=Math.hypot(p.x-peer.x,p.y-peer.y);peer.x=p.x;peer.y=p.y;peer.direction=p.direction;
   peer.walkDistance+=d;peer.state=peer.working?'work':d>.0001?'walk':'idle';peer.time+=dt;
  }
  if(state&&connected){const p=rendered?.find(p=>p.me);if(p){player.x=p.x;player.y=p.y;player.direction=p.direction}}


 }};
 document.querySelector('#townLobby').addEventListener('cancel',e=>{if(!state)e.preventDefault()});
 document.querySelector('#newTown').onclick=()=>join(true);document.querySelector('#shareTown').onclick=async()=>{try{await navigator.clipboard.writeText(location.href);toast('Ссылка скопирована. Открой её на другом устройстве или отправь напарнику.')}catch{document.querySelector('#inviteLink').value=location.href;document.querySelector('#inviteDialog').showModal();document.querySelector('#inviteLink').select()}};
 document.querySelector('#closeInvite').onclick=()=>document.querySelector('#inviteDialog').close();
 addEventListener('focus',async()=>{if(!accountMode||!state)return;try{const r=await hubFetch(new URL('session',endpoint));if(r.ok){const current=await r.json();if(current.account.slice(0,12)!==identity){source?.close();connected=false;location.reload()}}}catch{/* The stream handles transient connection failures. */}});
 addEventListener('blur',()=>{if(steering)api.steer(0,0)});
 addEventListener('pagehide',()=>{source?.close();if(town)navigator.sendBeacon(new URL('action',endpoint),new Blob([JSON.stringify({town,type:'stop',id:crypto.randomUUID()})],{type:'application/json'}))});
 if(accountMode){town=null;document.querySelector('#shareTown').hidden=true;document.querySelector('#resetOrder').hidden=true;document.querySelector('#newTown').textContent='Повторить вход';join()}else if(town)join();else document.querySelector('#townLobby').showModal();return api;
}
