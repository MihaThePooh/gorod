const {chromium}=require('/projects/tools/town-browser/node_modules/playwright-core');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage']});try{
 const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true});
 const page=await context.newPage(),errors=[];let routes=0;page.on('request',r=>{if(new URL(r.url()).pathname.endsWith('/route'))routes++});page.on('pageerror',e=>errors.push(e.message));
 if(process.env.LOCAL)await page.route('**/game.js',r=>r.fulfill({path:'/projects/work/living-town/.online-client-v1/game.js',contentType:'text/javascript'}));
 await page.goto(process.env.APP_URL||'https://michaelperov.com/preview/living-town-camera-v2/',{waitUntil:'domcontentloaded',timeout:60000});await page.locator('#newTown').click();
 await page.waitForFunction(()=>window.townDebug?.ready&&townDebug.construction.state.me,null,{timeout:60000});
 // Exercise the actual DOM handlers. Synthetic pointer IDs cannot acquire native capture.
 await page.evaluate(()=>{const canvas=document.querySelector('#world');const native=canvas.setPointerCapture.bind(canvas);canvas.setPointerCapture=id=>{if(id<100)native(id)}});
 const a={id:101,x:140,y:550},b={id:102,x:260,y:610};
 const send=(type,p)=>page.evaluate(({type,p})=>document.querySelector('#world').dispatchEvent(new PointerEvent(type,{pointerId:p.id,pointerType:'touch',clientX:p.x,clientY:p.y,bubbles:true})),{type,p});
const rows=[];
 for(const release of (process.env.EXPECT_FIXED?['pointerup','pointercancel','lostpointercapture']:['pointerup']))for(const remaining of [101,102]){
  await page.evaluate(()=>townDebug.setZoom(.6));
  const anchor=await page.evaluate(()=>townDebug.unproject(200,580));await send('pointerdown',a);await send('pointerdown',b);
  const moved=[{...a,x:100,y:530},{...b,x:300,y:630}];for(const p of moved)await send('pointermove',p);
  const before=await page.evaluate(()=>({camera:townDebug.camera,point:townDebug.project(12,-16)}));
  const finger=moved.find(p=>p.id===remaining);await send(release,moved.find(p=>p.id!==remaining));
  await send('pointermove',{...finger,x:finger.x+10,y:finger.y+10});
  const after=await page.evaluate(()=>({camera:townDebug.camera,point:townDebug.project(12,-16)}));
  await send('pointerup',{...finger,x:finger.x+10,y:finger.y+10});
  const jump=Math.hypot(after.point.x-before.point.x,after.point.y-before.point.y);
  rows.push({release,remaining,jump,zoomBefore:before.camera.zoom,zoomAfter:after.camera.zoom});
  if(process.env.EXPECT_FIXED){assert.ok(Math.abs(jump-Math.sqrt(200))<1,JSON.stringify(rows));assert.equal(after.camera.zoom,before.camera.zoom);const q=await page.evaluate(p=>townDebug.project(p.x,p.y),anchor);assert.ok(Math.hypot(q.x-210,q.y-590)<1)}
 }
 assert.deepEqual(errors,[]);assert.equal(routes,0);console.log(JSON.stringify({rows,errors}));await context.close();
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
