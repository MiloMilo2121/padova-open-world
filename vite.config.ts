import { defineConfig } from 'vite';
import { cpSync, existsSync, createReadStream } from 'node:fs';
import { resolve } from 'node:path';

// The live static build is immutable input. V2 never writes to dist/.
export default defineConfig({
  publicDir: false,
  build: { outDir: 'build-v2', emptyOutDir: true, sourcemap: true },
  plugins: [{
    name: 'legacy-data-read-only',
    configureServer(server) {
      server.middlewares.use('/data', (req, res, next) => {
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
