import { test } from 'node:test';
import assert from 'node:assert/strict';
import handling from '../src/sim/handling.json' with { type: 'json' };
import { createDriveState, driveStep } from '../src/sim/driving.ts';
const input = (forward=0, turn=0, brake=false) => ({ forward, turn, brake, boost:false });
const step = (s,i,n=60,h=handling.mito) => { for(let k=0;k<n;k++) driveStep(s,i,h,1/60); return s; };
test('acceleration, braking, reverse and stationary steering stay finite for all handling profiles', () => {
  for(const h of Object.values(handling)) {
    const s=createDriveState();step(s,input(0,1),120,h);assert.equal(s.yaw,0);
    step(s,input(1),600,h);assert(s.speed>10 && s.speed<=h.maxSpeed);const speed=s.speed;
    step(s,input(-1),30,h);assert(s.speed<speed);step(s,input(-1),600,h);assert(s.speed<0 && s.speed>=-h.reverseSpeed);
    assert(Object.values(s).every(Number.isFinite));
  }
});
test('rear handbrake grip loss creates greater slip than ordinary cornering', () => {
  const normal=createDriveState(), drift=createDriveState();normal.speed=drift.speed=24;
  let normalSlip=0, driftSlip=0;
  for(let n=0;n<70;n++) {
    driveStep(normal,input(0,.5),handling.mito,1/60);driveStep(drift,input(0,.5,true),handling.mito,1/60);
    normalSlip=Math.max(normalSlip,Math.abs(normal.slip));driftSlip=Math.max(driftSlip,Math.abs(drift.slip));
  }
  assert(driftSlip>normalSlip*1.1, `${driftSlip} vs ${normalSlip}`);
});
test('fixed input replay produces identical pose', () => {
  const a=createDriveState(), b=createDriveState();
  for(let n=0;n<1000;n++) {const i=input(n%300<200?1:-1,Math.sin(n/40)*.4,n%150>120);driveStep(a,i,handling.car,1/60);driveStep(b,i,handling.car,1/60);}
  assert.deepEqual(a,b);assert(Object.values(a).every(Number.isFinite));
});
