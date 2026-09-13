export function loadMap(){
 return new Promise((resolve,reject)=>{
  const worker=new Worker(new URL('./map-worker.js',import.meta.url),{type:'module'}),timeout=setTimeout(()=>{worker.terminate();reject(new Error('Map loading timed out'));},60000);
  const finish=()=>{clearTimeout(timeout);worker.terminate();};
  worker.onmessage=event=>{finish();if(event.data.error)reject(new Error(event.data.error));else resolve(event.data.map);};
  worker.onerror=event=>{finish();reject(new Error(event.message||'Map worker failed'));};
  worker.postMessage({url:new URL('./data/padova-v2.bin.gz',location.href).href});
 });
}
