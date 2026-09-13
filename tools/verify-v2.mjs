import {compactGlass} from '../src/view/compact-glass.js';
import {applyMapCorrections} from '../src/sim/map-corrections.js';
import {MultiplayerClient} from '../src/net/client.js';
import {advanceCar} from '../src/sim/player-step.js';
import * as driving from '../src/sim/driving.ts';
import handling from '../src/sim/handling.json' with {type:'json'};
import {DrivingInput} from '../src/view/input.js';
import {EngineAudio} from '../src/view/audio.js';
import {disposeObject} from '../src/view/dispose.js';
import * as bounds from '../src/sim/bounds.js';
import * as modernVehicles from '../src/view/modern-vehicles.js';
import * as modernDriving from '../src/sim/modern-driving.js';
import * as cameraModule from '../src/sim/camera-rig.js';
import * as districtModule from '../src/sim/districts.js';
import * as trafficModule from '../src/view/traffic.js';
import * as tramModule from '../src/view/tram.js';
import * as incidentModule from '../src/view/incidents.js';
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import * as THREE from '../dist/vendor/three.module.js';
import * as core from '../src/sim/core.js';
import * as worldModule from '../src/view/world.js';
import * as movement from '../src/sim/movement.js';
import * as terrainModule from '../src/sim/terrain.js';
import * as vehicles from '../src/view/vehicles.js';
import {BuildingModels,validateEntry} from '../src/view/building-models.js';
import {inspectGLB} from '../src/sim/model-format.js';
import {GLTFLoader} from '../dist/vendor/GLTFLoader.js';

const wall={p:[[2,-10],[3,-10],[3,10],[2,10]],minX:2,maxX:3,minZ:-10,maxZ:10,h:8};
const index=new core.SpatialIndex();index.add(wall,2,-10,3,10);
const slide=movement.slideMove({x:0,z:0},10,5,.36,index);
assert(slide.x<=1.641 && slide.z>4.9,'must slide along the wall');
assert(!core.collides(slide.x,slide.z,.36,index));
const fast=movement.slideMove({x:0,z:0},100,0,.36,index);
assert(fast.x<2,'must not tunnel through a wall');
const boom=movement.cameraBoom({x:0,y:1.5,z:0},{x:8,y:4,z:0},index);
assert(boom.x<1.71,'camera must stay in front of a wall');
const overhead=movement.cameraBoom({x:0,y:12,z:0},{x:8,y:12,z:0},index);
assert.equal(overhead.x,8,'camera may pass above a roof');
assert(movement.vehicleBlocked(.5,0,Math.PI/2,index),'car nose must collide before its centre');
for(const hz of [30,60,120,144]){
  const clock=new movement.FixedClock();let time=0;
  for(let i=0;i<hz*10;i++)clock.advance(1/hz,dt=>time+=dt);
  assert(Math.abs(time-10)<1e-7,'fixed timestep at '+hz+' Hz');
}
const clock=new movement.FixedClock();let ticks=0;clock.advance(60,()=>ticks++);assert.equal(ticks,8,'tab resume must not trigger an unbounded catch-up');

const html=fs.readFileSync(new URL('../index.html',import.meta.url),'utf8');
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size);
const els=new Map();const context2d=new Proxy({}, {get:(obj,key)=>obj[key]||(()=>{}),set:(obj,key,val)=>(obj[key]=val,true)});
const element=()=>({style:{},dataset:{},hidden:false,open:false,textContent:'',width:440,height:340,getContext:()=>context2d,addEventListener(){},showModal(){this.open=true;},close(){this.open=false;},querySelectorAll:()=>[],appendChild(){}});
ids.forEach(id=>els.set(id,element()));
const document={body:{classList:{add(){},remove(){}}},getElementById(id){assert(els.has(id),'missing DOM id '+id);return els.get(id);},querySelectorAll:()=>[],addEventListener(){},createElement:element};
globalThis.document=document;
const ctx=vm.createContext({THREE,compactGlass,applyMapCorrections,MultiplayerClient,advanceCar,...driving,handling,DrivingInput,EngineAudio,disposeObject,...bounds,...modernVehicles,...modernDriving,...cameraModule,...districtModule,...trafficModule,...tramModule,...incidentModule,...core,...worldModule,...movement,...terrainModule,...vehicles,BuildingModels,document,window:{addEventListener(){},matchMedia(){return {matches:false};}},localStorage:{getItem:()=>null,setItem(){}},console,Math,JSON,Set,Map,Number,Array,Float32Array,Uint8Array,devicePixelRatio:1,innerWidth:1440,innerHeight:900,requestAnimationFrame(){},location:{reload(){}}});
let code=fs.readFileSync(new URL('../src/view/game.js',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replace(/init\(\);\s*$/,'');vm.runInContext(code,ctx);
ctx.testData=JSON.parse(fs.readFileSync(new URL('../dist/data/padova.json',import.meta.url)));
ctx.cityData=JSON.parse(fs.readFileSync(new URL('../dist/data/city.json',import.meta.url)));
ctx.terrainData=JSON.parse(fs.readFileSync(new URL('../dist/data/terrain.json',import.meta.url)));
vm.runInContext(`data=testData;applyCityData(data,cityData);applyMapCorrections(data);districts=new Districts(data);terrain=new Terrain(terrainData,data,{modern:true});terrain.districts=districts;scene=new THREE.Scene();world=new CityWorld(scene,data,terrain);graph=makeRoadGraph(data.roads,{separateLevels:true});signals=new TrafficSignals(graph,data.signals);trams=new Trams(scene,data,terrain);incidents=new Incidents(scene);player=createPerson();camera=new THREE.PerspectiveCamera();sun=new THREE.DirectionalLight();marker=new THREE.Group();state.ready=true;state.started=true;createPopulation();followYaw=state.yaw;cameraRig.reset(state.yaw);`,ctx);
const t=vm.runInContext('({terrain,waterRecovery,recover,dryRoad,addCar,travel,falling,state,keys,cars,people,world,scene,player,camera,clock,movePlayer,updateCamera,updateUI,toggleVehicle,beginMission,cancelMission,updateMission,clearPolice,simulate,placeFeet})',ctx);

// At dense mapped junctions, visible ground must sit below every surface road.
// This coordinate previously produced a 4.6 m terrain bulge over Piazza delle Erbe.
const junction={x:-57.65,z:-57.5},surfaces=t.terrain.roads.candidates(junction.x,junction.z).filter(s=>!s.road.tunnel&&!s.road.crossing);
assert(surfaces.length>1,'expected overlapping mapped streets at terrain regression point');
assert(t.terrain.visualGroundHeight(junction.x,junction.z)<=Math.min(...surfaces.map(s=>s.height))-.049);
const footY=t.terrain.height(junction.x,junction.z);t.placeFeet(t.player,junction.x,footY,junction.z);
const soles=new THREE.Box3().setFromObject(t.player);assert(Math.abs(soles.min.y-footY)<1e-6,'character soles must rest on the simulation surface');

const initial=t.dryRoad({x:-700,z:-400},vehicles.VEHICLES.mito);assert(initial);
for(const car of t.cars)car.mesh.visible=false;
const car=t.addCar(initial.x,initial.z,initial.yaw,false,true,'mito');
Object.assign(t.state,initial,{mode:'car',car,y:car.y,health:100,speed:0,lateral:0,yawRate:0});
t.keys.add('KeyW');
for(let i=0;i<600;i++){
 t.state.elapsed+=1/60;t.movePlayer(1/60);t.updateCamera(1/60);
 assert([t.state.x,t.state.z,t.state.y,t.state.speed,t.state.yaw].every(Number.isFinite));
 assert([t.camera.position.x,t.camera.position.y,t.camera.position.z].every(Number.isFinite));
 if(t.state.health<=0)break;
}
assert(core.dist(initial,t.state)>2,'V2 car must actually move');
// Police resources must be released once, including transparent materials.
let disposed=0;const cop=t.addCar(initial.x+30,initial.z,0,true);
cop.mesh.traverse(o=>{if(o.geometry)o.geometry.addEventListener('dispose',()=>disposed++);});
t.clearPolice();assert(disposed>0);assert.equal(vm.runInContext('cops.length',ctx),0);
console.log('PASS V2 actual controller boots, drives mapped terrain, keeps camera finite and releases police geometry');
