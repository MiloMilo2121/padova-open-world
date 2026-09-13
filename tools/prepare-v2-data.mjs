import {readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import {gzipSync} from 'node:zlib';
import {encodeMap,decodeMap} from '../src/sim/map-codec.js';
import {encodeRoadSurfaceCache} from '../src/sim/road-surface-cache.js';
import {applyMapCorrections} from '../src/sim/map-corrections.js';
import {applyCityData} from '../src/sim/districts.js';
import {Terrain} from '../src/sim/terrain.js';
const TILE_SIZE=400,raw=await readFile('dist/data/padova.json'),map=JSON.parse(raw),named=[],tiles=new Map();
for(const building of map.buildings){
 const xs=building.p.map(p=>p[0]),zs=building.p.map(p=>p[1]);
 if(building.n){named.push(building);continue;}
 const key=Math.floor((Math.min(...xs)+Math.max(...xs))/2/TILE_SIZE)+','+Math.floor((Math.min(...zs)+Math.max(...zs))/2/TILE_SIZE);
 if(!tiles.has(key))tiles.set(key,[]);tiles.get(key).push(building);
}
const keyParts=key=>key.split(',').map(Number),keys=[...tiles.keys()].sort((a,b)=>{const [ax,az]=keyParts(a),[bx,bz]=keyParts(b);return ax-bx||az-bz;}),base={...map,buildings:named,buildingCount:map.buildings.length,buildingTiles:{size:TILE_SIZE,keys,count:map.buildings.length-named.length}},binary=encodeMap(base),compressed=gzipSync(binary,{level:9});
const decoded=decodeMap(binary.buffer);if(decoded.buildings.length!==named.length||decoded.roads.length!==map.roads.length||decoded.buildingTiles.keys.length!==keys.length)throw new Error('Base map conversion lost records');
const directory='assets-v2/data/buildings';await rm(directory,{recursive:true,force:true});await mkdir(directory,{recursive:true});
let tileBinaryBytes=0,tileDownloadBytes=0,tileBuildings=0;
for(let offset=0;offset<keys.length;offset+=32){await Promise.all(keys.slice(offset,offset+32).map(async key=>{const value=encodeMap({buildings:tiles.get(key)}),gzip=gzipSync(value,{level:9}),[x,z]=keyParts(key);tileBinaryBytes+=value.length;tileDownloadBytes+=gzip.length;tileBuildings+=tiles.get(key).length;await writeFile(`${directory}/${x}_${z}.bin.gz`,gzip);}));}
if(tileBuildings+named.length!==map.buildings.length)throw new Error('Building tile conversion lost records');
const [cityRaw,terrainRaw]=await Promise.all([readFile('dist/data/city.json','utf8'),readFile('dist/data/terrain.json','utf8')]),surfaceMap=decodeMap(binary.buffer);applyCityData(surfaceMap,JSON.parse(cityRaw));applyMapCorrections(surfaceMap);const surfaceTerrain=new Terrain(JSON.parse(terrainRaw),surfaceMap,{modern:true}),roadSurface=encodeRoadSurfaceCache(surfaceMap,surfaceTerrain.roads),roadSurfaceGzip=gzipSync(roadSurface,{level:9});
await mkdir('assets-v2/data',{recursive:true});await writeFile('assets-v2/data/padova-v2.bin.gz',compressed);await writeFile('assets-v2/data/road-surfaces-v1.bin.gz',roadSurfaceGzip);
await writeFile('docs/data-pipeline.json',JSON.stringify({format:'PDV2 v1 base + precomputed road profiles + 400 m building tiles, gzip transport',sourceBytes:raw.length,baseBinaryBytes:binary.length,baseDownloadBytes:compressed.length,roadSurfaceBinaryBytes:roadSurface.length,roadSurfaceDownloadBytes:roadSurfaceGzip.length,buildingTileBinaryBytes:tileBinaryBytes,buildingTileDownloadBytes:tileDownloadBytes,buildingTiles:keys.length,buildings:map.buildings.length,namedBuildingsInBase:named.length,roads:map.roads.length,coordinateResolutionMetres:.1,limitations:['Road topology remains global simulation data','Integrated building geometry and collision records stay resident after first use','Tile payloads still use structured-clone objects rather than zero-copy GPU buffers']},null,2)+'\n');
console.log(`V2 map: ${compressed.length} byte base + ${roadSurfaceGzip.length} byte road cache + ${keys.length} streamed building tiles vs ${raw.length} byte legacy; ${map.buildings.length} footprints`);
