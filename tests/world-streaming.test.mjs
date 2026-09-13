import {test} from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../dist/vendor/three.module.js';
const context=new Proxy({}, {get:(object,key)=>object[key]||(()=>{}),set:(object,key,value)=>(object[key]=value,true)});
globalThis.document={createElement:()=>({width:0,height:0,getContext:()=>context})};
const {CHUNK,CityWorld}=await import('../src/view/world.js');

test('world builds nearby chunks progressively and keeps distant chunks out of the queue',()=>{
 const scene=new THREE.Scene(),world=new CityWorld(scene,{buildings:[],roads:[],water:[],areas:[]});
 world.radius=600;
 for(let i=-4;i<=4;i++)for(let j=-4;j<=4;j++)world.chunk(i*CHUNK,j*CHUNK);
 const built=[];world.build=key=>{built.push(key);world.loaded.set(key,new THREE.Group());};
 world.update(0,0,true);
 assert.equal(built.length,2,'an initial or teleport update must not build the old twelve-chunk burst');
 assert(world.queue.length>0,'nearby chunks should remain queued for streaming');
 assert([...world.queue,...built].every(key=>{
  const chunk=world.chunks.get(key);
  return Math.hypot((chunk.i+.5)*CHUNK,(chunk.j+.5)*CHUNK)<=world.radius+CHUNK*.72;
 }),'the stream queue must exclude chunks outside the circular view radius');
 world.nextBuildAt=Infinity;world.update(0,0);assert.equal(built.length,2,'streaming must yield between chunk builds');
 world.nextBuildAt=0;world.update(0,0);assert.equal(built.length,3,'the next budgeted update should build one chunk');
 world.architecture.dispose();
});
