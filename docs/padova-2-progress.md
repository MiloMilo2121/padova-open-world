# PADOVA 2 — execution ledger

Started 2026-09-12, approximately 21:11 Europe/Rome. User limit: six hours.
Work branch: `repo-improvement-audit` (do not rename). Base: `origin/main`.

## Non-negotiable isolation

`dist/` and `.openai/hosting.json` are immutable. No merge to main and no deployment
of the existing site. V2 uses `src/`, root `index.html`, `app/` styles and
`build-v2/` output. `npm run dev:legacy` still serves the original build.
The V2 save key must remain separate from the original save key.

## Implemented so far

- Vite + TypeScript scaffolding, JavaScript migration boundary, ESLint and CI.
- Nine existing pure modules moved into `src/sim` in the V2 source tree.
- Renderer dependency boundary tested by recursively importing simulation in Node.
- Removed stale renaissance checks (live files unchanged).
- V2 police disposal and per-entity temporary array allocation fixes.
- Bicycle driving model with lateral velocity, axle loads and rear grip reduction.
- JSON handling profiles; tests for braking, reversing, drift and replay.
- Initial integration of the new driving model into the V2 controller.
- Keyboard steering ramp and standard gamepad analog driving input.
- Engine harmonics, filtered wind, slip-driven tire sound and positional sirens.

## Still required / not yet certified

- Browser gameplay QA, collision regressions on V2, complete resource ownership audit.
- Shared authoritative movement/collision, binary protocol, prediction/reconciliation,
  remote interpolation, 32-client load and adverse-network tests, server packaging.
- Significant graphics improvement, bounded effects, asset/data streaming,
  deterministic rendering budgets and exported performance evidence.
- City content/police/economy improvements and POI/clearance audit gates.
- Research real Padova building shapes and lawful downloadable assets (explicit user request).
- No public multiplayer deployment or real laptop FPS qualification yet.

## Environment

Initial npm install hit ENOSPC. Cleared only reproducible npm cache, retried successfully.
`~/ai-stack` is absent. CUA reports no browser available; HTTP preview responds on 5174.
