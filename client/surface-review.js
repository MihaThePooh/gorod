import { createGround } from './surfaces.js';
const canvas=document.querySelector('canvas'),ctx=canvas.getContext('2d');
const images={};
await Promise.all(['grass','asphalt','dirt','paving'].map(async name=>{const im=new Image();im.src=name==='paving'?'assets/paving.png':`assets/${name}-v2.webp`;await im.decode();images[name]=im}));
const ground=createGround(ctx,images),views={grass:[22,-31],asphalt:[24,-14],broken:[-44,-14],dirt:[-28,14]};
const descriptions={grass:'Один базовый рисунок травы: зелень, сухие места, пучки и редкие листья.',asphalt:'Спокойный серый асфальт, тонкая белая разметка и неровная пыльная обочина.',broken:'Тот же асфальт: поверх — трещины, заплаты, небольшие выбоины и две лужи.',dirt:'Светлая грунтовка: две колеи, немного травы по центру и неровные края.'};
let selected='grass';
function draw(){const d=Math.min(devicePixelRatio||1,2),w=innerWidth,h=innerHeight;canvas.width=w*d;canvas.height=h*d;const s=1000/43*Number(document.querySelector('#scale').value);ctx.setTransform(d,0,0,d,0,0);ctx.fillStyle='#a5ac8b';ctx.fillRect(0,0,w,h);const[x,y]=views[selected];ctx.translate(w/2,h*.56);ctx.transform(.81496*s,.3938*s,.57945*s,-.5539*s,0,0);ctx.translate(-x,-y);ground.draw(ctx)}
for(const button of document.querySelectorAll('[data-view]'))button.onclick=()=>{selected=button.dataset.view;for(const b of document.querySelectorAll('[data-view]'))b.setAttribute('aria-pressed',String(b===button));document.querySelector('#description').textContent=descriptions[selected];draw()};
document.querySelector('#scale').oninput=draw;addEventListener('resize',draw);draw();window.surfaceReview={get selected(){return selected},ready:true};
