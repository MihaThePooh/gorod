const {chromium}=require('/projects/tools/town-browser/node_modules/playwright-core');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage']});try{
 const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2});const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 // Add only a read-only path probe when testing the old published build.
 await page.route('**/game.js',async r=>{const response=await r.fetch();let body=await response.text();if(!body.includes('get destination()'))body=body.replace('window.townDebug={','window.townDebug={get destination(){return path.length?{...path.at(-1)}:null},');await r.fulfill({response,body})});
 await page.goto(process.env.APP_URL||'https://michaelperov.com/preview/living-town-camera-v3/',{waitUntil:'domcontentloaded',timeout:60000});await page.locator('#newTown').click();await page.waitForFunction(()=>window.townDebug?.ready&&townDebug.construction.state.me,null,{timeout:60000});
 await page.evaluate(()=>townDebug.setZoom(1.2));await page.mouse.move(220,530);await page.mouse.down();await page.mouse.move(240,540,{steps:4});await page.mouse.up();
 // Hold the command while real render frames and older SSE snapshots continue.
 let release;await page.route('**/api/route',async r=>{await new Promise(resolve=>release=resolve);await r.continue()});
 const target={x:14,y:-16};const point=await page.evaluate(t=>townDebug.project(t.x,t.y),target);await page.mouse.click(point.x,point.y);
 await page.waitForTimeout(900);const pending=await page.evaluate(()=>townDebug.destination);release();await page.unroute('**/api/route');
 if(process.env.EXPECT_FIXED)assert.ok(pending&&Math.hypot(pending.x-target.x,pending.y-target.y)<.01);else assert.equal(pending,null);
 await page.waitForFunction(()=>townDebug.construction.state.me.moving);
 const next={x:15,y:-16};const q=await page.evaluate(t=>townDebug.project(t.x,t.y),next);await page.mouse.click(q.x,q.y);await page.waitForTimeout(150);
 const retarget=await page.evaluate(()=>townDebug.destination);assert.ok(retarget&&Math.hypot(retarget.x-next.x,retarget.y-next.y)<.01);
 await page.waitForFunction(()=>townDebug.player.state==='idle'&&Math.abs(townDebug.player.x-15)<.02,null,{timeout:15000});
 const arrived=await page.evaluate(()=>townDebug.destination);assert.equal(arrived,null);
 const again={x:13,y:-16};const r=await page.evaluate(t=>townDebug.project(t.x,t.y),again);await page.mouse.click(r.x,r.y);await page.waitForTimeout(150);const restarted=await page.evaluate(()=>townDebug.destination);
 if(process.env.EXPECT_FIXED)assert.ok(restarted&&Math.hypot(restarted.x-again.x,restarted.y-again.y)<.01);
 assert.deepEqual(errors,[]);console.log(JSON.stringify({pending,retarget,arrived,restarted,errors}));await context.close();
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
