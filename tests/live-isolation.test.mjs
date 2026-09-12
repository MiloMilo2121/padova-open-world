import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import manifest from '../docs/live-build-sha256.json' with {type:'json'};
test('live game and hosting configuration remain byte-for-byte unchanged', () => {
  for(const [file,hash] of Object.entries(manifest)) assert.equal(createHash('sha256').update(readFileSync(file)).digest('hex'),hash,file);
});
