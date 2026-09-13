import {decodeMap} from '../sim/map-codec.js';
async function fetchBuffer(url){
 const response=await fetch(url);if(!response.ok)throw new Error(`Map download failed (${response.status})`);
 let buffer=await response.arrayBuffer();
 // Hosts may transparently gunzip .gz files via Content-Encoding. Decode only
 // if the payload still has the gzip signature, preventing double decompression.
 const signature=new Uint8Array(buffer,0,Math.min(2,buffer.byteLength));
 if(signature[0]===0x1f&&signature[1]===0x8b)buffer=await new Response(new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
 return buffer;
}
self.onmessage=async event=>{const {id,kind,url,roadUrl,entries=[]}=event.data;try{
 if(kind==='base'){const [mapBuffer,roadBuffer]=await Promise.all([fetchBuffer(url),fetchBuffer(roadUrl)]);self.postMessage({id,map:decodeMap(mapBuffer),roadBuffer},[roadBuffer]);return;}
 if(kind==='tiles'){const tiles=await Promise.all(entries.map(async entry=>({key:entry.key,buildings:decodeMap(await fetchBuffer(entry.url)).buildings})));self.postMessage({id,tiles});return;}
 throw new Error('Unknown map worker request');
}catch(error){self.postMessage({id,error:error.message});}};
