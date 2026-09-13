import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gzipSync} from 'node:zlib';
import {encodeMap} from '../src/sim/map-codec.js';
const budget=JSON.parse(readFileSync(new URL('../docs/perf-budget.json',import.meta.url)));
test('current map payload fits the versioned download budget',()=>{
 const map=JSON.parse(readFileSync(new URL('../dist/data/padova.json',import.meta.url)));
 const bytes=gzipSync(encodeMap(map)).length;
 assert(bytes<=budget.mapDownloadBytes,`Map download ${bytes} exceeds ${budget.mapDownloadBytes}`);
});
