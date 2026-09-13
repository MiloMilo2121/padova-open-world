import * as THREE from '../../dist/vendor/three.module.js';
// Preserve named groups so imported landmarks can still replace their authored proxy.
// Source geometry/materials can be shared by caches: do not dispose those here.
export function batchStatic(root,{spatial=true}={}) {
  root.updateMatrixWorld(true);
  const groups=new Map(),inverse=root.matrixWorld.clone().invert(),p=new THREE.Vector3(),n=new THREE.Vector3();
  root.traverse(object=>{
    let ancestor=object.parent;while(ancestor&&ancestor!==root){if(ancestor.userData.buildingName)return;ancestor=ancestor.parent;}
    if(!object.visible||!object.isMesh||object.isInstancedMesh||Array.isArray(object.material)||object.material.transparent||object.material.map)return;
    const position=object.geometry.attributes.position,normal=object.geometry.attributes.normal;
    if(!position||!normal)return;
    const origin=object.getWorldPosition(new THREE.Vector3()),tile=spatial?Math.floor(origin.x/320)+','+Math.floor(origin.z/320):'local',m=object.material,key=[tile,m.type,m.roughness,m.metalness,m.side,object.castShadow,object.receiveShadow].join(':');
    if(!groups.has(key))groups.set(key,{positions:[],normals:[],colors:[],objects:[],material:object.material,castShadow:object.castShadow,receiveShadow:object.receiveShadow});
    const batch=groups.get(key),matrix=new THREE.Matrix4().multiplyMatrices(inverse,object.matrixWorld),normalMatrix=new THREE.Matrix3().getNormalMatrix(matrix),index=object.geometry.index?.array,colors=object.geometry.attributes.color,color=object.material.color;
    for(let k=0;k<(index?.length||position.count);k++){const i=index?index[k]:k;p.fromBufferAttribute(position,i).applyMatrix4(matrix);n.fromBufferAttribute(normal,i).applyMatrix3(normalMatrix).normalize();batch.positions.push(p.x,p.y,p.z);batch.normals.push(n.x,n.y,n.z);batch.colors.push(color.r*(colors?colors.getX(i):1),color.g*(colors?colors.getY(i):1),color.b*(colors?colors.getZ(i):1));}
    batch.objects.push(object);
  });
  for(const batch of groups.values()){
    if(batch.objects.length<2)continue;
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(batch.positions,3));geometry.setAttribute('normal',new THREE.Float32BufferAttribute(batch.normals,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(batch.colors,3));geometry.computeBoundingSphere();
    const material=batch.material.clone();material.vertexColors=true;material.color.set('#ffffff');const mesh=new THREE.Mesh(geometry,material);mesh.castShadow=batch.castShadow;mesh.receiveShadow=batch.receiveShadow;
    for(const object of batch.objects)object.parent.remove(object);root.add(mesh);
  }
}
