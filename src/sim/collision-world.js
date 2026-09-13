import {SpatialIndex} from './core.js';
import {modernFootprints} from './modern-map.js';
import {PRATO} from './terrain.js';
import {roadStructures} from './road-structures.js';
export class CollisionWorld {
 constructor(data,terrain){
  this.terrain=terrain;if(terrain?.modern)data.buildings=modernFootprints(data.buildings,terrain);
  this.collision=new SpatialIndex(60);this.addBuildings(data.buildings,false);
 if(terrain){
   for(const [x,z,yaw,width] of [[0,130.5,0,11],[0,-130.5,0,11],[85.5,0,Math.PI/2,9],[-85.5,0,Math.PI/2,9]])for(const side of [-1,1]){const px=x+Math.cos(yaw)*(width/2+.2)*side,pz=z-Math.sin(yaw)*(width/2+.2)*side,c=Math.cos(PRATO.yaw),s=Math.sin(PRATO.yaw),wx=PRATO.x+c*px+s*pz,wz=PRATO.z-s*px+c*pz,a=yaw+PRATO.yaw,points=[[-.25,-7],[.25,-7],[.25,7],[-.25,7]].map(([u,v])=>[wx+Math.cos(a)*u+Math.sin(a)*v,wz-Math.sin(a)*u+Math.cos(a)*v]),xs=points.map(p=>p[0]),zs=points.map(p=>p[1]),b={p:points,minX:Math.min(...xs),maxX:Math.max(...xs),minZ:Math.min(...zs),maxZ:Math.max(...zs),minY:terrain.pratoHeight+.3,h:1.2};this.collision.add(b,b.minX,b.minZ,b.maxX,b.maxZ);}
   this.structures=roadStructures(terrain);for(const b of this.structures){this.collision.add(b,b.minX,b.minZ,b.maxX,b.maxZ);}}
 }
 addBuildings(buildings,correct=true){const terrain=this.terrain,resolved=correct&&terrain?.modern?modernFootprints(buildings,terrain):buildings;
  for(const b of resolved){let minX=Infinity,maxX=-Infinity,minZ=Infinity,maxZ=-Infinity;for(const [x,z] of b.p){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minZ=Math.min(minZ,z);maxZ=Math.max(maxZ,z);}b.minX=minX;b.maxX=maxX;b.minZ=minZ;b.maxZ=maxZ;b.cx=(minX+maxX)/2;b.cz=(minZ+maxZ)/2;b.minY=terrain?terrain.elevation(b.cx,b.cz):0;if(terrain?.modern){let bottom=b.minY;for(const p of b.p)bottom=Math.min(bottom,terrain.elevation(...p)-.25);const radius=Math.hypot(maxX-minX,maxZ-minZ)/2+1,nearRoad=terrain.roads.candidates(b.cx,b.cz,radius).length>0,nearWater=terrain.waterDistance(b.cx,b.cz)<=radius+12;if(nearRoad||nearWater)for(const p of b.p)bottom=Math.min(bottom,terrain.groundHeight(...p)-.25);b.h+=b.minY-bottom;b.minY=bottom;}this.collision.add({...b,source:b},minX,minZ,maxX,maxZ);}
  return resolved;
 }
}
