const{chromium}=require('/projects/tools/town-browser/node_modules/playwright-core'),a=require('node:assert/strict');
(async()=>{const b=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage']});try{
 const p=await b.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await p.goto('https://michaelperov.com/preview/living-town-v1/');await p.waitForFunction(()=>window.townDebug?.ready);const z=await p.evaluate(()=>townDebug.camera.zoom);const c=await p.context().newCDPSession(p);
 await c.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:130,y:500,id:1},{x:230,y:500,id:2}]});
 await c.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:80,y:500,id:1},{x:280,y:500,id:2}]});await c.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 a.ok(await p.evaluate(()=>townDebug.camera.zoom)>z+.1,'pinch zoom');
 await p.evaluate(()=>townDebug.setZoom(.3));await p.mouse.wheel(0,2000);await p.waitForTimeout(100);a.equal(await p.evaluate(()=>townDebug.camera.zoom),.3);
 await p.evaluate(()=>townDebug.setZoom(1));await p.mouse.wheel(0,-2000);await p.waitForTimeout(100);a.equal(await p.evaluate(()=>townDebug.camera.zoom),1);
 const start=await p.evaluate(()=>townDebug.player);await p.keyboard.down('d');await p.waitForTimeout(800);await p.keyboard.up('d');const end=await p.evaluate(()=>townDebug.player);a.ok(Math.hypot(start.x-end.x,start.y-end.y)>1);
 await p.mouse.move(200,500);await p.mouse.down();await p.mouse.move(240,550,{steps:4});await p.mouse.up();a.equal(await p.evaluate(()=>townDebug.camera.follow),false);await p.locator('#follow').click();a.equal(await p.evaluate(()=>townDebug.camera.follow),true);
 console.log('PUBLIC_PINCH_WHEEL_LIMITS_KEYBOARD_PAN_FOLLOW_PASS');
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
