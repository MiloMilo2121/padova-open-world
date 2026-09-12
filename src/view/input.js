export class DrivingInput {
  constructor(keys) { this.keys=keys;this.turn=0;this.mapping={forward:'KeyW',reverse:'KeyS',left:'KeyA',right:'KeyD',brake:'Space',boost:'ShiftLeft'};try{const saved=JSON.parse(localStorage.getItem('padova-v2-controls')||'{}');for(const action of Object.keys(this.mapping))if(typeof saved[action]==='string'&&/^(Key[A-Z]|Arrow\w+|Space|ShiftLeft|ShiftRight)$/.test(saved[action]))this.mapping[action]=saved[action];}catch{} }
  remap(action,code) { if(!(action in this.mapping)||!code) return;this.mapping[action]=code;localStorage.setItem('padova-v2-controls',JSON.stringify(this.mapping)); }
  sample(dt) {
    const k=this.keys,m=this.mapping,pressed=(a,alternate)=>k.has(m[a])||k.has(alternate);
    const pads=globalThis.navigator?.getGamepads?.()||[],pad=Array.from(pads).find(p=>p?.connected&&p.mapping==='standard');
    const deadzone=v=>Math.abs(v)<.12?0:Math.sign(v)*(Math.abs(v)-.12)/.88;
    const target=(pressed('left','ArrowLeft')?1:0)-(pressed('right','ArrowRight')?1:0);
    this.turn+=Math.max(-dt*3.5,Math.min(dt*3.5,target-this.turn));
    const analog=pad?deadzone(pad.axes[0]||0):0;
    return {forward:pad&&((pad.buttons[7]?.value||0)+(pad.buttons[6]?.value||0)>.05)?(pad.buttons[7]?.value||0)-(pad.buttons[6]?.value||0):(pressed('forward','ArrowUp')?1:0)-(pressed('reverse','ArrowDown')?1:0),turn:analog?-analog:this.turn,brake:k.has(m.brake)||!!pad?.buttons[0]?.pressed,boost:k.has(m.boost)||k.has('ShiftRight')||!!pad?.buttons[1]?.pressed};
  }
  reset(){this.turn=0;}
}
