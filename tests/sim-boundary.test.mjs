import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';
import { resolve, relative } from 'node:path';
import { pathToFileURL } from 'node:url';

test('every simulation dependency is renderer-free and imports in Node', async () => {
  const root = resolve('src/sim');
  const visited = new Set();
  async function inspect(file) {
    if (visited.has(file)) return;
    visited.add(file);
    assert(!relative(root, file).startsWith('..'), `simulation escapes boundary: ${file}`);
    const source = await readFile(file, 'utf8');
    assert(!/\b(document|window|THREE|WebGLRenderer)\b/.test(source), file);
    for (const match of source.matchAll(/(?:from\s*|import\s*\()\s*['"]([^'"]+)['"]/g)) {
      assert(match[1].startsWith('.'), `external simulation dependency: ${match[1]}`);
      await inspect(resolve(file, '..', match[1]));
    }
    if(file.endsWith('.json')) JSON.parse(source);
    else await import(pathToFileURL(file));
  }
  for (const name of await readdir(root)) if (/\.(js|ts)$/.test(name)) await inspect(resolve(root, name));
});
