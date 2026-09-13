import { defineConfig } from 'vite';
import { cpSync, existsSync, createReadStream, writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

// The live static build is immutable input. V2 never writes to dist/.
export default defineConfig({
  publicDir: 'assets-v2',
  build: { outDir: 'build-v2', emptyOutDir: true, sourcemap: true },
  plugins: [{
    name: 'legacy-data-read-only',
    configureServer(server) {
      server.middlewares.use('/__v2_benchmark', (req, res) => {
        const origin=req.headers.origin;
        if(req.method!=='POST'||!origin||!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(origin)){res.statusCode=403;res.end();return;}
        let body='';req.on('data',chunk=>{body+=chunk;if(body.length>65536)req.destroy();});
        req.on('end',()=>{try{const result=JSON.parse(body);if(!Number.isFinite(result.frames)||!Number.isFinite(result.maxDrawCalls))throw new Error('Invalid report');mkdirSync('.context',{recursive:true});writeFileSync('.context/render-benchmark.json',JSON.stringify(result,null,2));res.end('ok');}catch{res.statusCode=400;res.end();}});
      });
      server.middlewares.use('/data', (req, res, next) => {
        if((req.url||'').includes('padova-v2.bin.gz'))return next();
        const root = resolve('dist/data');
        let file: string;
        try { file = resolve(root, '.' + decodeURIComponent((req.url || '/').split('?')[0])); }
        catch { res.statusCode = 400; res.end(); return; }
        if (!file.startsWith(root + '/') || !existsSync(file)) return next();
        res.setHeader('Content-Type', file.endsWith('.json') ? 'application/json' : 'application/octet-stream');
        createReadStream(file).on('error', () => res.destroy()).pipe(res);
      });
    },
    closeBundle() { cpSync('dist/data', 'build-v2/data', { recursive: true }); }
  }]
});
