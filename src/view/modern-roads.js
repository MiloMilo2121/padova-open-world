import {Color} from '../../dist/vendor/three.module.js';

// Centreline sampling keeps both sides at the same cross-section elevation.
// Paint and pavement use exactly the same smooth profile as vehicle physics.
export function buildModernRoads(batch,segments,terrain){
 const colours=new Map(),colour=hex=>{if(!colours.has(hex))colours.set(hex,new Color(hex));return colours.get(hex);};
 const joins=new Set();
 for(const s of segments){
  const road=s.road,ped=/^(pedestrian|footway|path|cycleway|steps)$/.test(road.k),rail=road.k==='tram',urban=!/motorway|trunk|track|path/.test(road.k);
  const dx=s.b[0]-s.a[0],dz=s.b[1]-s.a[1],length=Math.hypot(dx,dz);if(length<.01)continue;
  const nx=-dz/length,nz=dx/length,central=Math.hypot(...s.a)<1550,asphalt=colour(ped?(central?'#bdae91':'#aaa799'):rail?'#8c8980':central?'#535b5b':'#586164');
  const section=(a,b,left,right,offset,c)=>{const h0=a[2]+offset,h1=b[2]+offset;batch.quad([a[0]+nx*left,h0,a[1]+nz*left],[b[0]+nx*left,h1,b[1]+nz*left],[b[0]+nx*right,h1,b[1]+nz*right],[a[0]+nx*right,h0,a[1]+nz*right],c);};
  const junction=(x,z)=>[...terrain.roads.index.near(x,z,12)].some(e=>[e.ia,e.ib].some(id=>{const n=terrain.roads.nodes[id];return n.degree>2&&Math.hypot(x-n.x,z-n.z)<Math.max(6,road.w); }));
  const count=Math.ceil(length/6),samples=Array.from({length:count+1},(_,i)=>{const x=s.a[0]+dx*i/count,z=s.a[1]+dz*i/count;return [x,z,terrain.roads.sample(road,x,z)];});
  for(let i=0;i<count;i++){
   const a=samples[i],b=samples[i+1],mid=[(a[0]+b[0])/2,(a[1]+b[1])/2],atJunction=junction(...mid);
   section(a,b,-road.w/2-.3,road.w/2+.3,.025,colour('#969b95'));
   section(a,b,-road.w/2,road.w/2,.075,asphalt);
   if(!ped&&!rail&&!atJunction){
    for(const side of [-1,1]){
     const edge=side*(road.w/2-.25);section(a,b,edge-.055,edge+.055,.086,colour('#d7d4c2'));
     if(urban&&!road.crossing){const off=side*(road.w/2+.65),x=mid[0]+nx*off,z=mid[1]+nz*off;
      if(!terrain.roads.candidates(x,z).some(c=>c.road!==road)&&terrain.waterDistance(x,z)>1)section(a,b,Math.min(side*road.w/2,side*(road.w/2+1.2)),Math.max(side*road.w/2,side*(road.w/2+1.2)),.13,colour('#b7b5a8'));
     }
    }
    if(road.w>=6.5&&!road.oneway&&Math.floor((i/count*length)/5)%2===0)section(a,b,-.06,.06,.09,colour('#d7d4c2'));
   }
   if(rail)for(const offset of [-.7,.7])section(a,b,offset-.055,offset+.055,.1,colour('#bdc8c9'));
  }
  // Bounded fan fills corner wedges; sample the road rather than a horizontal cap.
  for(const [p,cap] of [[s.a,s.capA],[s.b,s.capB]]){if(!cap)continue;const key=road.surfaceId+':'+p.join(',');if(joins.has(key))continue;joins.add(key);const y=terrain.roads.sample(road,...p)+.077;
   for(let i=0;i<8;i++){const a=i*Math.PI/4,b=(i+1)*Math.PI/4,r=road.w/2,vertex=t=>[p[0]+Math.cos(t)*r,y,p[1]+Math.sin(t)*r];batch.tri([p[0],y,p[1]],vertex(a),vertex(b),asphalt);}
  }
 }
}
