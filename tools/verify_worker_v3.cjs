const{chromium}=require('/projects/tools/town-browser/node_modules/playwright-core'),a=require('node:assert/strict');
(async()=>{const b=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage']});try{for(const mobile of (process.argv.includes('--mobile-only')?[true]:[false,true])){
const p=await b.newPage({viewport:mobile?{width:390,height:844}:{width:1280,height:900},isMobile:mobile,hasTouch:mobile});const errors=[];p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
await p.goto(process.argv[2]||'http://127.0.0.1:8790/');await p.waitForFunction(()=>window.townDebug?.ready);
const meta=await p.evaluate(()=>fetch('assets/worker.json').then(r=>r.json()));a.equal(meta.states.walk.count,48);a.equal(meta.columns,30);a.equal(meta.directionRows,2);a.equal(meta.cycleSeconds,2.1);
await p.evaluate(()=>townDebug.route({x:18,y:-16}));await p.waitForTimeout(400);const states=[];for(let i=0;i<18;i++){states.push(await p.evaluate(()=>townDebug.player));await p.waitForTimeout(120)}
a.ok(states.every(s=>s.state==='walk'));a.ok(states.at(-1).walkDistance-states[0].walkDistance>1);
await p.waitForFunction(()=>Math.hypot(townDebug.player.x-18,townDebug.player.y+16)<.12,null,{timeout:22000});a.equal(await p.evaluate(()=>townDebug.blocked),false);
await p.locator('#hammer').click();await p.waitForTimeout(200);a.equal(await p.evaluate(()=>townDebug.player.state),'work');await p.locator('#hammer').click();
a.equal(await p.evaluate(()=>townDebug.route({x:0,y:0})),false);await p.evaluate(()=>townDebug.setZoom(1.6));a.equal(await p.evaluate(()=>townDebug.camera.zoom),1.6);await p.evaluate(()=>townDebug.setZoom(.3));a.equal(await p.evaluate(()=>townDebug.camera.zoom),.3);
a.deepEqual(errors,[]);console.log(JSON.stringify({mobile,newModel:true,walkFrames:48,rowsPerDirection:2,reachesGoal:true,work:true,zoom:[.3,1.6],errors}));await p.close();}
if(!process.argv.includes('--skip-review')){const p=await b.newPage({viewport:{width:1100,height:1000}});const errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto((process.argv[2]||'http://127.0.0.1:8790/')+'walk.html');await p.waitForFunction(()=>window.walkReady);await p.locator('#direction').selectOption('3');await p.locator('#slow').click();await p.screenshot({path:'/workspace/worker-v3-browser-review.png'});a.deepEqual(errors,[]);console.log('COMPARISON_AND_MODEL_REVIEW_PASS')}
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
