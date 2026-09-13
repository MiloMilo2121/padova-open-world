import * as THREE from '../../dist/vendor/three.module.js';
export function compactGlass(root){
 root.updateMatrixWorld(true);const pieces=[];root.traverse(mesh=>{if(mesh.isMesh&&mesh.material.transparent)pieces.push(mesh);});
 if(!pieces.length)return;
 const inverse=root.matrixWorld.clone().invert(),positions=[],normals=[],colors=[],v=new THREE.Vector3(),n=new THREE.Vector3();
 for(const mesh of pieces){const matrix=new THREE.Matrix4().multiplyMatrices(inverse,mesh.matrixWorld),nm=new THREE.Matrix3().getNormalMatrix(matrix),g=mesh.geometry,p=g.attributes.position,no=g.attributes.normal,index=g.index?.array,c=mesh.material.color;
  for(let k=0;k<(index?.length||p.count);k++){const i=index?index[k]:k;v.fromBufferAttribute(p,i).applyMatrix4(matrix);n.fromBufferAttribute(no,i).applyMatrix3(nm).normalize();positions.push(v.x,v.y,v.z);normals.push(n.x,n.y,n.z);colors.push(c.r,c.g,c.b);}mesh.parent.remove(mesh);
 }
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
 const material=new THREE.MeshStandardMaterial({vertexColors:true,transparent:true,opacity:.72,roughness:.2,metalness:.1,depthWrite:false,side:THREE.DoubleSide});root.add(new THREE.Mesh(geometry,material));
}
