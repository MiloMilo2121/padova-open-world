export function tileKeysAround(manifest,x,z,radius){
 const size=manifest?.size;if(!(size>0)||!Array.isArray(manifest.keys))return [];
 const available=new Set(manifest.keys),pad=Math.SQRT2*size/2,result=[];
 for(let i=Math.floor((x-radius)/size);i<=Math.floor((x+radius)/size);i++)for(let j=Math.floor((z-radius)/size);j<=Math.floor((z+radius)/size);j++){
  const key=i+','+j;if(available.has(key)&&Math.hypot((i+.5)*size-x,(j+.5)*size-z)<=radius+pad)result.push(key);
 }
 return result.sort((a,b)=>{const [ax,az]=a.split(',').map(Number),[bx,bz]=b.split(',').map(Number);return Math.hypot((ax+.5)*size-x,(az+.5)*size-z)-Math.hypot((bx+.5)*size-x,(bz+.5)*size-z);});
}
export class MapStream{
 constructor(worker=null,baseUrl=location.href){this.worker=worker||new Worker(new URL('./map-worker.js',import.meta.url),{type:'module'});this.baseUrl=baseUrl;this.nextId=1;this.requests=new Map();this.cache=new Map();this.loaded=new Set();this.pending=new Map();this.manifest=null;this.worker.onmessage=event=>{const request=this.requests.get(event.data.id);if(!request)return;this.requests.delete(event.data.id);clearTimeout(request.timeout);if(event.data.error)request.reject(new Error(event.data.error));else request.resolve(event.data);};this.worker.onerror=event=>{const error=new Error(event.message||'Map worker failed');for(const request of this.requests.values()){clearTimeout(request.timeout);request.reject(error);}this.requests.clear();};}
 request(message){return new Promise((resolve,reject)=>{const id=this.nextId++,timeout=setTimeout(()=>{this.requests.delete(id);reject(new Error('Map loading timed out'));},60000);this.requests.set(id,{resolve,reject,timeout});this.worker.postMessage({...message,id});});}
 async loadBase(){const {map,roadBuffer}=await this.request({kind:'base',url:new URL('./data/padova-v2.bin.gz',this.baseUrl).href,roadUrl:new URL('./data/road-surfaces-v1.bin.gz',this.baseUrl).href});this.manifest=map.buildingTiles;return {map,roadCache:roadBuffer};}
 async loadAround(x,z,radius){
  const keys=tileKeysAround(this.manifest,x,z,radius),missing=keys.filter(key=>!this.loaded.has(key)&&!this.pending.has(key));
  if(missing.length){const entries=missing.map(key=>{const [i,j]=key.split(',');return {key,url:new URL(`./data/buildings/${i}_${j}.bin.gz`,this.baseUrl).href};}),batch=this.request({kind:'tiles',entries}).then(({tiles})=>{for(const tile of tiles){this.cache.set(tile.key,tile);this.loaded.add(tile.key);}}).finally(()=>{for(const key of missing)this.pending.delete(key);});for(const key of missing)this.pending.set(key,batch);}
  await Promise.all([...new Set(keys.map(key=>this.pending.get(key)).filter(Boolean))]);return keys.map(key=>this.cache.get(key)).filter(Boolean);
 }
 release(keys){for(const key of Array.isArray(keys)?keys:[keys])this.cache.delete(key);}
 close(){this.worker.terminate();for(const request of this.requests.values()){clearTimeout(request.timeout);request.reject(new Error('Map stream closed'));}this.requests.clear();}
}
export async function loadMap(x=-150,z=-49,radius=1100){
 const stream=new MapStream();try{const {map,roadCache}=await stream.loadBase(),tiles=await stream.loadAround(x,z,radius);map.buildings.push(...tiles.flatMap(tile=>tile.buildings));return {map,roadCache,stream,initialTileKeys:tiles.map(tile=>tile.key)};}catch(error){stream.close();throw error;}
}
