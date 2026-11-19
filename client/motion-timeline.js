// Render between authoritative simulation samples. Never advance game logic here.
export class MotionTimeline {
 constructor(){this.reset()}
 reset(){this.frames=[];this.boot=null;this.offset=Infinity;this.delay=.7;this.cursor=-Infinity;this.lastRender=null}
 push(state,now){
  if(this.boot!==state.boot){this.reset();this.boot=state.boot}
  this.offset=Math.min(this.offset,now-state.clock);
  this.delay=state.renderDelay??.7;
  const time=state.motionClock??state.clock,frame={time,members:state.members};
  const last=this.frames.at(-1);
  if(last&&time<last.time)return;
  if(last&&time===last.time)this.frames[this.frames.length-1]=frame;else this.frames.push(frame);
  while(this.frames.length>2&&(this.frames.length>80||time-this.frames[1].time>3))this.frames.shift();
 }
 sample(now){
  if(!this.frames.length)return null;
  const latest=this.frames.at(-1),resumed=this.lastRender!==null&&now-this.lastRender>1;
  let time=Math.min(latest.time,now-this.offset-this.delay);
  if(resumed)time=latest.time;
  time=Math.max(this.cursor,time);this.cursor=time;this.lastRender=now;
  let right=this.frames.findIndex(f=>f.time>=time);if(right<0)right=this.frames.length-1;
  const b=this.frames[right],a=this.frames[Math.max(0,right-1)];
  const mix=b.time>a.time?Math.max(0,Math.min(1,(time-a.time)/(b.time-a.time))):1;
  return b.members.map(p=>{
   const from=a.members.find(q=>q.id===p.id)||p,dx=p.x-from.x,dy=p.y-from.y;
   return {...p,x:from.x+dx*mix,y:from.y+dy*mix,direction:Math.hypot(dx,dy)>.0001?(Math.round(Math.atan2(dx,-dy)/(Math.PI/4))+8)%8:p.direction};
  });
 }
}
