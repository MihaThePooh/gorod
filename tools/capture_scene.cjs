const{chromium}=require('/projects/tools/town-browser/node_modules/playwright-core');
(async()=>{const b=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage']});try{
for(const mobile of [false,true]){const p=await b.newPage({viewport:mobile?{width:390,height:844}:{width:1440,height:1000},deviceScaleFactor:1,isMobile:mobile,hasTouch:mobile});await p.goto('https://michaelperov.com/preview/living-town-v1/');await p.waitForFunction(()=>window.townDebug?.ready);await p.waitForTimeout(700);await p.screenshot({path:`/workspace/town-initial-${mobile?'mobile':'desktop'}.png`});await p.close()}
const p=await b.newPage({viewport:{width:960,height:720}});await p.goto('https://michaelperov.com/preview/living-town-v1/');await p.waitForFunction(()=>window.townDebug?.ready);await p.locator('#hammer').click();await p.waitForTimeout(300);await p.screenshot({path:'/workspace/town-work.png'});await p.close()
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
