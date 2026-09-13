import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {gzipSync} from 'node:zlib';
import {encodeMap,decodeMap} from '../src/sim/map-codec.js';
const raw=await readFile('dist/data/padova.json'),map=JSON.parse(raw),binary=encodeMap(map),compressed=gzipSync(binary,{level:9});
const decoded=decodeMap(binary.buffer);if(decoded.buildings.length!==map.buildings.length||decoded.roads.length!==map.roads.length)throw new Error('Map conversion lost records');
await mkdir('assets-v2/data',{recursive:true});await writeFile('assets-v2/data/padova-v2.bin.gz',compressed);
await writeFile('docs/data-pipeline.json',JSON.stringify({format:'PDV2 v1 geometry arrays + metadata, gzip transport',sourceBytes:raw.length,binaryBytes:binary.length,downloadBytes:compressed.length,buildings:map.buildings.length,roads:map.roads.length,coordinateResolutionMetres:.1,limitations:['Full map is still decoded at boot; progressive tile loading is not implemented','Road and building metadata remain a compact JSON section']},null,2)+'\n');
console.log(`V2 map: ${compressed.length} bytes downloaded vs ${raw.length} legacy; ${map.buildings.length} footprints`);
