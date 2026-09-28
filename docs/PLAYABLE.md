# Padova exploration prototype

Open `Assets/Scenes/PadovaPlayable.unity` and press Play, or launch `.context/build/PadovaPlayable.app` after building. The game starts on foot in Piazza della Frutta.

## Controls

| Input | On foot | Driving | Sightseeing flight |
| --- | --- | --- | --- |
| Arrow keys (or WASD) | Camera-relative movement | Accelerate / reverse / steer | Climb / descend / bank |
| Shift | Run | — | Faster flight |
| Space | Jump | Brake | Air brake |
| Return | Enter nearby car | Exit when stopped | — |
| M | Open / close map | Open / close map | Open / close map |
| F | Start airborne tour | Start tour after stopping | Return to previous walking position |
| R | Return to market | Reset car to its parking position | End flight |
| Q / E, click-drag | Orbit camera | — | — |
| C / scroll | Centre camera / zoom | — | — |
| Tab | Toggle running | — | — |

The map pauses simulation. Drag to pan, scroll to zoom, click to set a waypoint, and press M or Esc to close it. Blue squares mark drivable cars. Distances are straight-line distances; this is not a route planner. Eight places can be discovered by exploring near them.

Three compact cars are available on Via Dante, Corso Milano and Via Roma. They use Rigidbody/WheelCollider suspension, steering, braking and architecture collision. These are player-driven vehicles; autonomous road traffic is not implemented.

F starts the aircraft already airborne. Flight assistance keeps it above the skyline and turns it back near the map boundary. There is no airport, takeoff, landing or flight-simulator physics. Ending flight restores the previous walking position.

## City and evidence

The detailed core retains Claude's modelled Palazzo della Ragione, façades, textured surfaces, porticoes and roofs. Additional landmark geometry covers the clock tower, Capitanio frontage, Duomo/baptistery and the Ancient Courtyard of Palazzo del Bo. These are reference-informed models with simplified ornament, not scanned reconstructions.

A 3 × 2.6 km envelope adds 19,355 municipal **volume units**, source road/green/water polygons and lower-detail roof geometry. Buildings can contain several volume units. The map uses the same survey outlines. Thirty-two animated pedestrians navigate a baked central NavMesh; twelve market stalls, eleven lamps, six benches and trees populate the scene. Individual trees and street objects are authored placements.

See [architecture and fidelity](ARCHITECTURE.md), [survey provenance](REAL_WORLD_DATA.md), and [landmark references and expansion limits](../Data/World/landmarks.md). DBT records date from 2007. Ordinary façades and roofs are typology; material textures are reusable surfaces, not site scans. Interiors and the whole city are not finished.

## Rebuild and verify

The saved scene, plans, assets and NavMesh work offline. Recreating the world from those inputs:

```sh
unity status --project-path "$PWD"
unity command set_autotick --enable true --interval_ms 50 --project-path "$PWD"
unity command recompile --project-path "$PWD"
unity command recompile_status --project-path "$PWD"
unity command run_script --file AgentScripts/BuildPadovaCity.cs --entry BuildPadovaCity.Build --project-path "$PWD"
unity command run_script --file AgentScripts/BuildOpenWorld.cs --entry BuildOpenWorld.Build --project-path "$PWD"
unity command run_tests --mode editor --async_tests true --project-path "$PWD"
unity command test_status --project-path "$PWD"
python3 Tools/verify_world.py --build --measure
```

`BuildOpenWorld` imports versioned `Data/World` files, saves vehicle meshes and pedestrian assets through Unity APIs, regenerates the surroundings and bakes pedestrian navigation. If the original skin files are absent from `.context/playable/Kenney/Skins`, it uses the already imported assets.

Re-exporting geography additionally needs the original municipal archive under `.context/geodata/padova-dbt`, the regional road snapshot `.context/world/street-network.json`, and the existing Python/CGAL setup:

```sh
.context/geo-venv/bin/python Tools/world/expand.py
.context/geo-venv/bin/python Tools/world/map.py
.context/geo-venv/bin/python Tools/world/verify_sources.py
```

`verify_world.py` reuses the fresh Player PID, focus checks and source fingerprint from `verify_playable.py`. Tests send actual input and assert animation, movement, map pause/waypoints, car travel/steering/braking/exit, aircraft climb/bank/return and NPC route progress. Screenshots are written under `.context/world/`; the report is `.context/playable-verification.json`. The Player closes after testing. Use `--case car` to rerun a failed scenario without rebuilding unchanged source.

Short performance samples are not a sustained thermal benchmark. A representative 20-minute M4 Air session remains an acceptance gate.

## Verification, 2026-09-28

- 15 EditMode tests passed; the six walking/geometry tests were rerun after ground tessellation and passed again.
- Final macOS Development build succeeded in 13.97 seconds with **zero errors and warnings**. All 11 native input/state scenarios passed: animation, four arrow directions/camera controls, walk/run, jump, collision, recovery, map, driving, flight, crowd movement and character grounding. Evidence: `.context/world/final-gameplay-verification.json`.
- The source comparison verified 19,355 volume units, 159,468 original outline vertices and 2,184 suspended clearances.
- A fresh 20-second walking interval without RPC polling recorded 60.00 FPS, 12.19 ms GPU time, a worst sampled frame of 18.63 ms and 541.6 MB Unity-allocated memory (`.context/world/quiet-performance.json`). This is a short window, not sustained certification.
- RPC-heavy runs recorded repeated roughly one-second stalls. Later attempts to collect an independent flight window encountered Pipeline command timeouts after the Player had become ready. The cause is unresolved. The successful gameplay report is retained separately from `.context/world/quiet-focus-failure.json`; do not claim stable flight or long-session performance from these runs.
