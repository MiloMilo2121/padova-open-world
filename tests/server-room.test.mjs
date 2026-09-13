import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Room} from '../server/room.mjs';
import {SpatialIndex} from '../src/sim/core.js';
import {decodeSnapshot} from '../src/net/protocol.ts';
const world=()=>({terrain:{height:()=>0,waterAt:()=>null},collision:new SpatialIndex(),spawns:Array.from({length:32},(_,i)=>({x:i*10,z:0,y:0,yaw:0}))});
const socket=()=>({packets:[],send(packet){this.packets.push(packet);},getBufferedAmount:()=>0,end(){}});
const input=seq=>({seq,snapshot:0,forward:1,turn:0,brake:false,boost:false});
test('server enforces room capacity, bounded queues and one input per tick',()=>{
 const room=new Room('TEST',world()),players=Array.from({length:32},()=>room.join(socket()));
 assert(players.every(Boolean));assert.equal(room.join(socket()),null);
 const p=players[0];assert(room.input(p,input(1)));assert.equal(room.input(p,input(1)),false);assert.equal(room.input(p,input(602)),false);
 for(let seq=2;seq<=120;seq++)assert(room.input(p,input(seq)));
 assert.equal(p.queue.length,8);room.step();assert.equal(p.ack,113);assert.equal(p.queue.length,7);assert(p.state.speed<1,'packet flood must not fast-forward car');
 room.snapshots();for(const p of players){const packet=p.socket.packets.at(-1);assert(packet.length<=1200);const snap=decodeSnapshot(packet);assert.equal(snap.self.id,p.id);assert.equal(snap.entities.length,31);}
});
test('server stops using held acceleration after missing inputs',()=>{
 const room=new Room('TEST',world()),p=room.join(socket());room.input(p,input(1));room.step();for(let i=0;i<13;i++)room.step();const speed=p.state.speed;for(let i=0;i<120;i++)room.step();assert(p.state.speed<speed);assert.equal(p.ack,1);
});
