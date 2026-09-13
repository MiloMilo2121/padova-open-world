// Measured source topology defect: bridge endpoint is 0.58 m from the continuation
// of the SAME street. Snap only this fingerprint, preserving the live source data.
export function applyMapCorrections(map){
 const bridge=map.roads.find(r=>r.n==='Via Monte Cero'&&r.b&&r.p.some(([x,z])=>Math.hypot(x+4250.3,z-999)<.05));
 const continuation=map.roads.find(r=>r.n==='Via Monte Cero'&&r.k==='track'&&Math.hypot(r.p[0][0]+4250.6,r.p[0][1]-998.5)<.05);
 if(bridge&&continuation){bridge.p[bridge.p.length-1]=[...continuation.p[0]];return ['Via Monte Cero: bridge endpoint joined to its same-street continuation'];}
 return [];
}
