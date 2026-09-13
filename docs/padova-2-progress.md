# PADOVA 2 — execution ledger

Updated 2026-09-13. Work branch: `repo-improvement-audit`; base `origin/main`.
This is a development milestone, not completion of the attached multi-phase plan.

## Live isolation

`dist/` and `.openai/hosting.json` remain immutable. No main merge, no deployment.
A hash-manifest test checks every live file. V2 uses `src/`, root `index.html`,
`app/`, generated `assets-v2/` and `build-v2/`; its save key is separate.
`npm run dev:legacy` serves the original build.

## Implemented

- Vite/TypeScript migration, ESLint, CI and recursive pure-simulation import boundary.
- Stale renaissance checks removed; V2 police geometry/material disposal fixed.
- Shared bicycle driving and swept vehicle collisions: axle load transfer, lateral
  grip, handbrake drift, JSON handling, keyboard ramp and standard gamepad support.
- Synthesized engine harmonics, tires, wind, impacts, spatial sirens; bounded smoke
  and skid buffers; asymmetric FOV and reduced-motion handling.
- uWebSockets authoritative server: 60 Hz simulation, 20 Hz binary snapshots,
  32-car rooms, input validation/rate bounds, spatial interest filtering,
  prediction/reconciliation and 125 ms remote interpolation. Local join/leave UI.
- Real OSM footprint edges receive procedural cornices, plinths, shutters, windows
  and some balconies. Static batching, instanced pedestrians, consolidated car
  glass and warm sky/lighting added to V2 only.
- Map geometry uses a binary decimetre-delta format decoded in a persistent worker.
  The global road/named-landmark base is 1,292,770 bytes; anonymous buildings are
  split across 1,122 gzip tiles of 400 m. The initial centre fetch is 1,566,794
  bytes and 8,960 footprints, compared with 3,712,684 bytes and all 87,881
  footprints before tiling. Moving and map travel prefetch further tiles.
- Fingerprinted Via Monte Cero endpoint correction applied to V2 client/server.
- Real building source research and Blender/GLB asset queue documented separately.
- Visible terrain is clamped below nearby surface roads, including overlapping OSM
  ways at Piazza delle Erbe, and character roots account for the model's actual
  sole height. Tunnels and raised crossings retain their separate vertical level.
- City geometry now streams in a circular queue: two immediate chunks, one later
  chunk per time slice, a 600 m gameplay prefetch band and distant chunk disposal.
  Decoded building tiles become collidable before rendering and enter the world
  one tile per time slice. The minimap renders in idle batches after play is ready.
- Road meshes cache their centreline samples, use 6 m render sections and create
  junction fans only at real source vertices. Road-surface nodes keep a stable V8
  object shape and use bounded smoothing over 12 m samples.

## Verification and limits

23 pure tests cover driving, protocol, delayed/missing snapshot reconciliation,
render batching, server capacity/input flood bounds, idle-input expiry and live
isolation, signal/tram batching, tile selection/cache reuse, dynamic collision and
progressive world streaming. A V2 controller
harness drives actual map terrain and checks camera finiteness, road/ground
separation, sole placement and resource disposal. `npm run check` passed: typecheck, lint, simulation/controller tests, legacy
city/terrain/modern tests, map audit and V2 production build. The added map budget
test also passed separately.

The isolated 32-client, 20-second real WebSocket loopback run passed with
zero errors, approximately 9.5–10.0 KiB/s per player and server tick p99 11.63 ms.
A simultaneous browser/full-suite load caused queue overflow and disconnects;
that failed run is retained in `.context/multiplayer-load-contended.json`.
The server now bounds pending input to eight recent commands, dropping obsolete
commands after stalls without granting extra simulation steps.
See `multiplayer-load.json` for the actual run, not a hosting capacity promise.

Chrome rendered the V2 scene and exposed bugs in gzip handling, startup and the
online-button layout; these were fixed. The pre-instancing street observation
was 507 draws / 666k triangles and Chrome reported substantial memory use.
The subsequent pre-streaming diagnostic flythrough reached 605 draws, 803k triangles and
1.61 GB heap. Its 917 ms frame p99 includes tab visibility changes and simultaneous
repository tests: it does not establish foreground FPS. Graphics budgets are
not met and that report predates the latest chunk/road optimizations; see
`render-benchmark.json`. `?benchmark=1` is a diagnostic route; rendering
budgets in `perf-budget.json` are targets, not certified results. CI enforces the
map download budget; it does not yet enforce a deterministic GPU scene budget.

The isolated Node startup profile now reaches 253 MiB after world indexes and the
first two geometry chunks, versus about 451 MiB after full-map world indexing in
the comparable pre-tiling profile. This is process-heap evidence, not browser or
VRAM certification. Global road-surface construction still takes about 3.9 s in
that harness and is the next startup bottleneck.

## Outstanding plan work

- Public multiplayer trial/deployment, network adversity over a real transport,
  long-session stability, contact resolution tuning and delta snapshots.
- Authoritative police/missions/signals and shared NPC promotion. Online currently
  limits players to cars and suspends local NPC simulation; no online walking.
- Road/topology tiling, zero-copy quantized GPU buffers, screen-space LOD, baked AO,
  complete GPU memory accounting, new Three version/CSM/postprocessing.
- Downloaded and verified real landmark meshes; none are claimed included yet.
- City-content density, police search behavior, economy, remapping UI and strict
  V2 topology/clearance audit. First delivery start is integrated but not a full
  redesign of the first 90 seconds.

## GitHub

The configured account cannot push to `scandolo/padova-open-world` (403).
A fork at `MiloMilo2121/padova-open-world` provides the authorized GitHub backup.
The original origin and current branch name are preserved. No production branch
is overwritten or merged by this work.
