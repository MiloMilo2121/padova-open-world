import {encodeInput,decodeInput,decodeSnapshot,PROTOCOL_VERSION} from './protocol.ts';
import {Prediction,interpolateEntity} from './prediction.ts';
import {advanceCar} from '../sim/player-step.js';
export class MultiplayerClient {
 constructor({terrain,collision,onStatus,onJoin,onLeave}){Object.assign(this,{terrain,collision,onStatus,onJoin,onLeave});this.seq=0;this.snapshots=[];this.connected=false;this.bytes=0;this.lastMessage=0;}
 connect(endpoint,room){
  if(this.socket)this.close();
  const url=new URL(endpoint);if(!['ws:','wss:'].includes(url.protocol))throw new Error('Use ws:// or wss://');if(location.protocol==='https:'&&url.protocol!=='wss:')throw new Error('A secure page requires a wss:// server');
  url.pathname='/play';url.search=new URLSearchParams({room:room.toUpperCase(),v:String(PROTOCOL_VERSION)}).toString();
  this.seq=0;this.snapshots=[];this.prediction=null;this.lastTick=0;this.bytes=0;this.onStatus('Connecting…');
  const socket=this.socket=new WebSocket(url);socket.binaryType='arraybuffer';
  socket.onmessage=event=>{if(this.socket!==socket)return;try{
    this.lastMessage=performance.now();if(typeof event.data==='string'){const message=JSON.parse(event.data);if(message.type!=='welcome'||message.version!==PROTOCOL_VERSION)throw new Error('Protocol mismatch');this.id=message.id;this.room=message.room;return;}
    this.bytes+=event.data.byteLength;const snapshot=decodeSnapshot(new Uint8Array(event.data));if(snapshot.self.id!==this.id)throw new Error('Player identity mismatch');if(snapshot.tick<this.lastTick)return;
    this.lastTick=snapshot.tick;this.receivedAt=performance.now();
    if(!this.prediction){this.prediction=new Prediction(snapshot.self,(state,input)=>advanceCar(state,input,1/60,this.terrain,this.collision));this.connected=true;this.onJoin(snapshot.self);}
    else this.prediction.reconcile(snapshot);
    this.snapshots.push(snapshot);if(this.snapshots.length>40)this.snapshots.shift();this.onStatus(`${this.room} · ${snapshot.entities.length+1}/32 nearby`);
  }catch(error){this.onStatus(error.message);this.close();}};
  socket.onclose=event=>{if(this.socket!==socket)return;this.connected=false;this.socket=null;this.prediction=null;this.onStatus(event.code===1000?'Offline':`Disconnected · ${event.reason||'server unavailable'}`);this.onLeave();};
  socket.onerror=()=>this.onStatus('Cannot reach the multiplayer server');
 }
 step(input){
  if(!this.connected||this.socket.readyState!==WebSocket.OPEN)return null;
  if(performance.now()-this.lastMessage>5000){this.close();return null;}
  const bytes=encodeInput({...input,seq:++this.seq,snapshot:this.lastTick});const frame=decodeInput(bytes);
  if(this.socket.bufferedAmount>65536){this.close();return null;}
  this.socket.send(bytes);try{return this.prediction.advance(frame);}catch(error){this.onStatus(error.message);this.close();return null;}
 }
 remotes(){
  if(!this.snapshots.length)return [];
  const latest=this.snapshots.at(-1),tick=Math.min(latest.tick,this.lastTick-7.5+(performance.now()-this.receivedAt)*.06);
  let a=this.snapshots[0],b=latest;for(const s of this.snapshots){if(s.tick<=tick)a=s;if(s.tick>=tick){b=s;break;}}
  return b.entities.map(entity=>{const before=a.entities.find(e=>e.id===entity.id);return before&&b.tick>a.tick?interpolateEntity(before,entity,(tick-a.tick)/(b.tick-a.tick),(b.tick-a.tick)/60):entity;});
 }
 close(){const socket=this.socket,joined=this.connected;this.socket=null;this.connected=false;this.prediction=null;this.snapshots=[];socket?.close(1000,'Leaving room');this.onStatus('Offline');if(joined)this.onLeave();}
}
