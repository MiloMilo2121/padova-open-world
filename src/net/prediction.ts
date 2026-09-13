import type { InputFrame, NetEntity, Snapshot } from './protocol.ts';
export type Step = (state: NetEntity, input: InputFrame) => void;
export class Prediction {
  state: NetEntity;
  pending: InputFrame[] = [];
  correction = {x:0,y:0,z:0};
  step: Step;
  constructor(state: NetEntity, step: Step){this.state={...state};this.step=step;}
  advance(input: InputFrame){
    if(this.pending.length>=180)throw new Error('Server acknowledgement timeout');
    this.pending.push(input);this.step(this.state,input);return this.state;
  }
  reconcile(snapshot: Snapshot){
    const old={...this.state};
    this.pending=this.pending.filter(input=>input.seq>snapshot.ack);
    this.state={...snapshot.self};for(const input of this.pending)this.step(this.state,input);
    const dx=old.x-this.state.x,dy=old.y-this.state.y,dz=old.z-this.state.z;
    if(Math.hypot(dx,dy,dz)>.1){this.correction.x+=dx;this.correction.y+=dy;this.correction.z+=dz;}
  }
  visual(dt: number){const factor=Math.exp(-dt/.12);this.correction.x*=factor;this.correction.y*=factor;this.correction.z*=factor;return {...this.state,x:this.state.x+this.correction.x,y:this.state.y+this.correction.y,z:this.state.z+this.correction.z};}
}
export function interpolateEntity(a: NetEntity,b: NetEntity,t: number,seconds: number): NetEntity {
 const u=Math.max(0,Math.min(1,t)),u2=u*u,u3=u2*u;
 const velocity=(e:NetEntity)=>({x:Math.sin(e.yaw)*e.speed+Math.cos(e.yaw)*e.lateral,z:Math.cos(e.yaw)*e.speed-Math.sin(e.yaw)*e.lateral});
 const av=velocity(a),bv=velocity(b),h=(x:number,y:number,v:number,w:number)=>(2*u3-3*u2+1)*x+(u3-2*u2+u)*v*seconds+(-2*u3+3*u2)*y+(u3-u2)*w*seconds;
 return {...b,x:h(a.x,b.x,av.x,bv.x),z:h(a.z,b.z,av.z,bv.z),y:a.y+(b.y-a.y)*u,yaw:a.yaw+Math.atan2(Math.sin(b.yaw-a.yaw),Math.cos(b.yaw-a.yaw))*u};
}
