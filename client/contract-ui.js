import {ORDER,PLACES,initial,valid,apply,objective} from './construction.js';
const KEY='living-town-contract-v1',POSITION=KEY+'-position';
const stageNames=['Подготовка основания','Укладка покрытия','Уплотнение покрытия'];
export function createContract({player,camera,route,blocked,setWorking,toast,project,assets}){
 const $=id=>document.getElementById(id);let state=initial(),storageError=false,busy=false,running=false,elapsed=0,uiClock=0,positionClock=0;
 try{const raw=localStorage.getItem(KEY);if(raw){const loaded=JSON.parse(raw);if(!valid(loaded))throw Error('invalid');state=loaded}else localStorage.setItem(KEY,JSON.stringify(state));const p=JSON.parse(localStorage.getItem(POSITION)||'null');if(p&&Number.isFinite(p.x)&&Number.isFinite(p.y)&&!blocked(p.x,p.y)){player.x=p.x;player.y=p.y;camera.x=p.x;camera.y=p.y}}catch{state=initial();storageError=true}
 function distance(name){const p=PLACES[name];return Math.hypot(player.x-p.x,player.y-p.y)}
 function stop(){running=false;elapsed=0;setWorking(false)}
 function refresh(){
  const next=objective(state),near=distance(next.place)<2.8;$('taskTitle').textContent=next.title;$('taskBody').textContent=running?stageNames[state.progress]+'…':next.body;
  $('wallet').textContent=state.money.player;$('stoneCount').textContent=state.stone.player;$('orderPhase').textContent=state.phase==='paid'?'Заказ сдан':`Этап ${Math.min(4,state.journal.length?state.phase==='accepted'?state.stone.player?3:2:state.phase==='ready'?5:4:1)} из 5`;
  $('nextAction').disabled=busy||storageError||running;$('nextAction').textContent=storageError?'Сохранение недоступно':running?'Идёт ремонт…':near?next.button:`${{board:'К доске',supplier:'К складу',site:'К участку'}[next.place]} · ${Math.ceil(distance(next.place))} м`;
  $('buildProgress').hidden=!['delivered','building','ready','paid'].includes(state.phase);$('buildProgress').value=state.progress+(running?elapsed/ORDER.stageSeconds:0);$('stepStatus').textContent=state.phase==='paid'?'Принят посёлком':state.phase==='ready'?'Можно сдавать работу':`${state.progress} из 3 этапов ремонта`;
  $('savedStatus').textContent=storageError?'Не удалось прочитать или записать сохранение. Скопируй важный прогресс перед сбросом пробы.':'Прогресс сохраняется на этом устройстве.';
  $('savedStatus').classList.toggle('save-error',storageError);$('taskStep').textContent=state.phase==='paid'?'ГОТОВО':'ДОРОЖНЫЙ ЗАКАЗ № 001';
  if($('orderDialog').open)details();
 }
 function details(){
  const list=$('orderSteps');list.replaceChildren();
  const done=[state.phase!=='available',state.phase!=='available'&&(state.stone.player===20||!['accepted','available'].includes(state.phase)),['delivered','building','ready','paid'].includes(state.phase),['ready','paid'].includes(state.phase),state.phase==='paid'];
  ['Принять заказ у доски','Купить 20 ед. щебня у Николая','Доставить щебень к ограждению','Отремонтировать участок','Сдать работу и получить 300 монет'].forEach((text,i)=>{const li=document.createElement('li');li.textContent=text;li.classList.toggle('complete',done[i]);if(!done[i]&&(i===0||done[i-1]))li.classList.add('current');list.append(li)});
  $('treasury').textContent=state.money.treasury;$('escrow').textContent=state.money.escrow;$('supplierStock').textContent=state.stone.supplier;$('siteStock').textContent=state.stone.site;$('roadStock').textContent=state.stone.road;
  $('orderLog').replaceChildren();for(const entry of state.journal){const li=document.createElement('li');li.textContent=entry.text;$('orderLog').append(li)}
  if(!state.journal.length){const li=document.createElement('li');li.textContent='Пока нет операций.';$('orderLog').append(li)}
 }
 async function dispatch(type){
  if(busy||storageError)return false;busy=true;refresh();
  const commit=()=>{const raw=localStorage.getItem(KEY);const latest=raw?JSON.parse(raw):initial();if(!valid(latest))throw Error('Сохранение заказа повреждено.');const next=apply(latest,type);localStorage.setItem(KEY,JSON.stringify(next));state=next;return state.journal.at(-1).text};
  try{const message=navigator.locks?await navigator.locks.request(KEY,commit):commit();toast(message);refresh();return true}catch(e){stop();if(e.name==='QuotaExceededError'||e.name==='SecurityError'){storageError=true;toast('Не удалось сохранить прогресс. Освободи место или разреши хранение данных сайта.')}else toast(e.message);return false}finally{busy=false;refresh()}
 }
 $('nextAction').onclick=async()=>{
  const next=objective(state);if(distance(next.place)>=2.8){route(PLACES[next.place]);return}
  if(!next.action){route(PLACES.site);return}
  if(next.action==='work'){running=true;elapsed=0;setWorking(true);refresh();return}
  await dispatch(next.action);
 };
 $('orderDetails').onclick=()=>{details();$('orderDialog').showModal()};$('closeOrder').onclick=()=>$('orderDialog').close();
 $('orderDialog').addEventListener('click',e=>{if(e.target===$('orderDialog')){const b=e.target.getBoundingClientRect();if(e.clientX<b.left||e.clientX>b.right||e.clientY<b.top||e.clientY>b.bottom)e.target.close()}});
 $('resetOrder').onclick=async()=>{if(!confirm('Начать пробный заказ заново? Баланс, материалы и ремонт этой пробы будут сброшены.'))return;stop();const reset=()=>{state=initial();localStorage.setItem(KEY,JSON.stringify(state));localStorage.removeItem(POSITION)};try{if(navigator.locks)await navigator.locks.request(KEY,reset);else reset();storageError=false;$('orderDialog').close();route(PLACES.board);toast('Начата новая проба заказа.');refresh()}catch{toast('Не удалось сохранить новую пробу.')}};
 addEventListener('storage',e=>{if(e.key!==KEY||!e.newValue)return;try{const other=JSON.parse(e.newValue);if(!valid(other))throw Error();stop();state=other;storageError=false;refresh()}catch{storageError=true;stop();refresh()}});
 function savePosition(){try{localStorage.setItem(POSITION,JSON.stringify({x:player.x,y:player.y}))}catch{}}
 addEventListener('pagehide',savePosition);document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();savePosition()}});
 function update(dt){
  if(running){if(distance('site')>=2.8){stop();toast('Ремонт приостановлен. Вернись на участок, чтобы продолжить.')}else if(!busy){elapsed+=dt;if(elapsed>=ORDER.stageSeconds){elapsed=0;dispatch('stage').then(ok=>{if(!ok||state.phase==='ready')stop();refresh()})}}}
  uiClock+=dt;positionClock+=dt;if(uiClock>.2){refresh();uiClock=0}if(positionClock>1){savePosition();positionClock=0}
 }
 function mapTap(x,y){for(const [name,p] of Object.entries(PLACES)){const q=project(p.x,p.y);if(Math.hypot(x-q.x,y-(q.y-24))<25){if(distance(name)<2.8){if(name===objective(state).place)$('nextAction').click();else{details();$('orderDialog').showModal()}}else route(p);return true}}return false}
 function road(ctx,scale){
  const p=project(0,0);ctx.save();ctx.transform(.81496*scale,.3938*scale,.57945*scale,-.5539*scale,p.x,p.y);
  ctx.fillStyle=state.progress===0?'#696154':state.progress===1?'#a29a83':'#454c4b';ctx.fillRect(14,-17,8,6);
  if(state.progress===0){ctx.strokeStyle='#272c27';ctx.lineWidth=.15;for(let i=0;i<5;i++){ctx.beginPath();ctx.moveTo(14+i*1.5,-11.3);ctx.lineTo(15+i*1.4,-14.2);ctx.lineTo(14.6+i*1.4,-16.6);ctx.stroke()}ctx.fillStyle='#34332c';for(const [x,y] of [[16,-13],[19,-15.5],[20,-12]]){ctx.beginPath();ctx.ellipse(x,y,.6,.38,0,0,Math.PI*2);ctx.fill()}}
  if(state.progress===1){ctx.fillStyle='#756d59';for(let i=0;i<42;i++){const x=14+(i*1.73%7.8),y=-17+(i*1.27%5.8);ctx.fillRect(x,y,.12,.12)}}
  if(state.progress>=2){const image=assets().images.asphalt;const pattern=ctx.createPattern(image,'repeat');pattern.setTransform(new DOMMatrix().scale(5/image.width));ctx.globalAlpha=.6;ctx.fillStyle=pattern;ctx.fillRect(14,-17,8,6);ctx.globalAlpha=1}
  if(state.progress===3){ctx.strokeStyle='#dddcc8';ctx.lineWidth=.11;ctx.setLineDash([2.4,3.6]);ctx.beginPath();ctx.moveTo(14,-14);ctx.lineTo(22,-14);ctx.stroke();ctx.setLineDash([])}
  ctx.strokeStyle=state.phase==='paid'?'#7b9d7c':'#edc160';ctx.lineWidth=.10;ctx.strokeRect(14,-17,8,6);
  if(state.phase!=='paid')for(const [x,y] of [[14,-17],[22,-17],[14,-11],[22,-11]]){ctx.fillStyle='#c58637';ctx.beginPath();ctx.moveTo(x-.18,y);ctx.lineTo(x,y-.45);ctx.lineTo(x+.18,y);ctx.closePath();ctx.fill()}
  ctx.restore();
 }
 function landmark(ctx,name,scale){
  const p=PLACES[name],q=project(p.x,p.y),k=Math.max(.7,Math.min(1.3,scale/16));ctx.save();ctx.translate(q.x,q.y);
  if(name==='board'){
   ctx.fillStyle='#493f2b';ctx.fillRect(-15*k,-32*k,30*k,25*k);ctx.fillStyle='#dbcfaa';ctx.fillRect(-12*k,-29*k,24*k,18*k);ctx.strokeStyle='#76674a';ctx.lineWidth=k;for(let i=0;i<3;i++){ctx.beginPath();ctx.moveTo(-8*k,(-25+i*4)*k);ctx.lineTo(8*k,(-25+i*4)*k);ctx.stroke()}ctx.fillStyle='#59472f';ctx.fillRect(-12*k,-8*k,3*k,8*k);ctx.fillRect(9*k,-8*k,3*k,8*k);
  }else if(name==='supplier'){
   ctx.fillStyle='#6e7460';ctx.fillRect(-25*k,-27*k,40*k,25*k);ctx.fillStyle='#3b493d';ctx.beginPath();ctx.moveTo(-31*k,-26*k);ctx.lineTo(-5*k,-42*k);ctx.lineTo(23*k,-26*k);ctx.closePath();ctx.fill();ctx.fillStyle='#c1ae7b';ctx.fillRect(-18*k,-18*k,13*k,16*k);ctx.fillStyle='#aaa38a';ctx.beginPath();ctx.moveTo(4*k,0);ctx.lineTo(18*k,-15*k);ctx.lineTo(31*k,0);ctx.closePath();ctx.fill();
   const {images,atlas}=assets(),idle=atlas.states.idle;const spriteScale=scale/(atlas.frameHeight/2.5);ctx.drawImage(images.worker,(idle.start%atlas.columns)*atlas.frameWidth,0,atlas.frameWidth,atlas.frameHeight,22*k,-atlas.anchor[1]*spriteScale,atlas.frameWidth*spriteScale,atlas.frameHeight*spriteScale);
  }else{ctx.strokeStyle=state.progress===3?'#8db093':'#edc160';ctx.lineWidth=2*k;ctx.beginPath();ctx.ellipse(0,0,12*k,6*k,0,0,Math.PI*2);ctx.stroke()}
  const active=objective(state).place===name;if(active||distance(name)<3){const text=p.name;ctx.font='600 11px system-ui';const w=ctx.measureText(text).width;ctx.fillStyle=active?'#314b3cef':'#283e30df';ctx.fillRect(-w/2-8,-58*k,w+16,22);ctx.fillStyle=active?'#ffe0a1':'#f0ecd9';ctx.textAlign='center';ctx.fillText(text,0,-43*k)}ctx.restore();
 }
 refresh();return {update,stop,mapTap,road,landmark,places:PLACES,get state(){return structuredClone(state)},get running(){return running},get activePlace(){return objective(state).place},get objective(){return objective(state)}};
}
