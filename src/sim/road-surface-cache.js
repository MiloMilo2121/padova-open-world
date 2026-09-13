const MAGIC=0x32534452,VERSION=1,HEADER=20,SAMPLE_BYTES=4,SCALE=10000;

// Road geometry already ships in the map base. Persist only the solved height
// and Hermite slope for each deterministic sample, at centimetre/1e-4 precision.
export function encodeRoadSurfaceCache(map,surfaces){
 const samples=[...surfaces.profiles.values()].reduce((sum,profile)=>sum+profile.ids.length,0),size=HEADER+samples*SAMPLE_BYTES,buffer=new ArrayBuffer(size),view=new DataView(buffer);let at=0;
 for(const value of [MAGIC,VERSION,map.roads.length,samples,size]){view.setUint32(at,value,true);at+=4;}
 for(const road of map.roads){const profile=surfaces.profiles.get(road);if(!profile)continue;for(let i=0;i<profile.ids.length;i++){const height=Math.round(surfaces.nodes[profile.ids[i]].h*100),slope=Math.round((profile.slopes?.[i]||0)*SCALE);if(height<-32768||height>32767||slope<-32768||slope>32767)throw new RangeError('Road surface cache value out of range');view.setInt16(at,height,true);view.setInt16(at+2,slope,true);at+=SAMPLE_BYTES;}}
 return new Uint8Array(buffer);
}

export function decodeRoadSurfaceCache(map,buffer){
 const view=new DataView(buffer);if(buffer.byteLength<HEADER||view.getUint32(0,true)!==MAGIC||view.getUint32(4,true)!==VERSION||view.getUint32(8,true)!==map.roads.length)throw new Error('Invalid road surface cache header');const samples=view.getUint32(12,true),size=view.getUint32(16,true);if(size!==buffer.byteLength||size!==HEADER+samples*SAMPLE_BYTES)throw new Error('Invalid road surface cache sizes');const heights=new Int16Array(samples),slopes=new Int16Array(samples);let at=HEADER;for(let i=0;i<samples;i++){heights[i]=view.getInt16(at,true);slopes[i]=view.getInt16(at+2,true);at+=SAMPLE_BYTES;}return {samples,heights,slopes};
}

export function applyRoadSurfaceCache(surfaces,cache){
 let at=0;for(const road of surfaces.map.roads){const profile=surfaces.profiles.get(road);if(!profile)continue;profile.slopes=[];for(let i=0;i<profile.ids.length;i++){if(at>=cache.samples)throw new Error('Truncated road surface cache');surfaces.nodes[profile.ids[i]].h=cache.heights[at]/100;profile.slopes.push(cache.slopes[at]/SCALE);at++;}}
 if(at!==cache.samples)throw new Error('Road surface cache sample mismatch');
}
