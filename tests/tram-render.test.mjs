import {test} from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../dist/vendor/three.module.js';
import {Trams,sampleRail} from '../src/view/tram.js';
test('tram carriages begin on their mapped rail and batch static panels',()=>{
 const scene=new THREE.Scene(),map={tracks:[{p:Array.from({length:13},(_,i)=>[100+i*100,200+i*20])}],stops:[]},terrain={roads:{sample:()=>3},height:()=>3};
 const trams=new Trams(scene,map,terrain);assert(trams.vehicles.length>0);
 for(const tram of trams.vehicles)for(let i=0;i<tram.cars.length;i++){
  const car=tram.cars[i],expected=sampleRail(tram.route,tram.d-i*8.65*tram.direction);assert.equal(car.position.x,expected.x);assert.equal(car.position.z,expected.z);assert.equal(car.position.y,3.05);
  assert.equal(car.children.filter(o=>o.isMesh).length,1);assert(car.children[0].geometry.attributes.position.count>100);
 }
 const tram=trams.vehicles[0],before=tram.d;trams.update(1/60,0,{x:100,z:200},[],()=>{});assert.notEqual(tram.d,before);assert.equal(tram.cars.length,2);
});
