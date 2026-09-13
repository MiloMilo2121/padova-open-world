import {decodeMap} from '../sim/map-codec.js';
async function fetchMap(url){
 const response=await fetch(url);if(!response.ok)throw new Error(`Map download failed (${response.status})`);
 let buffer=await response.arrayBuffer();
 // Hosts may transparently gunzip .gz files via Content-Encoding. Decode only
 // if the payload still has the gzip signature, preventing double decompression.
 const signature=new Uint8Array(buffer,0,Math.min(2,buffer.byteLength));
 if(signature[0]===0x1f&&signature[1]===0x8b)buffer=await new Response(new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
 return decodeMap(buffer);
}
self.onmessage=async event=>{const {id,kind,url,entries=[]}=event.data;try{
 if(kind==='base'){self.postMessage({id,map:await fetchMap(url)});return;}
 if(kind==='tiles'){const tiles=await Promise.all(entries.map(async entry=>({key:entry.key,buildings:(await fetchMap(entry.url)).buildings})));self.postMessage({id,tiles});return;}
 throw new Error('Unknown map worker request');
}catch(error){self.postMessage({id,error:error.message});}};
