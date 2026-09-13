import * as THREE from '../../dist/vendor/three.module.js';
export class DrivingEffects {
 constructor(scene){
  this.capacity=1024;this.cursor=0;this.used=0;this.previous=null;this.positions=new Float32Array(this.capacity*18);this.geometry=new THREE.BufferGeometry();this.geometry.setAttribute('position',new THREE.BufferAttribute(this.positions,3).setUsage(THREE.DynamicDrawUsage));this.geometry.setDrawRange(0,0);
  this.skids=new THREE.Mesh(this.geometry,new THREE.MeshBasicMaterial({color:'#242b28',transparent:true,opacity:.38,depthWrite:false,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:-1}));this.skids.frustumCulled=false;scene.add(this.skids);
  this.particles=Array.from({length:80},()=>({life:0,x:0,y:0,z:0,scale:0}));this.nextParticle=0;this.dummy=new THREE.Object3D();this.smoke=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1,0),new THREE.MeshBasicMaterial({color:'#b7b7aa',transparent:true,opacity:.14,depthWrite:false}),80);this.smoke.frustumCulled=false;scene.add(this.smoke);this.lastEmit=0;
 }
 update(state,dt,terrain,reducedMotion){
  const active=state.mode==='car'&&!state.car?.spec.aircraft&&Math.abs(state.slip||0)>.10&&Math.abs(state.speed)>4;
  if(active){
   const rear=(state.car?.spec.wheelbase||2.5)*.55,half=(state.car?.spec.width||2)*.38;
   const wheels=[-half,half].map(side=>{const x=state.x-Math.sin(state.yaw)*rear+Math.cos(state.yaw)*side,z=state.z-Math.cos(state.yaw)*rear-Math.sin(state.yaw)*side;return {x,z,y:terrain.height(x,z,state.y)+.055};});
   if(this.previous&&Math.hypot(wheels[0].x-this.previous[0].x,wheels[0].z-this.previous[0].z)<3){
    for(let i=0;i<2;i++){const a=this.previous[i],b=wheels[i],dx=b.x-a.x,dz=b.z-a.z,len=Math.hypot(dx,dz);if(len<.03)continue;const nx=-dz/len*.095,nz=dx/len*.095,vertices=[[a.x+nx,a.y,a.z+nz],[b.x+nx,b.y,b.z+nz],[b.x-nx,b.y,b.z-nz],[a.x+nx,a.y,a.z+nz],[b.x-nx,b.y,b.z-nz],[a.x-nx,a.y,a.z-nz]];this.positions.set(vertices.flat(),this.cursor*18);this.cursor=(this.cursor+1)%this.capacity;this.used=Math.min(this.capacity,this.used+1);}
    this.geometry.attributes.position.needsUpdate=true;this.geometry.setDrawRange(0,this.used*6);
   }this.previous=wheels;
   if(!reducedMotion&&state.elapsed-this.lastEmit>.04){this.lastEmit=state.elapsed;const p=this.particles[this.nextParticle++%80];Object.assign(p,{life:1,x:wheels[0].x,y:wheels[0].y+.15,z:wheels[0].z,scale:.2});}
  }else this.previous=null;
  for(let i=0;i<80;i++){const p=this.particles[i];p.life=Math.max(0,p.life-dt*.7);if(p.life){p.y+=dt*.55;p.scale+=dt*.35;}this.dummy.position.set(p.x,p.y,p.z);this.dummy.scale.setScalar(p.life?p.scale*p.life:0);this.dummy.updateMatrix();this.smoke.setMatrixAt(i,this.dummy.matrix);}this.smoke.instanceMatrix.needsUpdate=true;
 }
}
