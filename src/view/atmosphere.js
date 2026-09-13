import * as THREE from '../../dist/vendor/three.module.js';
export function setupAtmosphere(scene,renderer){
 const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=512;
 const context=canvas.getContext('2d'),sky=context.createLinearGradient(0,0,0,512);
 sky.addColorStop(0,'#245276');sky.addColorStop(.30,'#6e9dae');sky.addColorStop(.47,'#c9c5ae');sky.addColorStop(.52,'#e6cda2');sky.addColorStop(.61,'#928771');sky.addColorStop(1,'#454c49');context.fillStyle=sky;context.fillRect(0,0,1024,512);
 const halo=context.createRadialGradient(710,224,2,710,224,100);halo.addColorStop(0,'rgba(255,239,192,0.9)');halo.addColorStop(.12,'rgba(255,221,156,0.3)');halo.addColorStop(1,'rgba(255,215,146,0)');context.fillStyle=halo;context.fillRect(0,0,1024,512);
 const texture=new THREE.CanvasTexture(canvas);texture.mapping=THREE.EquirectangularReflectionMapping;texture.colorSpace=THREE.SRGBColorSpace;
 scene.background=texture;scene.fog.color.set('#c1c3af');scene.fog.near=180;renderer.toneMappingExposure=1.05;
 return {dispose(){texture.dispose();}};
}
