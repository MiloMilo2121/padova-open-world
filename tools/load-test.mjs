import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {performance} from 'node:perf_hooks';
import {encodeInput,decodeSnapshot,PROTOCOL_VERSION} from '../src/net/protocol.ts';
const endpoint=process.env.SERVER_URL||'ws://127.0.0.1:8787';
const count=Number(process.env.BOTS||32),seconds=Number(process.env.SECONDS||20),room=`LOAD${Date.now().toString(36).slice(-7)}`.toUpperCase();
const clients=[];let running=false,timer;const errors=[];
try{
 for(let id=0;id<count;id++){
  const url=new URL('/play',endpoint);url.search=new URLSearchParams({v:PROTOCOL_VERSION,room});
  const client={id,ws:new WebSocket(url),seq:0,tick:0,bytes:0,snapshots:0,ack:0,maxPending:0};clients.push(client);
  client.ws.binaryType='arraybuffer';
  await new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(new Error('Join timeout')),10000);client.ws.onmessage=event=>{try{if(typeof event.data==='string'){const message=JSON.parse(event.data);assert.equal(message.type,'welcome');client.serverId=message.id;clearTimeout(timeout);resolve();}else{const s=decodeSnapshot(new Uint8Array(event.data));assert(Object.values(s.self).every(Number.isFinite));assert(s.self.health>=0);client.tick=s.tick;client.ack=s.ack;client.bytes+=event.data.byteLength;client.snapshots++;client.maxPending=Math.max(client.maxPending,client.seq-s.ack);}}catch(error){errors.push(error.message);reject(error);}};client.ws.onerror=()=>{clearTimeout(timeout);reject(new Error('WebSocket error'));};client.ws.onclose=event=>{if(running)errors.push(`Premature disconnect ${id}: ${event.code} ${event.reason}`);};});
 }
 running=true;const began=performance.now();
 timer=setInterval(()=>{for(const client of clients)if(client.ws.readyState===WebSocket.OPEN)client.ws.send(encodeInput({seq:++client.seq,snapshot:client.tick,forward:1,turn:Math.sin(client.seq*.008+client.id)*.4,brake:client.seq%400>360,boost:false}));},1000/60);
 await new Promise(resolve=>setTimeout(resolve,seconds*1000));
 clearInterval(timer);timer=null;running=false;
 const duration=(performance.now()-began)/1000,metricsURL=new URL('/metrics',endpoint);metricsURL.protocol=metricsURL.protocol==='wss:'?'https:':'http:';
 const metrics=await (await fetch(metricsURL)).json();
 const report={clients:count,seconds:duration,room,transport:'real WebSocket TCP connections',snapshotHz:20,bytesPerSecondPerPlayer:clients.map(c=>Math.round(c.bytes/duration)),minSnapshots:Math.min(...clients.map(c=>c.snapshots)),maxUnacknowledged:Math.max(...clients.map(c=>c.maxPending)),server:metrics,errors,limitations:['Headless test: no GPU/frame-time measurement','Loopback transport: not a public internet or human gameplay trial']};
 await writeFile('docs/multiplayer-load.json',JSON.stringify(report,null,2)+'\n');
 assert.equal(errors.length,0,errors.join('\n'));assert(clients.every(c=>c.snapshots>seconds*12),'missing snapshots');assert(metrics.tickP99Ms<16.67,`Server p99 ${metrics.tickP99Ms} ms exceeds tick budget`);assert(report.maxUnacknowledged<120,'unbounded input backlog');
 console.log(JSON.stringify(report,null,2));console.log('PASS 32-client loopback load gate');
}finally{running=false;if(timer)clearInterval(timer);for(const client of clients)client.ws.close();}
