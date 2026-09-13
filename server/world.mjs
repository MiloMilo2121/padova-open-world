import {applyMapCorrections} from '../src/sim/map-corrections.js';
import {readFile} from 'node:fs/promises';
import {Terrain} from '../src/sim/terrain.js';
import {applyCityData} from '../src/sim/districts.js';
import {CollisionWorld} from '../src/sim/collision-world.js';
import {makeRoadGraph} from '../src/sim/core.js';
import {safeDryRoad} from '../src/sim/terrain.js';
import {NETWORK_CAR} from '../src/sim/player-step.js';
export async function loadWorld(){
 const [map,grid,city]=await Promise.all(['padova','terrain','city'].map(async name=>JSON.parse(await readFile(new URL(`../dist/data/${name}.json`,import.meta.url),'utf8'))));
 applyCityData(map,city);applyMapCorrections(map);const terrain=new Terrain(grid,map,{modern:true}),world=new CollisionWorld(map,terrain),graph=makeRoadGraph(map.roads,{separateLevels:true});
 const spawns=[];
 for(let n=0;n<32;n++){
  const angle=n*2.399963229728653,radius=n?35+Math.sqrt(n)*12:0;
  const p=safeDryRoad({x:-150+Math.sin(angle)*radius,z:-49+Math.cos(angle)*radius},graph,world.collision,terrain,NETWORK_CAR,q=>spawns.every(s=>Math.hypot(s.x-q.x,s.z-q.z)>8));
  if(!p)throw new Error(`Cannot find safe spawn ${n}`);spawns.push({...p,y:terrain.height(p.x,p.z)});
 }
 return {terrain,collision:world.collision,spawns,graph};
}
