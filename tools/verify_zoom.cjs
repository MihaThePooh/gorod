const{chromium}=require('/projects/tools/town-browser/node_modules/playwright-core'),a=require('node:assert/strict');
(async()=>{const b=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage']});try{for(const width of [390,1440]){
 const p=await b.newPage({viewport:{width,height:width===390?844:1000},isMobile:width===390,hasTouch:width===390});const errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto('https://michaelperov.com/preview/living-town-v2/');await p.waitForFunction(()=>window.townDebug?.ready);
 await p.locator('#zoom').evaluate(e=>{e.value='1.6';e.dispatchEvent(new Event('input'))});a.equal(await p.evaluate(()=>townDebug.camera.zoom),1.6);
 await p.mouse.wheel(0,-3000);await p.waitForTimeout(150);a.equal(await p.evaluate(()=>townDebug.camera.zoom),1.6);
 await p.locator('#zoom').evaluate(e=>{e.value='.3';e.dispatchEvent(new Event('input'))});a.equal(await p.evaluate(()=>townDebug.camera.zoom),.3);
 await p.mouse.wheel(0,3000);await p.waitForTimeout(150);a.equal(await p.evaluate(()=>townDebug.camera.zoom),.3);
 const ratios=await p.evaluate(()=>{townDebug.setZoom(1);const a=townDebug.project(1,0),b=townDebug.project(0,0);townDebug.setZoom(1.6);const c=townDebug.project(1,0),d=townDebug.project(0,0);return Math.hypot(c.x-d.x,c.y-d.y)/Math.hypot(a.x-b.x,a.y-b.y)});a.ok(Math.abs(ratios-1.6)<1e-8);
 if(width===390){await p.evaluate(()=>townDebug.route({x:7.5,y:-7.5}));await p.waitForFunction(()=>Math.hypot(townDebug.player.x-8,townDebug.player.y+7)<.3,{timeout:15000});await p.waitForTimeout(500);await p.screenshot({path:'/workspace/zoom-reference-mobile.png'})}
 a.deepEqual(errors,[]);console.log(JSON.stringify({width,min:.3,max:1.6,uniformWorldScale:ratios,errors}));await p.close()
}}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
