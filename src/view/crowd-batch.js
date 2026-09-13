import * as THREE from '../../dist/vendor/three.module.js';
// Logical skeletons remain available to AI/animation; matching geometry is rendered
// in a small number of instanced draws, with per-instance clothing/skin colours.
export class CrowdBatch {
 constructor(scene,actors){
  this.groups=[];this.zero=new THREE.Matrix4().makeScale(0,0,0);const groups=new Map();
  for(const actor of actors)actor.mesh.traverse(part=>{
    if(!part.isMesh||Array.isArray(part.material)||part.material.transparent)return;
    const key=part.geometry.uuid;if(!groups.has(key))groups.set(key,{geometry:part.geometry,entries:[]});groups.get(key).entries.push({actor,part});part.visible=false;
  });
  for(const group of groups.values()){
    const material=new THREE.MeshStandardMaterial({roughness:.85}),mesh=new THREE.InstancedMesh(group.geometry,material,group.entries.length);mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);mesh.castShadow=mesh.receiveShadow=true;mesh.frustumCulled=false;
    group.entries.forEach(({part},i)=>mesh.setColorAt(i,part.material.color));mesh.instanceColor.needsUpdate=true;scene.add(mesh);this.groups.push({...group,mesh});
  }
  this.actors=actors;
 }
 update(){for(const actor of this.actors)if(actor.mesh.visible)actor.mesh.updateMatrixWorld(true);for(const {entries,mesh} of this.groups){entries.forEach(({actor,part},i)=>mesh.setMatrixAt(i,actor.mesh.visible?part.matrixWorld:this.zero));mesh.instanceMatrix.needsUpdate=true;}}
 dispose(scene){for(const {entries,mesh} of this.groups){scene.remove(mesh);mesh.dispose();mesh.material.dispose();for(const {part} of entries)part.visible=true;}}
}
