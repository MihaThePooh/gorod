const {chromium}=require('/projects/tools/town-browser/node_modules/playwright-core');const assert=require('node:assert/strict'),fs=require('fs');
(async()=>{const browser=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage','--disable-background-timer-throttling','--disable-renderer-backgrounding']});try{const result=process.env.ONLY_AFTER?[JSON.parse(fs.readFileSync('/workspace/motion-qa.log','utf8').split('\n')[0])]:[];
for(const [label,url] of [['before','https://michaelperov.com/preview/living-town-online-v1/'],['after','https://michaelperov.com/preview/living-town-smooth-v1/']]){
 if(process.env.ONLY_AFTER&&label==='before')continue;
 const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2}),p=await context.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.addInitScript(()=>{const original=CanvasRenderingContext2D.prototype.drawImage;window.motionQA={draws:0,noImages:false};CanvasRenderingContext2D.prototype.drawImage=function(...a){motionQA.draws++;if(!motionQA.noImages||!window.townDebug?.ready)return original.apply(this,a)}});
 await p.goto(url);await p.locator('#newTown').click();await p.waitForFunction(()=>window.townDebug?.ready&&!document.querySelector('#nextAction').disabled);await p.evaluate(()=>townDebug.setZoom(1.6));
 const rendering=await p.evaluate(()=>new Promise(resolve=>{const times=[],draws=[];let prev=performance.now(),n=0;motionQA.draws=0;function step(t){if(n++){times.push(t-prev);draws.push(motionQA.draws)}prev=t;motionQA.draws=0;if(n<31)requestAnimationFrame(step);else resolve({median_frame_ms:times.sort((a,b)=>a-b)[Math.floor(times.length/2)],draws_per_frame:draws.reduce((a,b)=>a+b,0)/draws.length})}requestAnimationFrame(step)}));
 // Isolate network pacing from GPU performance, using the real client/server route.
 await p.evaluate(()=>{motionQA.noImages=true;townDebug.route({x:30,y:-16})});
 const samples=await p.evaluate(()=>new Promise(resolve=>{const points=[];const start=performance.now();function frame(t){points.push({t:(t-start)/1000,x:townDebug.player.x,y:townDebug.player.y});if(t-start<8500)requestAnimationFrame(frame);else resolve(points)}requestAnimationFrame(frame)}));
 const speeds=samples.slice(1).map((v,i)=>({t:v.t,speed:Math.hypot(v.x-samples[i].x,v.y-samples[i].y)/(v.t-samples[i].t)})).filter(v=>v.t>2&&Number.isFinite(v.speed)).map(v=>v.speed).sort((a,b)=>a-b);const q=f=>speeds[Math.floor((speeds.length-1)*f)];
 const row={label,...rendering,speed_p10:q(.1),speed_p50:q(.5),speed_p90:q(.9),samples:speeds.length,errors};console.log(JSON.stringify(row));result.push(row);assert.deepEqual(errors,[]);
 if(label==='after'){assert.ok(row.speed_p10>.65,'no regular stops between snapshots');assert.ok(row.speed_p90<1.5,'no catch-up bursts');await p.evaluate(()=>motionQA.noImages=false);await p.screenshot({path:'/projects/work/living-town/art/renders/motion-preview.png'})}
 await context.close();
}
assert.ok(result[1].draws_per_frame<result[0].draws_per_frame/2);assert.ok(result[1].speed_p10>result[0].speed_p10*3);fs.writeFileSync('/projects/work/living-town/art/renders/motion-qa.json',JSON.stringify(result,null,2));console.log('MOTION_AND_RENDER_CULLING_PASS');}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
