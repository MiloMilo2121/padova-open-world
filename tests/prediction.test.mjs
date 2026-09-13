import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Prediction,interpolateEntity} from '../src/net/prediction.ts';
import {createDriveState,driveStep} from '../src/sim/driving.ts';
import h from '../src/sim/handling.json' with {type:'json'};
const state=()=>({...createDriveState(),id:1,y:0,health:100,wanted:0});
const step=(s,i)=>driveStep(s,i,h.mito,1/60);
test('prediction replays only unacknowledged inputs under delayed and lost snapshots',()=>{
 const server=state(),client=new Prediction(state(),step),deliveries=[];
 for(let seq=1;seq<=900;seq++){
  const input={seq,snapshot:0,forward:1,turn:Math.sin(seq*.01)*.3,brake:false,boost:false};step(server,input);client.advance(input);
  if(seq%3===0&&seq%15!==0)deliveries.push({at:seq+9,snapshot:{tick:seq,ack:seq,self:{...server},entities:[]}});
  for(const d of deliveries.filter(d=>d.at===seq))client.reconcile(d.snapshot);
  assert(Math.hypot(client.state.x-server.x,client.state.z-server.z)<1e-9);assert(client.pending.length<20);
 }
 client.reconcile({tick:900,ack:900,self:server,entities:[]});assert.equal(client.pending.length,0);
});
test('render correction decays without mutating authoritative collision pose',()=>{const s=state(),p=new Prediction(s,step);p.state.x=2;p.reconcile({tick:1,ack:0,self:s,entities:[]});assert.equal(p.state.x,0);assert(p.visual(1/60).x>1);for(let i=0;i<60;i++)p.visual(1/60);assert(Math.abs(p.visual(0).x)<.001);});
test('Hermite interpolation preserves endpoints and wraps heading at pi',()=>{const a={...state(),yaw:3.1},b={...state(),x:10,yaw:-3.1};assert.equal(interpolateEntity(a,b,0,.05).x,0);assert.equal(interpolateEntity(a,b,1,.05).x,10);assert(Math.abs(interpolateEntity(a,b,.5,.05).yaw-Math.PI)<.001);});
