const MAGIC=0x32564450,VERSION=1;
const encoder=new TextEncoder(),decoder=new TextDecoder();
// Geometry uses 0.1 m integer deltas around each footprint's local origin.
// Exact for the source map's decimetre precision; no float JSON coordinate parsing.
export function encodeMap(map){
 const shapes=[];
 const json=JSON.stringify(map,(key,value)=>{
  if(key==='p'&&Array.isArray(value)&&value.length&&Array.isArray(value[0])){const id=shapes.length;shapes.push(value);return {$shape:id};}
  return value;
 });
 const metadata=encoder.encode(json);let size=20+metadata.length;
 for(const shape of shapes)size+=12+shape.length*8;
 const bytes=new Uint8Array(size),view=new DataView(bytes.buffer);view.setUint32(0,MAGIC,true);view.setUint32(4,VERSION,true);view.setUint32(8,metadata.length,true);view.setUint32(12,shapes.length,true);view.setUint32(16,size,true);bytes.set(metadata,20);let at=20+metadata.length;
 for(const shape of shapes){
  view.setUint32(at,shape.length,true);const ox=Math.round(shape[0][0]*10),oz=Math.round(shape[0][1]*10);view.setInt32(at+4,ox,true);view.setInt32(at+8,oz,true);at+=12;
  for(const [x,z] of shape){if(!Number.isFinite(x)||!Number.isFinite(z)||Math.abs(x)>1000000||Math.abs(z)>1000000)throw new RangeError('Map coordinates out of range');view.setInt32(at,Math.round(x*10)-ox,true);view.setInt32(at+4,Math.round(z*10)-oz,true);at+=8;}
 }
 return bytes;
}
export function decodeMap(buffer){
 const view=new DataView(buffer);if(buffer.byteLength<20||view.getUint32(0,true)!==MAGIC||view.getUint32(4,true)!==VERSION||view.getUint32(16,true)!==buffer.byteLength)throw new Error('Invalid Padova map header');
 const length=view.getUint32(8,true),count=view.getUint32(12,true);if(length>buffer.byteLength-20||count>1000000)throw new Error('Invalid map section sizes');
 let at=20+length;const shapes=[];
 for(let i=0;i<count;i++){
  if(at+12>buffer.byteLength)throw new Error('Truncated map shape');const n=view.getUint32(at,true),ox=view.getInt32(at+4,true),oz=view.getInt32(at+8,true);at+=12;
  if(n>100000||at+n*8>buffer.byteLength)throw new Error('Invalid map polygon');const points=[];for(let j=0;j<n;j++){points.push([(ox+view.getInt32(at,true))/10,(oz+view.getInt32(at+4,true))/10]);at+=8;}shapes.push(points);
 }
 if(at!==buffer.byteLength)throw new Error('Trailing map bytes');
 return JSON.parse(decoder.decode(new Uint8Array(buffer,20,length)),(key,value)=>{if(key==='p'&&value&&typeof value.$shape==='number'){if(!Number.isInteger(value.$shape)||!shapes[value.$shape])throw new Error('Invalid shape reference');return shapes[value.$shape];}return value;});
}
