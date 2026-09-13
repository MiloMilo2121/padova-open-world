import * as THREE from '../../dist/vendor/three.module.js';
import {pointInside} from '../sim/core.js';
// Close-range 3D facade relief follows the actual footprint edges. Details are
// procedural interpretations; they are not advertised as a survey of the facade.
export class ArchitectureDetails {
 constructor(scene,collision){this.scene=scene;this.collision=collision;this.key='';this.mesh=null;this.material=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.82,side:THREE.DoubleSide});this.radius=180;}
 update(x,z){
  const key=Math.floor(x/60)+','+Math.floor(z/60);if(key===this.key)return;this.key=key;
  const positions=[],colors=[];const color=new THREE.Color();
  const quad=(a,b,c,d,tint)=>{color.set(tint);for(const p of [a,b,c,a,c,d]){positions.push(...p);colors.push(color.r,color.g,color.b);}};
  const candidates=[...this.collision.near(x,z,this.radius)].filter(b=>b.cx!==undefined&&!(b.source||b).authoredLandmark&&!(b.source||b).modelActive&&b.h>5&&b.h<38&&Math.hypot(b.cx-x,b.cz-z)<this.radius).sort((a,b)=>Math.hypot(a.cx-x,a.cz-z)-Math.hypot(b.cx-x,b.cz-z)).slice(0,48);
  for(const b of candidates){
   if(positions.length>240000)break;
   const historical=Math.hypot(b.cx,b.cz)<1600,base=b.minY;
   for(let i=0;i<b.p.length;i++){
    const a=b.p[i],q=b.p[(i+1)%b.p.length],length=Math.hypot(q[0]-a[0],q[1]-a[1]);if(length<4||length>65)continue;
    const ux=(q[0]-a[0])/length,uz=(q[1]-a[1])/length,side=pointInside((a[0]+q[0])/2-uz*.1,(a[1]+q[1])/2+ux*.1,b.p)?-1:1,nx=-uz*side,nz=ux*side;
    const p=(u,y,depth)=>[a[0]+ux*u+nx*depth,base+y,a[1]+uz*u+nz*depth];
    const panel=(u,v,w,h,depth,tint)=>quad(p(u,v,depth),p(u+w,v,depth),p(u+w,v+h,depth),p(u,v+h,depth),tint);
    // Stone plinth, continuous cornice and real projecting eave catch the sun.
    panel(0,.05,length,.65,.045,'#a19381');panel(0,b.h-.4,length,.22,.1,'#e2cdae');
    quad(p(0,b.h,.02),p(length,b.h,.02),p(length,b.h,.42),p(0,b.h,.42),'#80614c');
    const columns=Math.max(1,Math.floor(length/3.7)),spacing=length/columns,floors=Math.min(7,Math.floor((b.h-1)/3.15));
    for(let floor=0;floor<floors;floor++)for(let col=0;col<columns;col++){
      if(positions.length>240000)break;
      const u=spacing*(col+.5)-.55,v=1.05+floor*3.15,w=1.1,h=1.72;
      if(v+h>b.h-.6)continue;
      panel(u-.12,v-.12,w+.24,h+.24,.07,'#dbc8aa');panel(u,v,w,h,.085,'#233b42');
      const warm=(b.c*13+col*7+floor*3)%11===0;
      panel(u+.06,v+.08,w-.12,h-.16,.09,warm?'#bb9259':'#49646a');
      panel(u+w*.49,v,.045,h,.13,'#b5ad98');panel(u,v+h*.56,w,.045,.13,'#b5ad98');
      // Deep stone sill and lintel give parallax instead of flat painted windows.
      quad(p(u-.17,v-.13,.06),p(u+w+.17,v-.13,.06),p(u+w+.17,v-.13,.32),p(u-.17,v-.13,.32),'#dac9ac');
      panel(u-.17,v-.24,w+.34,.11,.32,'#b6a187');
      if(historical&&col%3!==1){panel(u-.48,v,.32,h,.18,['#46695f','#665c4c','#596557'][b.c%3]);panel(u+w+.16,v,.32,h,.18,['#46695f','#665c4c','#596557'][b.c%3]);}
      if(historical&&floor===1&&(col+b.c)%4===0){
        quad(p(u-.3,v-.28,.1),p(u+w+.3,v-.28,.1),p(u+w+.3,v-.28,.9),p(u-.3,v-.28,.9),'#bba88e');
        panel(u-.3,v+.55,w+.6,.05,.9,'#39413e');for(let bar=0;bar<6;bar++)panel(u-.3+bar*(w+.6)/5,v-.25,.025,.8,.9,'#39413e');
      }
    }
   }
  }
  if(this.mesh){this.scene.remove(this.mesh);this.mesh.geometry.dispose();}
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));geometry.computeVertexNormals();geometry.computeBoundingSphere();this.mesh=new THREE.Mesh(geometry,this.material);this.mesh.castShadow=this.mesh.receiveShadow=true;this.scene.add(this.mesh);
 }
 dispose(){if(this.mesh){this.scene.remove(this.mesh);this.mesh.geometry.dispose();}this.material.dispose();}
}
