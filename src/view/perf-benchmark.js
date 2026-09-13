export class RenderBenchmark {
 constructor(){this.started=null;this.samples=[];this.done=false;this.path=[[-700,-400],[-150,-180],[160,-500],[430,-80],[250,550],[-100,850],[-600,530],[-700,-400]];}
 before(time,camera,world,terrain){
  if(this.done)return;if(this.started===null)this.started=time;
  const elapsed=(time-this.started)/1000,segment=Math.min(this.path.length-2,Math.floor(elapsed/20*(this.path.length-1))),u=Math.min(1,elapsed/20*(this.path.length-1)-segment),a=this.path[segment],b=this.path[segment+1],x=a[0]+(b[0]-a[0])*u,z=a[1]+(b[1]-a[1])*u;
  world.update(x,z);const y=terrain.height(x,z);camera.position.set(x,y+24,z+40);camera.lookAt(x,y+7,z-25);
 }
 after(time,renderer,rawFrameMs){
  if(this.done||this.started===null)return;const elapsed=(time-this.started)/1000;
  this.samples.push({ms:rawFrameMs,calls:renderer.info.render.calls,triangles:renderer.info.render.triangles,geometries:renderer.info.memory.geometries,textures:renderer.info.memory.textures});
  if(elapsed<20)return;this.done=true;const sorted=this.samples.map(s=>s.ms).sort((a,b)=>a-b),max=key=>Math.max(...this.samples.map(s=>s[key]));
  const result={durationSeconds:elapsed,frames:this.samples.length,frameP99Ms:sorted[Math.floor(sorted.length*.99)],maxDrawCalls:max('calls'),maxTriangles:max('triangles'),maxGeometries:max('geometries'),maxTextures:max('textures'),heapBytes:performance.memory?.usedJSHeapSize??null,viewport:[innerWidth,innerHeight],pixelRatio:renderer.getPixelRatio(),limitations:['One local Chrome flythrough, not a cross-device qualification','Frame time includes scheduling and is diagnostic; draw calls include renderer passes']};
  const output=document.createElement('pre');output.id='benchmarkResult';output.textContent=JSON.stringify(result,null,2);Object.assign(output.style,{position:'fixed',inset:'100px 20px auto auto',zIndex:100,background:'#10212b',color:'#ffe2ab',padding:'24px',fontSize:'13px',maxWidth:'540px'});document.body.appendChild(output);
  fetch('/__v2_benchmark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(result)}).catch(()=>{});
 }
}
