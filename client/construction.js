// Prototype accounting is pure and testable; a future server must own these transitions.
export const ORDER=Object.freeze({id:'road-001',reward:300,stone:20,unitPrice:6,stages:3,stageSeconds:2.5});
export const PLACES=Object.freeze({board:{x:8,y:-19,name:'Доска заказов'},supplier:{x:20,y:-22,name:'Склад · Николай'},site:{x:18,y:-14,name:'Ремонт дороги'}});
export function initial(){return {version:1,revision:0,phase:'available',progress:0,money:{player:180,supplier:400,treasury:1000,escrow:0},stone:{player:0,supplier:80,site:0,road:0},journal:[]}}
export function valid(s){
 if(!s||s.version!==1||!['available','accepted','delivered','building','ready','paid'].includes(s.phase)||!Number.isSafeInteger(s.revision)||s.revision<0||!Number.isSafeInteger(s.progress)||s.progress<0||s.progress>3)return false;
 for(const [bucket,names] of [['money',['player','supplier','treasury','escrow']],['stone',['player','supplier','site','road']]])if(!s[bucket]||names.some(n=>!Number.isSafeInteger(s[bucket][n])||s[bucket][n]<0)||Object.keys(s[bucket]).length!==names.length)return false;
 if(Object.values(s.money).reduce((a,b)=>a+b,0)!==1580||Object.values(s.stone).reduce((a,b)=>a+b,0)!==80)return false;
 if(s.money.escrow!==(['accepted','delivered','building','ready'].includes(s.phase)?300:0))return false;
 if((['ready','paid'].includes(s.phase))!==(s.progress===3))return false;
 if(['available','accepted'].includes(s.phase)&&s.progress!==0)return false;
 if(['delivered','building'].includes(s.phase)&&s.stone.site!==20)return false;
 if(['ready','paid'].includes(s.phase)&&(s.stone.road!==20||s.stone.site!==0))return false;
 if(!['ready','paid'].includes(s.phase)&&s.stone.road!==0)return false;
 if(!Array.isArray(s.journal)||s.journal.length>20)return false;
 return true;
}
export function apply(state,type){
 if(!valid(state))throw new Error('Сохранение заказа повреждено.');
 const s=structuredClone(state);let text;
 switch(type){
 case 'accept':
  if(s.phase!=='available')throw new Error('Заказ уже принят.');
  if(s.money.treasury<ORDER.reward)throw new Error('В казне не хватает денег.');
  s.money.treasury-=300;s.money.escrow+=300;s.phase='accepted';text='Заказ принят. 300 монет зарезервированы в казне.';break;
 case 'buy':
  if(s.phase!=='accepted'||s.stone.player||s.stone.site)throw new Error('Материалы для этого заказа уже куплены или пока не нужны.');
  if(s.money.player<120)throw new Error('Не хватает 120 монет на материалы.');
  if(s.stone.supplier<20)throw new Error('На складе не хватает щебня.');
  s.money.player-=120;s.money.supplier+=120;s.stone.supplier-=20;s.stone.player+=20;text='Куплено 20 ед. щебня за 120 монет.';break;
 case 'deliver':
  if(s.phase!=='accepted'||s.stone.player<20)throw new Error('Сначала купи щебень на складе.');
  s.stone.player-=20;s.stone.site+=20;s.phase='delivered';text='20 ед. щебня доставлены на участок.';break;
 case 'stage':
  if(!['delivered','building'].includes(s.phase)||s.progress>=3||s.stone.site!==20)throw new Error('Ремонт сейчас недоступен.');
  s.progress++;s.phase=s.progress===3?'ready':'building';if(s.progress===3){s.stone.site-=20;s.stone.road+=20}text=['Подготовлено основание дороги.','Уложено новое покрытие.','Покрытие уплотнено. Ремонт готов к сдаче.'][s.progress-1];break;
 case 'claim':
  if(s.phase!=='ready'||s.money.escrow!==300)throw new Error('Этот заказ ещё не готов или уже оплачен.');
  s.money.escrow-=300;s.money.player+=300;s.phase='paid';text='Заказ сдан. Получено 300 монет, дорога принята посёлком.';break;
 default:throw new Error('Неизвестное действие.');
 }
 s.revision++;s.journal.push({id:s.revision,type,text});if(!valid(s))throw new Error('Нарушен баланс заказа.');return s;
}
export function objective(s){
 if(s.phase==='available')return {place:'board',action:'accept',title:'Возьми первый заказ',body:'Посёлку нужен ремонт участка дороги.',button:'Взять заказ'};
 if(s.phase==='accepted'&&!s.stone.player)return {place:'supplier',action:'buy',title:'Купи щебень у Николая',body:'20 ед. щебня · 120 монет за весь заказ.',button:'Купить щебень · 120'};
 if(s.phase==='accepted')return {place:'site',action:'deliver',title:'Доставь щебень на участок',body:'Материалы у тебя. Принеси их к ограждению.',button:'Доставить материалы'};
 if(['delivered','building'].includes(s.phase))return {place:'site',action:'work',title:'Отремонтируй дорогу',body:'Подготовь основание, уложи покрытие и уплотни его.',button:s.progress?'Продолжить ремонт':'Начать ремонт'};
 if(s.phase==='ready')return {place:'board',action:'claim',title:'Сдай готовую работу',body:'Вернись к доске заказов за оплатой.',button:'Сдать заказ · +300'};
 return {place:'site',action:null,title:'Первый заказ выполнен',body:'Дорога отремонтирована. Чистый заработок — 180 монет.',button:'Посмотреть дорогу'};
}
