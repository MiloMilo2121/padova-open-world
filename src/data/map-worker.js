import {decodeMap} from '../sim/map-codec.js';
self.onmessage=async event=>{try{
 const response=await fetch(event.data.url);if(!response.ok)throw new Error(`Map download failed (${response.status})`);
 let buffer=await response.arrayBuffer();
 // Hosts may transparently gunzip .gz files via Content-Encoding. Decode only
 // if the payload still has the gzip signature, preventing double decompression.
 const signature=new Uint8Array(buffer,0,Math.min(2,buffer.byteLength));
 if(signature[0]===0x1f&&signature[1]===0x8b)buffer=await new Response(new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
 const map=decodeMap(buffer);self.postMessage({map});
}catch(error){self.postMessage({error:error.message});}};
