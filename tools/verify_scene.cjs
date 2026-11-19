const {chromium}=require('/projects/tools/town-browser/node_modules/playwright-core');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage']});try{
for(const mobile of [false,true]){
 const page=await browser.newPage({viewport:mobile?{width:390,height:844}:{width:1440,height:1000},deviceScaleFactor:1,isMobile:mobile,hasTouch:mobile});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 await page.goto(process.argv[2]||'http://127.0.0.1:8790/');await page.waitForFunction(()=>window.townDebug?.ready,{timeout:30000});
 await page.waitForTimeout(300);
 const before=await page.evaluate(()=>townDebug.player);
 const pos=await page.evaluate(()=>townDebug.project(-2,-14));
 if(mobile)await page.touchscreen.tap(pos.x,pos.y);else await page.mouse.click(pos.x,pos.y);
 await page.waitForTimeout(1800);
 const after=await page.evaluate(()=>townDebug.player);assert.ok(Math.hypot(after.x-before.x,after.y-before.y)>2,'click/tap moves worker');assert.equal(await page.evaluate(()=>townDebug.blocked),false);
 await page.locator('#hammer').click();await page.waitForTimeout(300);assert.equal(await page.evaluate(()=>townDebug.player.state),'work');
 await page.locator('#hammer').click();
 await page.locator('#plus').click();await page.locator('#minus').click();
 await page.locator('#zoom').evaluate(e=>{e.value='1';e.dispatchEvent(new Event('input'))});assert.equal(await page.evaluate(()=>townDebug.camera.zoom),1);
 await page.locator('#zoom').evaluate(e=>{e.value='0.3';e.dispatchEvent(new Event('input'))});assert.equal(await page.evaluate(()=>townDebug.camera.zoom),.3);
 const reject=await page.evaluate(()=>townDebug.route({x:0,y:0}));assert.equal(reject,false);
 const target={x:22,y:3};assert.equal(await page.evaluate(t=>townDebug.route(t),target),true);
 await page.waitForFunction(t=>Math.hypot(townDebug.player.x-t.x,townDebug.player.y-t.y)<.3,target,{timeout:25000});assert.equal(await page.evaluate(()=>townDebug.blocked),false);
 await page.locator('#follow').click();await page.evaluate(()=>townDebug.setZoom(innerWidth<600?.43:.66));
 await page.waitForTimeout(2500);await page.screenshot({path:`/workspace/living-town-${mobile?'mobile':'desktop'}.png`});
 assert.deepEqual(errors,[]);console.log(JSON.stringify({mobile,ready:true,movement:true,work:true,zoomRange:[.3,1],blockedDestRejected:true,errors}));await page.close();
}}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
