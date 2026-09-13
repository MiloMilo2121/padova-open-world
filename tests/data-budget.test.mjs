import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gzipSync} from 'node:zlib';
import {encodeMap} from '../src/sim/map-codec.js';
import {encodeRoadSurfaceCache} from '../src/sim/road-surface-cache.js';
import {Terrain} from '../src/sim/terrain.js';
import {applyMapCorrections} from '../src/sim/map-corrections.js';
import {applyCityData} from '../src/sim/districts.js';
const budget=JSON.parse(readFileSync(new URL('../docs/perf-budget.json',import.meta.url)));
test('initial streamed map payload fits the versioned download budget',()=>{
 const map=JSON.parse(readFileSync(new URL('../dist/data/padova.json',import.meta.url))),tiles=new Map(),named=[],size=400;
 for(const building of map.buildings){const xs=building.p.map(p=>p[0]),zs=building.p.map(p=>p[1]);if(building.n){named.push(building);continue;}const key=Math.floor((Math.min(...xs)+Math.max(...xs))/2/size)+','+Math.floor((Math.min(...zs)+Math.max(...zs))/2/size);if(!tiles.has(key))tiles.set(key,[]);tiles.get(key).push(building);}
 const base={...map,buildings:named,buildingCount:map.buildings.length,buildingTiles:{size,keys:[...tiles.keys()],count:map.buildings.length-named.length}},baseBytes=gzipSync(encodeMap(base)).length;
 const surfaceMap=JSON.parse(readFileSync(new URL('../dist/data/padova.json',import.meta.url))),city=JSON.parse(readFileSync(new URL('../dist/data/city.json',import.meta.url))),grid=JSON.parse(readFileSync(new URL('../dist/data/terrain.json',import.meta.url)));applyCityData(surfaceMap,city);applyMapCorrections(surfaceMap);const roadBytes=gzipSync(encodeRoadSurfaceCache(surfaceMap,new Terrain(grid,surfaceMap,{modern:true}).roads)).length;
 let tileBytes=0;for(const [key,buildings] of tiles){const [x,z]=key.split(',').map(Number);if(Math.hypot((x+.5)*size+150,(z+.5)*size+49)<=1100+Math.SQRT2*size/2)tileBytes+=gzipSync(encodeMap({buildings})).length;}
 const bytes=baseBytes+roadBytes+tileBytes;assert(bytes<=budget.mapDownloadBytes,`Initial streamed map download ${bytes} exceeds ${budget.mapDownloadBytes}`);
});
