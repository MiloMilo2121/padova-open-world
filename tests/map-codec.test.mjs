import {test} from 'node:test';
import assert from 'node:assert/strict';
import {encodeMap,decodeMap} from '../src/sim/map-codec.js';
test('map codec preserves footprints, topology, names and attributes',()=>{const map={origin:[45.4064,11.8768],buildings:[{p:[[-6020.1,6480.7],[-6015.5,6482.2],[-6016,6486]],h:15.3,n:'Palazzo della Ragione',t:'civic'}],roads:[{p:[[100,120],[101.2,130.6]],w:7,oneway:-1}],license:'ODbL 1.0'};const b=encodeMap(map);assert.deepEqual(decodeMap(b.buffer),map);assert.throws(()=>decodeMap(b.buffer.slice(0,-1)));b[0]=0;assert.throws(()=>decodeMap(b.buffer));});
