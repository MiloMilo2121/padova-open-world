import {driveStep,createDriveState} from './driving.ts';
import handling from './handling.json' with {type:'json'};
import {vehicleBlocked} from './movement.js';
import {PLAY_BOUNDS} from './bounds.js';
export const NETWORK_CAR=Object.freeze({width:2,length:4.08,height:1.46,wheelbase:2.51,accel:10.2,brake:20,max:39,boost:48,reverse:8});
export function advanceCar(actor,input,dt,terrain,collision,spec=NETWORK_CAR,style='mito') {
  const h={...(handling[style]||handling.car),wheelbase:spec.wheelbase,acceleration:spec.accel,braking:spec.brake,maxSpeed:spec.max,reverseSpeed:spec.reverse};
  const motion={...createDriveState(actor.x,actor.z,actor.yaw),speed:actor.speed,lateral:actor.lateral||0,yawRate:actor.yawRate||0,pitch:actor.pitch||0};
  driveStep(motion,input,h,dt);
  actor.speed=motion.speed;actor.lateral=motion.lateral;actor.slip=motion.slip;actor.pitch=motion.pitch;actor.yawRate=motion.yawRate;actor.acceleration=motion.acceleration;
  if(!vehicleBlocked(actor.x,actor.z,motion.yaw,collision,spec,actor.y))actor.yaw=motion.yaw;
  else{actor.yawRate=0;actor.lateral=0;}
  const steps=Math.max(1,Math.ceil(Math.hypot(actor.speed,actor.lateral)*dt/.5)),step=dt/steps;
  let hitSpeed=0,wet=false;
  for(let i=0;i<steps;i++){
    const x=actor.x+(Math.sin(actor.yaw)*actor.speed+Math.cos(actor.yaw)*actor.lateral)*step;
    const z=actor.z+(Math.cos(actor.yaw)*actor.speed-Math.sin(actor.yaw)*actor.lateral)*step;
    if(x<PLAY_BOUNDS.minX||x>PLAY_BOUNDS.maxX||z<PLAY_BOUNDS.minZ||z>PLAY_BOUNDS.maxZ||vehicleBlocked(x,z,actor.yaw,collision,spec,actor.y)){
      hitSpeed=Math.abs(actor.speed);actor.speed*=-.15;actor.lateral=0;actor.yawRate=0;break;
    }
    actor.x=x;actor.z=z;actor.y=terrain.height(x,z,actor.y);
    if(terrain.waterAt(x,z,0,actor.y)!==null){wet=true;break;}
  }
  return {hitSpeed,wet};
}
