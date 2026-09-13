import {createDriveState} from '../src/sim/driving.ts';
import {advanceCar} from '../src/sim/player-step.js';
import {encodeSnapshot,MAX_PLAYERS} from '../src/net/protocol.ts';
import {SpatialIndex} from '../src/sim/core.js';
const neutral=()=>({forward:0,turn:0,brake:false,boost:false});
export class Room {
 constructor(code,world){this.code=code;this.world=world;this.players=new Map();this.tick=0;this.nextId=1;}
 join(socket){
  if(this.players.size>=MAX_PLAYERS)return null;
  const id=this.nextId++;
  if(this.nextId>4095)this.nextId=1;
  if(this.players.has(id))return null;
  const spawn=this.world.spawns.find(s=>[...this.players.values()].every(p=>Math.hypot(p.state.x-s.x,p.state.z-s.z)>7));
  if(!spawn)return null;
  const state={...createDriveState(spawn.x,spawn.z,spawn.yaw),id,y:spawn.y,health:100,wanted:0};
  const player={id,socket,state,queue:[],ack:0,lastSeq:0,lastInput:neutral(),idleTicks:0,spawn,bytes:0};this.players.set(id,player);return player;
 }
 input(player,input){
  // A packet can request one fixed step only. Floods cannot accelerate simulation.
  if(input.seq<=player.lastSeq||input.seq>player.lastSeq+600)return false;
  // Keep recent intent when a server stalls. Dropped input is acknowledged by
  // the next consumed sequence, but never earns extra simulation steps.
  player.lastSeq=input.seq;if(player.queue.length>=8)player.queue.shift();player.queue.push(input);return true;
 }
 step(){
  this.tick++;
  for(const player of this.players.values()){
   const input=player.queue.shift();if(input){player.lastInput=input;player.ack=input.seq;player.idleTicks=0;}else player.idleTicks++;
   const active=player.idleTicks<15?player.lastInput:neutral();
   const result=advanceCar(player.state,player.state.health>0?active:{...neutral(),brake:true},1/60,this.world.terrain,this.world.collision);
   if(result.hitSpeed>4)player.state.health=Math.max(0,player.state.health-(result.hitSpeed-1)*1.2);
   if(result.wet||player.state.health<=0){player.recoverAt??=this.tick+120;if(this.tick>=player.recoverAt){const id=player.id;Object.assign(player.state,createDriveState(player.spawn.x,player.spawn.z,player.spawn.yaw),{id,y:player.spawn.y,health:100,wanted:0});player.recoverAt=null;}}else player.recoverAt=null;
  }
  const list=[...this.players.values()];
  for(let i=0;i<list.length;i++)for(let j=i+1;j<list.length;j++){
   const a=list[i].state,b=list[j].state,dx=b.x-a.x,dz=b.z-a.z,d=Math.hypot(dx,dz);
   if(d<2.1&&Math.abs(a.y-b.y)<2){const impact=Math.abs(a.speed-b.speed);a.health=Math.max(0,a.health-impact*.1);b.health=Math.max(0,b.health-impact*.1);a.speed*=-.15;b.speed*=-.15;a.lateral=b.lateral=0;a.wanted=b.wanted=1;}
  }
 }
 snapshots(){
  const index=new SpatialIndex(250);for(const p of this.players.values())index.add(p.state,p.state.x,p.state.z,p.state.x,p.state.z);
  for(const p of this.players.values()){
   const entities=[...index.near(p.state.x+Math.sin(p.state.yaw)*100,p.state.z+Math.cos(p.state.yaw)*100,625)].filter(e=>e.id!==p.id).sort((a,b)=>Math.hypot(a.x-p.state.x,a.z-p.state.z)-Math.hypot(b.x-p.state.x,b.z-p.state.z)).slice(0,31);
   const packet=encodeSnapshot({tick:this.tick,ack:p.ack,self:p.state,entities});
   if(p.socket.getBufferedAmount()>64*1024){p.socket.end(1013,'Slow connection');continue;}
   p.socket.send(packet,true);p.bytes+=packet.length;
  }
 }
}
