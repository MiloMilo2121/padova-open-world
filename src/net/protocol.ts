import type { DriveInput, DriveState } from '../sim/driving.ts';
export const PROTOCOL_VERSION = 2;
export const MAX_PLAYERS = 32;
export const MAX_PACKET_BYTES = 1200;
export class BitWriter {
  bytes: Uint8Array; offset = 0;
  constructor(size = MAX_PACKET_BYTES) { this.bytes = new Uint8Array(size); }
  write(value: number, bits: number) {
    if (!Number.isInteger(value) || value < 0 || value >= 2 ** bits || this.offset + bits > this.bytes.length * 8) throw new RangeError('Invalid bit field');
    for (let i = 0; i < bits; i++, this.offset++) if (Math.floor(value / 2 ** i) % 2) this.bytes[this.offset >> 3] |= 1 << (this.offset & 7);
  }
  finish() { return this.bytes.slice(0, Math.ceil(this.offset / 8)); }
}
export class BitReader {
  bytes: Uint8Array; offset = 0;
  constructor(bytes: Uint8Array) { this.bytes = bytes; }
  read(bits: number) {
    if (this.offset + bits > this.bytes.length * 8) throw new RangeError('Truncated packet');
    let value = 0;
    for (let i = 0; i < bits; i++, this.offset++) value += ((this.bytes[this.offset >> 3] >> (this.offset & 7)) & 1) * 2 ** i;
    return value;
  }
}
const quantize = (v: number, min: number, max: number, bits: number) => {
  if (!Number.isFinite(v)) throw new RangeError('Nonfinite state');
  return Math.round((Math.min(max, Math.max(min, v)) - min) / (max - min) * (2 ** bits - 1));
};
const unquantize = (v: number, min: number, max: number, bits: number) => min + v / (2 ** bits - 1) * (max - min);
export interface InputFrame extends DriveInput { seq: number; snapshot: number }
export function encodeInput(input: InputFrame) {
  const w = new BitWriter(12);
  w.write(1, 8); w.write(input.seq >>> 0, 32); w.write(input.snapshot >>> 0, 32);
  w.write(quantize(input.forward, -1, 1, 8), 8); w.write(quantize(input.turn, -1, 1, 8), 8);
  w.write((input.brake ? 1 : 0) | (input.boost ? 2 : 0), 8); return w.finish();
}
export function decodeInput(bytes: Uint8Array): InputFrame {
  if (bytes.length !== 12) throw new RangeError('Input size');
  const r = new BitReader(bytes); if (r.read(8) !== 1) throw new RangeError('Input type');
  const seq = r.read(32), snapshot = r.read(32), forward = unquantize(r.read(8), -1, 1, 8), turn = unquantize(r.read(8), -1, 1, 8), flags = r.read(8);
  if (flags > 3) throw new RangeError('Input flags');
  return { seq, snapshot, forward: Math.abs(forward)<.005?0:forward, turn: Math.abs(turn)<.005?0:turn, brake: !!(flags & 1), boost: !!(flags & 2) };
}
export interface NetEntity extends DriveState { id: number; y: number; health: number; wanted: number }
export interface Snapshot { tick: number; ack: number; self: NetEntity; entities: NetEntity[] }
const floatFields = ['x','z','yaw','speed','lateral','yawRate','acceleration','slip','pitch','y','health','wanted'] as const;
export function encodeSnapshot(s: Snapshot) {
  if(s.entities.length>MAX_PLAYERS-1)throw new RangeError('Entity count');
  const w=new BitWriter();w.write(2,8);w.write(PROTOCOL_VERSION,8);w.write(s.tick>>>0,32);w.write(s.ack>>>0,32);w.write(s.self.id,12);w.write(s.entities.length,6);w.write(0,2);
  // Full precision authoritative self state prevents quantization from spoiling replay.
  const floats=new DataView(new ArrayBuffer(floatFields.length*4));
  floatFields.forEach((key,i)=>{if(!Number.isFinite(s.self[key]))throw new RangeError('Nonfinite self');floats.setFloat32(i*4,s.self[key],true);});
  for(const b of new Uint8Array(floats.buffer))w.write(b,8);
  for(const e of s.entities){
    w.write(e.id,12);w.write(quantize(e.x,-8192,8192,19),19);w.write(quantize(e.z,-8192,8192,19),19);
    w.write(quantize(e.y,-64,448,14),14);w.write(quantize(Math.atan2(Math.sin(e.yaw),Math.cos(e.yaw)),-Math.PI,Math.PI,12),12);
    w.write(quantize(e.speed,-32,128,12),12);w.write(quantize(e.lateral,-64,64,12),12);w.write(Math.round(Math.max(0,Math.min(100,e.health))),7);w.write(e.wanted,3);
  }
  return w.finish();
}
export function decodeSnapshot(bytes: Uint8Array): Snapshot {
  if(bytes.length>MAX_PACKET_BYTES)throw new RangeError('Snapshot size');
  const r=new BitReader(bytes);if(r.read(8)!==2||r.read(8)!==PROTOCOL_VERSION)throw new RangeError('Protocol mismatch');
  const tick=r.read(32),ack=r.read(32),id=r.read(12),count=r.read(6);if(count>31||r.read(2)!==0)throw new RangeError('Snapshot header');
  const raw=new Uint8Array(floatFields.length*4);for(let i=0;i<raw.length;i++)raw[i]=r.read(8);const floats=new DataView(raw.buffer);
  const self={id} as NetEntity;floatFields.forEach((key,i)=>{self[key]=floats.getFloat32(i*4,true);if(!Number.isFinite(self[key]))throw new RangeError('Nonfinite self');});
  const entities:NetEntity[]=[];const ids=new Set([id]);
  for(let i=0;i<count;i++){
    const entityId=r.read(12);if(ids.has(entityId))throw new RangeError('Duplicate entity');ids.add(entityId);
    entities.push({id:entityId,x:unquantize(r.read(19),-8192,8192,19),z:unquantize(r.read(19),-8192,8192,19),y:unquantize(r.read(14),-64,448,14),yaw:unquantize(r.read(12),-Math.PI,Math.PI,12),speed:unquantize(r.read(12),-32,128,12),lateral:unquantize(r.read(12),-64,64,12),health:r.read(7),wanted:r.read(3),yawRate:0,acceleration:0,slip:0,pitch:0});
  }
  if(Math.ceil(r.offset/8)!==bytes.length)throw new RangeError('Trailing snapshot data');
  return {tick,ack,self,entities};
}
