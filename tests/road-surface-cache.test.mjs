import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Terrain} from '../src/sim/terrain.js';
import {encodeRoadSurfaceCache} from '../src/sim/road-surface-cache.js';

const grid={version:1,width:3,height:3,x0:-100,z0:-100,step:100,heights:[0,1,2,1,2,3,2,3,4],waterPlane:[0,0,0]};
const source={roads:[{p:[[-30,0],[0,0],[30,0]],w:8,k:'residential'},{p:[[0,-30],[0,0],[0,30]],w:8,k:'residential',layer:1,b:true}],water:[],areas:[]};

test('precomputed road profiles restore sample heights, junctions and crossings',()=>{
 const map=structuredClone(source),baseline=new Terrain(grid,map,{modern:true}),packed=encodeRoadSurfaceCache(map,baseline.roads),restoredMap=structuredClone(map),restored=new Terrain(grid,restoredMap,{modern:true,roadCache:packed.buffer});
 for(const [road] of map.roads.entries())for(const [x,z] of [[-20,0],[0,0],[20,0]])assert(Math.abs(baseline.roads.sample(map.roads[road],x,z)-restored.roads.sample(restoredMap.roads[road],x,z))<.011);
 assert.equal(restored.roads.candidates(0,0).length,2);assert(restoredMap.roads[1].crossing);assert.equal(restored.roads.nodes.length,baseline.roads.nodes.length);
});
