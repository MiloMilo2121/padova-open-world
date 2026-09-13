import {test} from 'node:test';
import assert from 'node:assert/strict';
import {MapStream,tileKeysAround} from '../src/data/load-map.js';

test('building tile selection is circular, stable and nearest-first',()=>{
 const manifest={size:400,keys:['-2,0','-1,-1','-1,0','0,-1','0,0','1,1','4,4']},keys=tileKeysAround(manifest,-150,-49,500);
 assert.deepEqual(keys,['-1,-1','-1,0','0,-1','0,0','-2,0']);
 assert(!keys.includes('1,1'));assert(!keys.includes('4,4'));
});

test('map stream reuses decoded tiles instead of requesting them twice',async()=>{
 class FakeWorker{constructor(){this.messages=[];this.terminated=false;}postMessage(message){this.messages.push(message);queueMicrotask(()=>{if(message.kind==='base')this.onmessage({data:{id:message.id,map:{buildings:[],buildingTiles:{size:400,keys:['0,0'],count:1}}}});else this.onmessage({data:{id:message.id,tiles:[{key:'0,0',buildings:[{h:4,p:[[0,0],[1,0],[1,1]]}]}]}});});}terminate(){this.terminated=true;}}
 const worker=new FakeWorker(),stream=new MapStream(worker,'http://example.test/game/');await stream.loadBase();const first=await stream.loadAround(0,0,100),second=await stream.loadAround(0,0,100);
 assert.equal(first[0],second[0]);stream.release('0,0');assert.deepEqual(await stream.loadAround(0,0,100),[]);assert.equal(worker.messages.filter(message=>message.kind==='tiles').length,1);assert.match(worker.messages[1].entries[0].url,/\/game\/data\/buildings\/0_0\.bin\.gz$/);stream.close();assert(worker.terminated);
});
