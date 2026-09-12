export interface Handling {
  mass: number; wheelbase: number; frontWeight: number; cgHeight: number;
  grip: number; cornerStiffness: number; steerAngle: number;
  acceleration: number; braking: number; maxSpeed: number; reverseSpeed: number; drag: number;
}
export interface DriveInput { forward: number; turn: number; brake: boolean; boost: boolean }
export interface DriveState {
  x: number; z: number; yaw: number; speed: number;
  lateral: number; yawRate: number; acceleration: number;
  slip: number; pitch: number;
}
export const clamp = (n: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, n));
export function gripCurve(slip: number, stiffness: number) {
  const value = Math.abs(slip) * stiffness;
  return Math.sign(slip) * (value < 1 ? value : value < 2 ? 1 : Math.max(0.65, 1 - (value - 2) * 0.12));
}
export function createDriveState(x = 0, z = 0, yaw = 0): DriveState {
  return { x, z, yaw, speed: 0, lateral: 0, yawRate: 0, acceleration: 0, slip: 0, pitch: 0 };
}
// Bicycle model in local coordinates: +forward follows yaw; +lateral is right.
// Fixed 60 Hz on client and server. Mass cancels in the linear acceleration.
export function driveStep(state: DriveState, raw: DriveInput, h: Handling, dt: number) {
  if (!Number.isFinite(dt) || dt <= 0 || dt > 1 / 30) throw new RangeError('driveStep requires a fixed step <= 1/30');
  const forward = clamp(Number.isFinite(raw.forward) ? raw.forward : 0, -1, 1);
  const turn = clamp(Number.isFinite(raw.turn) ? raw.turn : 0, -1, 1);
  const previous = state.speed;
  const braking = forward * state.speed < -0.5;
  const drive = braking ? forward * h.braking : forward * h.acceleration * (raw.boost ? 1.3 : 1);
  const resistance = state.speed * (0.13 + Math.abs(state.speed) * h.drag);
  state.speed += (drive - resistance - (raw.brake ? Math.sign(state.speed) * h.braking * 0.35 : 0)) * dt;
  if ((!forward || raw.brake || braking) && previous * state.speed < 0) state.speed = 0;
  state.speed = clamp(state.speed, -h.reverseSpeed, h.maxSpeed * (raw.boost ? 1.15 : 1));
  state.acceleration = (state.speed - previous) / dt;
  const frontLoad = clamp(h.frontWeight * 9.81 - h.cgHeight / h.wheelbase * state.acceleration, 1.5, 8.5);
  const rearLoad = 9.81 - frontLoad;
  const frontArm = h.wheelbase * (1 - h.frontWeight), rearArm = h.wheelbase * h.frontWeight;
  const speed = Math.max(2, Math.abs(state.speed));
  const steer = turn * h.steerAngle / (1 + Math.abs(state.speed) * 0.018);
  const frontSlip = Math.atan2(state.lateral + state.yawRate * frontArm, speed) - steer * Math.sign(state.speed);
  const rearSlip = Math.atan2(state.lateral - state.yawRate * rearArm, speed);
  const frontForce = -gripCurve(frontSlip, h.cornerStiffness) * h.grip * frontLoad;
  const rearForce = -gripCurve(rearSlip, h.cornerStiffness) * h.grip * rearLoad * (raw.brake ? 0.35 : 1);
  const inertia = h.wheelbase * h.wheelbase * 0.35;
  state.yawRate += (frontForce * frontArm - rearForce * rearArm) / inertia * dt;
  state.yawRate *= Math.exp(-0.5 * dt);
  state.lateral += (frontForce + rearForce - state.yawRate * state.speed) * dt;
  if (Math.abs(state.speed) < 2) {
    const blend = 1 - Math.exp(-12 * dt);
    state.yawRate += (Math.tan(steer) * state.speed / h.wheelbase - state.yawRate) * blend;
    state.lateral *= Math.exp(-12 * dt);
  }
  state.yaw = Math.atan2(Math.sin(state.yaw + state.yawRate * dt), Math.cos(state.yaw + state.yawRate * dt));
  state.x += (Math.sin(state.yaw) * state.speed + Math.cos(state.yaw) * state.lateral) * dt;
  state.z += (Math.cos(state.yaw) * state.speed - Math.sin(state.yaw) * state.lateral) * dt;
  state.slip = Math.atan2(state.lateral, Math.max(0.5, Math.abs(state.speed)));
  state.pitch += (-state.acceleration * 0.004 - state.pitch) * (1 - Math.exp(-8 * dt));
  return state;
}
