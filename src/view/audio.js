export class EngineAudio {
  constructor() {
    this.ctx=new (window.AudioContext||window.webkitAudioContext)();const c=this.ctx;
    this.gain=c.createGain();this.gain.gain.value=0;this.gain.connect(c.destination);
    this.osc=c.createOscillator();this.osc.type='sawtooth';
    this.harmonic=c.createOscillator();this.harmonic.type='triangle';
    this.filter=c.createBiquadFilter();this.filter.type='lowpass';
    const shape=c.createWaveShaper();shape.curve=Float32Array.from({length:1024},(_,i)=>Math.tanh((i/511.5-1)*2));
    this.osc.connect(shape);this.harmonic.connect(shape);shape.connect(this.filter).connect(this.gain);
    this.osc.start();this.harmonic.start();
    const buffer=c.createBuffer(1,c.sampleRate*2,c.sampleRate),channel=buffer.getChannelData(0);
    for(let i=0;i<channel.length;i++)channel[i]=Math.random()*2-1;
    this.noise=c.createBufferSource();this.noise.buffer=buffer;this.noise.loop=true;
    this.tires=c.createGain();this.tires.gain.value=0;const tireFilter=c.createBiquadFilter();tireFilter.type='bandpass';tireFilter.frequency.value=1600;tireFilter.Q.value=1.4;
    this.wind=c.createGain();this.wind.gain.value=0;const windFilter=c.createBiquadFilter();windFilter.type='lowpass';windFilter.frequency.value=350;
    this.noise.connect(tireFilter).connect(this.tires).connect(c.destination);this.noise.connect(windFilter).connect(this.wind).connect(c.destination);this.noise.start();this.sirens=new Map();
  }
  update(state,input,active,cops=[]) {
    const c=this.ctx,t=c.currentTime,speed=Math.abs(state.speed),style=state.car?.style;
    const cylinders=style==='motorcycle'?2:style==='scooter'?1:style==='truck'?6:4;
    const gear=Math.min(6,Math.max(1,Math.ceil(speed*3.6/32))),rpm=850+speed/(gear*1.4+1)*420;
    const hz=Math.max(25,rpm/60*cylinders/2);
    this.osc.frequency.setTargetAtTime(hz,t,.07);this.harmonic.frequency.setTargetAtTime(hz*2,t,.07);
    this.filter.frequency.setTargetAtTime(250+Math.abs(input.forward)*1600+speed*9,t,.1);
    this.gain.gain.setTargetAtTime(active?.016+Math.abs(input.forward)*.012:0,t,.08);
    this.tires.gain.setTargetAtTime(active?Math.min(.1,Math.max(0,Math.abs(state.slip||0)-.08)*.18)*Math.min(1,speed/8):0,t,.04);
    this.wind.gain.setTargetAtTime(active?Math.min(.055,speed*speed*.000012):0,t,.2);
    const listener=c.listener;for(const [key,value] of Object.entries({positionX:state.x,positionY:state.y+2,positionZ:state.z,forwardX:Math.sin(state.yaw),forwardY:0,forwardZ:Math.cos(state.yaw),upX:0,upY:1,upZ:0}))listener[key]?.setTargetAtTime(value,t,.03);
    const audible=new Set();for(const cop of cops.slice(0,8)) {
      if(!active)break;audible.add(cop);let s=this.sirens.get(cop);
      if(!s){const osc=c.createOscillator(),gain=c.createGain(),pan=c.createPanner();pan.panningModel='HRTF';pan.distanceModel='inverse';pan.refDistance=8;pan.maxDistance=350;gain.gain.value=.035;osc.type='sine';osc.connect(gain).connect(pan).connect(c.destination);osc.start();s={osc,gain,pan,lastDistance:0};this.sirens.set(cop,s);}
      const distance=Math.hypot(cop.x-state.x,cop.z-state.z),radial=Math.max(-70,Math.min(70,(distance-s.lastDistance)*60));s.lastDistance=distance;
      s.osc.frequency.setTargetAtTime((650+250*Math.sin(state.elapsed*5))*343/(343+radial),t,.08);
      s.pan.positionX.setTargetAtTime(cop.x,t,.03);s.pan.positionY.setTargetAtTime((cop.y||0)+2,t,.03);s.pan.positionZ.setTargetAtTime(cop.z,t,.03);
    }
    for(const [cop,s] of this.sirens)if(!audible.has(cop)){s.osc.stop();s.osc.disconnect();s.gain.disconnect();s.pan.disconnect();this.sirens.delete(cop);}
  }
  hit(speed=15) {const c=this.ctx,o=c.createOscillator(),g=c.createGain();o.type='triangle';o.frequency.setValueAtTime(95,c.currentTime);o.frequency.exponentialRampToValueAtTime(22,c.currentTime+.2);g.gain.setValueAtTime(Math.min(.22,Math.abs(speed)*.008),c.currentTime);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+.22);o.connect(g).connect(c.destination);o.start();o.stop(c.currentTime+.24);o.onended=()=>{o.disconnect();g.disconnect();};}
  mute(){this.update({x:0,y:0,z:0,yaw:0,speed:0},{forward:0},false);}
}
