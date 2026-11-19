import {test} from 'node:test';import assert from 'node:assert/strict';
import {MotionTimeline} from '../client/motion-timeline.js';
function simulate({tick=.05,send=.1,delay=.2,jitter=false}={}){
 const timeline=new MotionTimeline(),speed=1.075,frames=[],motions=[];let old=0,last=0,lastX=0;
 for(let t=0;t<12;t+=send){const clock=Math.round(t/tick)*tick;frames.push({arrival:t+.04+(jitter?Math.sin(t*17)*.012:0),data:{boot:'test',clock:t,motionClock:clock,renderDelay:delay,members:[{id:'a',me:true,x:clock*speed,y:0,direction:2}]}})}
 for(let t=0;t<11;t+=1/60){while(frames.length&&frames[0].arrival<=t){const f=frames.shift();timeline.push(f.data,f.arrival);last=f.data.members[0].x}
  old+=(last-old)*(1-Math.exp(-12/60));const rendered=timeline.sample(t);if(!rendered)continue;const x=rendered[0].x;
  if(t>2)motions.push({buffered:(x-lastX)*60,old:(old-(motions.oldX??old))*60});motions.oldX=old;lastX=x;
 }
 return motions;
}
test('baseline reproduces 400ms catch-up bursts; buffered motion stays at walking speed',()=>{
 const values=simulate({tick:.25,send:.4,delay:.7});const before=values.map(v=>v.old),after=values.map(v=>v.buffered);
 assert.ok(Math.max(...before)/Math.min(...before)>20);
 assert.ok(Math.min(...after)>1.07);assert.ok(Math.max(...after)<1.08);
 console.log(JSON.stringify({baseline_speed_range:[Math.min(...before),Math.max(...before)],buffered_speed_range:[Math.min(...after),Math.max(...after)]}));
});
test('100ms snapshots tolerate arrival jitter without stopping between packets',()=>{
 const speeds=simulate({jitter:true}).map(v=>v.buffered);assert.ok(Math.min(...speeds)>.99);assert.ok(Math.max(...speeds)<1.16);
});
test('no extrapolation through a stop, reset on server restart, bounded snapshot storage',()=>{
 const m=new MotionTimeline();for(let i=0;i<200;i++)m.push({boot:'a',clock:i/10,motionClock:i/10,renderDelay:.2,members:[{id:'a',x:Math.min(i/10,3),y:0}]},i/10);
 assert.ok(m.frames.length<=80);assert.equal(m.sample(20)[0].x,3);assert.equal(m.sample(40)[0].x,3);
 m.push({boot:'b',clock:1,motionClock:1,renderDelay:.2,members:[{id:'a',x:0,y:4}]},41);assert.deepEqual([m.sample(41)[0].x,m.sample(41)[0].y],[0,4]);
});
