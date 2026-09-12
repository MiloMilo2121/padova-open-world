import tseslint from 'typescript-eslint';
export default [
  { ignores: ['dist/**', 'build-v2/**', 'node_modules/**'] },
  { files: ['src/**/*.js'], rules: { 'no-unreachable': 'error', 'no-dupe-args': 'error', 'no-dupe-keys': 'error', 'valid-typeof': 'error' } },
  ...tseslint.configs.recommended.map(config => ({ ...config, files: ['src/**/*.ts', 'server/**/*.ts'] })),
  { files: ['src/sim/**/*.{js,ts}'], rules: { 'no-restricted-imports': ['error', { patterns: ['*three*', '*view*', '*vendor*'] }] } }
];
