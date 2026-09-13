import uWS from 'uWebSockets.js';
import {performance} from 'node:perf_hooks';
import {decodeInput,PROTOCOL_VERSION} from '../src/net/protocol.ts';
import {loadWorld} from './world.mjs';
import {Room} from './room.mjs';

export async function startServer({port=Number(process.env.PORT||8787),host=process.env.HOST||'127.0.0.1',world=undefined}={}){
 world??=await loadWorld();
 const rooms=new Map(),allowed=new Set((process.env.ALLOWED_ORIGINS||'http://127.0.0.1:5174,http://localhost:5174,http://127.0.0.1:4173').split(','));
 const metrics={ticks:0,tickMs:[],outBytes:0,players:0};let listener;
 const app=uWS.App().get('/health',(res)=>{res.writeHeader('Content-Type','application/json').end(JSON.stringify({ok:true,protocol:PROTOCOL_VERSION,rooms:rooms.size,players:metrics.players}));})
 .get('/metrics',(res)=>{const values=[...metrics.tickMs].sort((a,b)=>a-b);res.writeHeader('Content-Type','application/json').end(JSON.stringify({ticks:metrics.ticks,players:metrics.players,rooms:rooms.size,tickP99Ms:values[Math.floor(values.length*.99)]||0,tickMaxMs:values.at(-1)||0,outBytes:metrics.outBytes}));})
 .ws('/play',{
  maxPayloadLength:128,idleTimeout:30,maxBackpressure:65536,closeOnBackpressureLimit:true,
  upgrade(res,req,context){
   const origin=req.getHeader('origin'),query=new URLSearchParams(req.getQuery()),code=(query.get('room')||'PADOVA').toUpperCase();
   if(origin&&!allowed.has(origin)){res.writeStatus('403 Forbidden').end();return;}
   if(!/^[A-Z0-9]{3,12}$/.test(code)||Number(query.get('v'))!==PROTOCOL_VERSION){res.writeStatus('400 Bad Request').end();return;}
   if(metrics.players>=128||(!rooms.has(code)&&rooms.size>=16)){res.writeStatus('503 Service Unavailable').end();return;}
   res.upgrade({code,window:performance.now(),messages:0},req.getHeader('sec-websocket-key'),req.getHeader('sec-websocket-protocol'),req.getHeader('sec-websocket-extensions'),context);
  },
  open(ws){const data=ws.getUserData();let room=rooms.get(data.code);if(!room){room=new Room(data.code,world);rooms.set(data.code,room);}const player=room.join(ws);if(!player){ws.end(1013,'Room full');return;}data.room=room;data.player=player;metrics.players++;ws.send(JSON.stringify({type:'welcome',version:PROTOCOL_VERSION,id:player.id,room:data.code,tickRate:60,snapshotRate:20}),false);room.snapshots();},
  message(ws,message,binary){const data=ws.getUserData();if(!data.player)return;const now=performance.now();if(now-data.window>1000){data.window=now;data.messages=0;}if(++data.messages>120){ws.end(1008,'Input rate exceeded');return;}try{if(!binary)throw new Error('Binary input required');const input=decodeInput(new Uint8Array(message));if(!data.room.input(data.player,input))ws.end(1008,'Invalid input sequence');}catch{ws.end(1008,'Invalid input');}},
  close(ws){const data=ws.getUserData();if(data.player){data.room.players.delete(data.player.id);metrics.players--;if(!data.room.players.size)rooms.delete(data.code);}},
 });
 await new Promise((resolve,reject)=>app.listen(host,port,socket=>{if(!socket)reject(new Error(`Cannot listen on ${host}:${port}`));else{listener=socket;resolve();}}));
 let previous=performance.now(),accumulator=0;
 const timer=setInterval(()=>{
  const now=performance.now();accumulator+=Math.min(now-previous,100);previous=now;
  while(accumulator>=1000/60){const start=performance.now();for(const room of rooms.values()){room.step();if(room.tick%3===0)room.snapshots();}metrics.ticks++;metrics.tickMs.push(performance.now()-start);if(metrics.tickMs.length>3600)metrics.tickMs.shift();accumulator-=1000/60;}
  metrics.outBytes=[...rooms.values()].reduce((sum,room)=>sum+[...room.players.values()].reduce((n,p)=>n+p.bytes,0),0);
 },4);
 console.log(`Padova 2 authoritative server http://${host}:${port} · 60 Hz / 20 Hz snapshots`);
 return {rooms,metrics,close(){clearInterval(timer);for(const room of rooms.values())for(const p of room.players.values())p.socket.end(1001,'Server stopping');uWS.us_listen_socket_close(listener);}};
}
if(import.meta.url===new URL(process.argv[1],'file:').href){const server=await startServer();for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{server.close();process.exit(0);});}
