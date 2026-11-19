const {chromium}=require('/projects/tools/town-browser/node_modules/playwright-core');
const assert=require('node:assert/strict');
const fs=require('node:fs');

(async()=>{
 const browser=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage']});
 try{
  const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2});
  const page=await context.newPage(),errors=[];
  await page.addInitScript(()=>{
   const Original=EventSource;
   window.EventSource=class extends Original{
    constructor(...args){super(...args);window.cameraTestStream=this}
   };
  });
  page.on('pageerror',error=>errors.push(error.message));
  if(process.env.LOCAL)await page.route('**/living-town-smooth-v1/**',async request=>{
   const name=new URL(request.request().url()).pathname.split('/').pop()||'index.html';
   const path='/projects/work/living-town/.online-client-v1/'+name;
   if((name.endsWith('.js')||name==='index.html')&&fs.existsSync(path)){
    await request.fulfill({path,contentType:name.endsWith('.js')?'text/javascript':'text/html'});
   }else await request.continue();
  });
  await page.goto(process.env.APP_URL||'https://michaelperov.com/preview/living-town-smooth-v1/',{waitUntil:'domcontentloaded',timeout:60000});
  await page.locator('#newTown').click();
  await page.waitForFunction(()=>window.townDebug?.ready&&townDebug.construction.state.me,null,{timeout:60000});
  await page.waitForTimeout(1000);
  await page.evaluate(()=>townDebug.setZoom(1.2));
  await page.mouse.move(200,520);await page.mouse.down();
  await page.mouse.move(255,545,{steps:8});await page.mouse.up();
  const before=await page.evaluate(()=>townDebug.camera);
  assert.equal(before.follow,false);
  // Keep the complete renderer enabled: these are frame intervals, not phone FPS.
  const frames=await page.evaluate(()=>new Promise(resolve=>{
   const samples=[];let last;
   function frame(time){
    if(last)samples.push(time-last);last=time;
    if(samples.length<40)requestAnimationFrame(frame);
    else resolve(samples.sort((a,b)=>a-b));
   }
   requestAnimationFrame(frame);
  }));
  const target=await page.evaluate(()=>({x:townDebug.player.x+2,y:townDebug.player.y}));
  const point=await page.evaluate(t=>townDebug.project(t.x,t.y),target);
  await page.mouse.click(point.x,point.y);
  await page.waitForFunction(t=>Math.hypot(townDebug.player.x-t.x,townDebug.player.y-t.y)<.02&&townDebug.player.state==='idle',target,{timeout:15000});
  const after=await page.evaluate(()=>townDebug.camera);
  if(process.env.EXPECT_FIXED||process.env.LOCAL){
   assert.equal(after.follow,false);assert.equal(after.x,before.x);assert.equal(after.y,before.y);
   await page.setViewportSize({width:390,height:780});
   assert.equal((await page.evaluate(()=>townDebug.camera)).x,before.x);
   // A client-only authoritative correction must also preserve manual camera placement.
   await page.evaluate(()=>{
    const next=townDebug.construction.state;next.revision++;next.me.x+=4;
    cameraTestStream.dispatchEvent(new MessageEvent('message',{data:JSON.stringify(next)}));
   });
   assert.equal((await page.evaluate(()=>townDebug.camera)).x,before.x);
   await page.locator('#follow').click();await page.waitForTimeout(1000);
   assert.equal((await page.evaluate(()=>townDebug.camera)).follow,true);
  }
  assert.deepEqual(errors,[]);
  await page.screenshot({path:'/projects/work/living-town/art/renders/mobile-camera.png'});
  console.log(JSON.stringify({before,after,frameMedian:frames[20],frameP90:frames[36],errors,passed:true}));
  await context.close();
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
