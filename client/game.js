import { createGround } from './surfaces.js';
import { createContract } from './contract-ui.js';
import { PLACES } from './construction.js';
const canvas=document.querySelector('#world'),ctx=canvas.getContext('2d');
const ui={loading:document.querySelector('#loading'),zoom:document.querySelector('#zoom'),state:document.querySelector('#state'),hint:document.querySelector('#hint')};
const PPU=1000/43,MIN=.30,MAX=1.6,rx=.81496,ry=.57945,dx=.3938,dy=-.5539;
const houses=[{x:0,y:0},{x:-38,y:27},{x:34,y:32}];
const player={x:12,y:-16,direction:0,state:'idle',time:0,walkDistance:0,speed:0,heading:0};
const camera={x:player.x,y:player.y,zoom:innerWidth<600?.43:.66,follow:true};
let width=0,height=0,dpr=1,path=[],keys=new Set(),ready=false,clock=0;
let construction=null;
let images={},panel,atlas,ground,worldSeed=29,pointers=new Map(),drag=null,pinch=null,work=false;
function rand(){worldSeed=(Math.imul(worldSeed,1664525)+1013904223)|0;return (worldSeed>>>0)/4294967296}
function resize(){width=innerWidth;height=innerHeight;dpr=Math.min(devicePixelRatio||1,2);const w=Math.round(width*dpr),h=Math.round(height*dpr);if(canvas.width!==w)canvas.width=w;if(canvas.height!==h)canvas.height=h}
addEventListener('resize',resize);resize();
function project(x,y,z=0){return {x:(rx*(x-camera.x)+ry*(y-camera.y))*PPU*camera.zoom+width/2,y:(dx*(x-camera.x)+dy*(y-camera.y)-.735*z)*PPU*camera.zoom+height*.57}}
function unproject(x,y){const u=(x-width/2)/(PPU*camera.zoom),v=(y-height*.57)/(PPU*camera.zoom),det=rx*dy-ry*dx;return {x:camera.x+(dy*u-ry*v)/det,y:camera.y+(-dx*u+rx*v)/det}}
function blocked(x,y){return x< -62||x>62||y< -62||y>62||houses.some(h=>Math.abs(x-h.x)<15.45&&Math.abs(y-h.y)<5.45)}
function toast(text){const t=document.querySelector('#toast');t.textContent=text;t.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.classList.remove('show'),2400)}
function setZoom(z){camera.zoom=Math.max(MIN,Math.min(MAX,z));ui.zoom.value=camera.zoom.toFixed(2)}
function route(target){
 if(blocked(target.x,target.y)){toast('Здесь пройти нельзя. Выбери место на земле.');return false}
 const sx=Math.round(player.x),sy=Math.round(player.y),tx=Math.round(target.x),ty=Math.round(target.y),key=(x,y)=>`${x},${y}`;
 const queue=[[sx,sy]],prev=new Map([[key(sx,sy),null]]);let found=null;
 for(let i=0;i<queue.length&&i<18000;i++){
  const [x,y]=queue[i];if(x===tx&&y===ty){found=[x,y];break}
  for(const [a,b] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,-1],[1,-1],[-1,1]]){
   const nx=x+a,ny=y+b,k=key(nx,ny);if(prev.has(k)||blocked(nx,ny)||blocked(x+a,y)||blocked(x,y+b))continue;
   prev.set(k,[x,y]);queue.push([nx,ny]);
  }
 }
 if(!found){toast('Путь не найден. Попробуй выбрать место ближе.');return false}
 path=[];for(let p=found;prev.get(key(...p));p=prev.get(key(...p)))path.push({x:p[0],y:p[1]});path.reverse();
 construction?.stop();work=false;updateWork();return true;
}
function updateWork(){ui.state.textContent=work?'Ремонтирует дорогу':path.length?'Идёт к месту':'Готов к работе'}
document.querySelector('#follow').onclick=()=>{camera.follow=true};
document.querySelector('#plus').onclick=()=>setZoom(camera.zoom+.10);document.querySelector('#minus').onclick=()=>setZoom(camera.zoom-.10);ui.zoom.oninput=()=>setZoom(Number(ui.zoom.value));
document.querySelector('#help').onclick=()=>{ui.hint.hidden=!ui.hint.hidden};
canvas.addEventListener('wheel',e=>{e.preventDefault();setZoom(camera.zoom*Math.exp(-e.deltaY*.001))},{passive:false});
function beginPinch(){
 const [a,b]=[...pointers.values()],x=(a.x+b.x)/2,y=(a.y+b.y)/2;
 pinch={distance:Math.hypot(a.x-b.x,a.y-b.y),zoom:camera.zoom,anchor:unproject(x,y)};
 camera.follow=false;if(drag)drag.moved=true;
}
canvas.addEventListener('pointerdown',e=>{
 if(!ready)return;canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
 if(pointers.size===1)drag={x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,moved:false};
 if(pointers.size>=2)beginPinch();
});
canvas.addEventListener('pointermove',e=>{
 if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
 if(pointers.size>=2&&pinch){
  const[a,b]=[...pointers.values()];setZoom(pinch.zoom*Math.hypot(a.x-b.x,a.y-b.y)/Math.max(pinch.distance,1));
  const under=unproject((a.x+b.x)/2,(a.y+b.y)/2);camera.x+=pinch.anchor.x-under.x;camera.y+=pinch.anchor.y-under.y;return;
 }
 if(drag&&pointers.size===1){
  if(Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)>7)drag.moved=true;
  if(drag.moved){const a=unproject(drag.x,drag.y),b=unproject(e.clientX,e.clientY);camera.x+=a.x-b.x;camera.y+=a.y-b.y;camera.follow=false;drag.x=e.clientX;drag.y=e.clientY}
 }
});
function pointerUp(e,allowTap=true){
 if(!pointers.has(e.pointerId))return;
 const tap=allowTap&&pointers.size===1&&drag&&!drag.moved&&!pinch;
 pointers.delete(e.pointerId);
 if(tap&&!construction?.mapTap(e.clientX,e.clientY))route(unproject(e.clientX,e.clientY));
 if(pointers.size>=2){beginPinch();return}
 pinch=null;
 // Continue from the remaining finger, never from the pre-pinch drag origin.
 if(pointers.size===1){const p=[...pointers.values()][0];drag={x:p.x,y:p.y,startX:p.x,startY:p.y,moved:true}}
 else drag=null;
}
canvas.addEventListener('pointerup',e=>pointerUp(e));
canvas.addEventListener('pointercancel',e=>pointerUp(e,false));
canvas.addEventListener('lostpointercapture',e=>pointerUp(e,false));
addEventListener('keydown',e=>{if(e.target.matches('input,button')||document.querySelector('dialog[open]'))return;if(['w','a','s','d','ц','ф','ы','в','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();keys.add(e.key.toLowerCase());construction?.stop();path=[];work=false;updateWork()}});
addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));addEventListener('blur',()=>{keys.clear();pointers.clear();drag=null;pinch=null});
function update(dt){
 let vx=0,vy=0;
 if(keys.has('w')||keys.has('ц')||keys.has('arrowup'))vy-=1;if(keys.has('s')||keys.has('ы')||keys.has('arrowdown'))vy+=1;
 if(keys.has('a')||keys.has('ф')||keys.has('arrowleft'))vx-=1;if(keys.has('d')||keys.has('в')||keys.has('arrowright'))vx+=1;
 // Keyboard directions follow the screen, not hidden world axes.
 if(vx||vy){const det=rx*dy-ry*dx,a=(dy*vx-ry*vy)/det,b=(-dx*vx+rx*vy)/det;vx=a;vy=b;camera.follow=true}
 else {while(path.length&&Math.hypot(path[0].x-player.x,path[0].y-player.y)<.09)path.shift();if(path.length){vx=path[0].x-player.x;vy=path[0].y-player.y}}
 const len=Math.hypot(vx,vy);let moving=false;const desired=len>.001?Math.min(atlas.walkSpeed||1.075,path.length===1?len*4:Infinity):0;player.speed+=(desired-player.speed)*(1-Math.exp(-10*dt));
 if(len>.001){vx/=len;vy/=len;const step=Math.min(player.speed*dt,len);
  if(!blocked(player.x+vx*step,player.y+vy*step)){player.x+=vx*step;player.y+=vy*step;player.walkDistance+=step;moving=step>.0001}
  else if(path.length)path=[];
  const targetHeading=Math.atan2(vx,-vy),delta=Math.atan2(Math.sin(targetHeading-player.heading),Math.cos(targetHeading-player.heading));player.heading+=delta*(1-Math.exp(-12*dt));player.direction=(Math.round(player.heading/(Math.PI/4))+8)%8;
 }
 const state=moving?'walk':work?'work':'idle';if(player.state!==state){player.time=0;player.state=state;updateWork()}player.time+=dt;
 construction?.update(dt);
 if(camera.follow){const t=1-Math.exp(-dt*7);camera.x+=(player.x-camera.x)*t;camera.y+=(player.y-camera.y)*t}
}
async function makeGround(){const map=document.createElement('canvas');map.width=map.height=2304;const c=map.getContext('2d');c.setTransform(16,0,0,16,72*16,72*16);createGround(c,images,houses).draw(c);return createImageBitmap(map)}
const trees=[];for(let i=0;i<90;i++){const x=rand()*126-63,y=rand()*126-63;if(!Object.values(PLACES).some(p=>Math.hypot(p.x-x,p.y-y)<10)&&!blocked(x,y)&&Math.abs(y+14)>7&&!(Math.abs(x)<23&&y<1&&y> -25))trees.push({x,y,size:4+rand()*2.5,hue:rand()})}
// Cache the expensive affine ground transform around the viewport; walking only blits it.
let groundView=null;
function drawGround(){
 const p=project(-72,-72),s=PPU*camera.zoom/16,pad=160;
 if(!groundView||groundView.zoom!==camera.zoom||groundView.width!==width||groundView.height!==height||groundView.dpr!==dpr||Math.abs(p.x-groundView.x)>pad||Math.abs(p.y-groundView.y)>pad){
  const image=document.createElement('canvas');image.width=Math.ceil((width+pad*2)*dpr);image.height=Math.ceil((height+pad*2)*dpr);const c=image.getContext('2d');
  c.setTransform(dpr,0,0,dpr,pad*dpr,pad*dpr);c.transform(rx*s,dx*s,ry*s,dy*s,p.x,p.y);c.drawImage(ground,0,0);
  groundView={image,x:p.x,y:p.y,zoom:camera.zoom,width,height,dpr};
 }
 ctx.drawImage(groundView.image,p.x-groundView.x-pad,p.y-groundView.y-pad,groundView.image.width/dpr,groundView.image.height/dpr);
}
function tree(t){const p=project(t.x,t.y),k=PPU*camera.zoom/(384/8.5)*(t.size/6);const pad=40*camera.zoom;if(p.x+128*k+pad<0||p.x-128*k-pad>width||p.y-(192+3*.735*384/8.5)*k+384*k+pad<0||p.y-(192+3*.735*384/8.5)*k-pad>height)return;ctx.save();ctx.fillStyle='#203b2828';ctx.beginPath();ctx.ellipse(p.x+9*camera.zoom,p.y,24*camera.zoom,8*camera.zoom,0,0,Math.PI*2);ctx.fill();ctx.drawImage(images.birch,p.x-128*k,p.y-(192+3*.735*384/8.5)*k,256*k,384*k);ctx.restore()}
function house(h){const p=project(h.x,h.y),k=(1000/1200)*camera.zoom;const nearPlayer=player.x>h.x-15.5&&player.x<h.x+15.5&&player.y>h.y+5;
 const left=p.x-panel.anchor_pixel[0]*k,top=p.y-panel.anchor_pixel[1]*k;if(left+images.panel.width*k<0||left>width||top+images.panel.height*k<0||top>height)return;
 ctx.save();if(nearPlayer)ctx.globalAlpha=.4;ctx.drawImage(images.panel,p.x-panel.anchor_pixel[0]*k,p.y-panel.anchor_pixel[1]*k,images.panel.width*k,images.panel.height*k);ctx.restore()}
function worker(){const p=project(player.x,player.y),s=PPU*camera.zoom;ctx.fillStyle='#1b312c38';ctx.beginPath();ctx.ellipse(p.x,p.y,.40*s,.16*s,0,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#f0c776';ctx.lineWidth=1.5;ctx.beginPath();ctx.ellipse(p.x,p.y,.48*s,.24*s,0,0,Math.PI*2);ctx.stroke();
 const info=atlas.states[player.state],phase=player.state==='walk'?player.walkDistance/atlas.strideMeters*info.count:player.time*(info.fps||atlas.fps),f=info.start+Math.floor(phase)%info.count,k=PPU*camera.zoom/(atlas.frameHeight/2.5);
 ctx.drawImage(images.worker,(f%atlas.columns)*atlas.frameWidth,(player.direction*(atlas.directionRows||1)+Math.floor(f/atlas.columns))*atlas.frameHeight,atlas.frameWidth,atlas.frameHeight,p.x-atlas.frameWidth*.5*k,p.y-atlas.anchor[1]*k,atlas.frameWidth*k,atlas.frameHeight*k)
}
function draw(){ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#69764d';ctx.fillRect(0,0,width,height);if(!ready)return;
 drawGround();construction?.road(ctx,PPU*camera.zoom);if(path.length){const p=project(path.at(-1).x,path.at(-1).y);ctx.strokeStyle='#f0c776';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(p.x,p.y,7*camera.zoom+3,4*camera.zoom+2,0,0,Math.PI*2);ctx.stroke()}
 const objects=[...Object.entries(construction.places).map(([name,p])=>({depth:dx*p.x+dy*p.y,draw:()=>construction.landmark(ctx,name,PPU*camera.zoom)})),...houses.map(h=>({depth:dx*h.x+dy*h.y,draw:()=>house(h)})),...trees.map(t=>({depth:dx*t.x+dy*t.y,draw:()=>tree(t)})),{depth:dx*player.x+dy*player.y,draw:worker}];objects.sort((a,b)=>a.depth-b.depth);for(const o of objects)o.draw();
 // Front foliage subtly frames the playable world without covering controls.
}
let last=performance.now();function frame(now){const dt=Math.min((now-last)/1000,.25);last=now;clock+=dt;if(ready)update(dt);draw();requestAnimationFrame(frame)}requestAnimationFrame(frame);
async function loadImage(name){const im=new Image();im.src=['grass','asphalt','dirt'].includes(name)?`assets/${name}-v2.webp`:`assets/${name}.png`;await im.decode();images[name]=im}
construction=createContract({player,camera,route,blocked,setWorking:value=>{work=value;if(value)path=[];updateWork()},toast,project,assets:()=>({images,atlas})});
try{
 await Promise.all(['panel','worker','grass','asphalt','dirt','paving','birch'].map(loadImage));
 [panel,atlas]=await Promise.all(['panel.json','worker.json'].map(async n=>{const r=await fetch(`assets/${n}`);if(!r.ok)throw Error(n);return r.json()}));
 ground=await makeGround();ready=true;ui.loading.classList.add('done');setZoom(camera.zoom);
 setTimeout(()=>{ui.hint.style.opacity='.0';setTimeout(()=>{ui.hint.hidden=true;ui.hint.style.opacity='1'},250)},13000);
}catch(e){ui.loading.textContent='Не удалось загрузить посёлок. Обнови страницу.';console.error(e)}
// Read-only diagnostics are shared by automated QA and the local teaching notes.
window.townDebug={get destination(){return path.length?{...path.at(-1)}:null},get ready(){return ready},get player(){return {...player}},get camera(){return {...camera}},get blocked(){return blocked(player.x,player.y)},project,unproject,route,setZoom,get construction(){return {state:construction.state,running:construction.running,activePlace:construction.activePlace}}};
