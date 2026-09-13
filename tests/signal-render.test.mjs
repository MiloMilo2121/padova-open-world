import {test} from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../dist/vendor/three.module.js';
import {TrafficSignals} from '../src/view/traffic.js';
test('signal batches preserve phase colours and release instance buffers on rebuild',()=>{
 const signals=new TrafficSignals({segments:[],nodes:[]}),scene=new THREE.Scene(),terrain={height:()=>0,roads:{sample:()=>0,candidates:()=>[]}},road={w:8};
 signals.junctions.set(1,{id:1,x:0,z:0,offset:0,radius:6,approaches:[{yaw:0,road},{yaw:Math.PI/2,road}]});signals.update(scene,terrain,0,0,0);
 let visible=0;signals.group.traverseVisible(o=>{if(o.isMesh)visible++;});assert.equal(visible,3);assert.equal(signals.lightBatch.count,6);
 const color=new THREE.Color();signals.lightBatch.getColorAt(2,color);assert.equal(color.getHexString(),'5cff8a');signals.lightBatch.getColorAt(3,color);assert.equal(color.getHexString(),'ff4234');
 signals.update(scene,terrain,0,0,13);signals.lightBatch.getColorAt(1,color);assert.equal(color.getHexString(),'ffc547');
 let disposed=false;signals.lightBatch.addEventListener('dispose',()=>disposed=true);signals.update(scene,terrain,800,800,13);assert(disposed);assert.equal(signals.lightBatch,null);
});
