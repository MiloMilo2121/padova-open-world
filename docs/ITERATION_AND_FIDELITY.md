# Iteration fixes and architectural fidelity

## What failed in the first handoff

The previous scene was a GIS volume blockout with generic tiling materials. It did not reconstruct Padova's façades, roofs, shops or arcades. Passing geometry and movement tests did not make it visually faithful. Treat that as a failed visual acceptance gate, not a finished city.

The user's screenshot also showed the stopped Editor's saved T-pose and large ground shards. The live Editor was stopped (`Application.isPlaying=false`, animation time zero), so that preview was not evidence of a broken runtime animator. The saved scene now contains an idle pose; runtime verification additionally compares actual foot-bone rotations.

## Ground repair

The imported ground had 1,182 shared XY positions with elevations differing by over 10 cm among the road/pedestrian/sidewalk layers. Drawing all three produced intersections and raised shards. Millimetre rendering offsets could not fix metre-scale elevation disagreement.

`Tools/geodata/build_walk_surface.py` dissolves the three mapped plan layers into a single coverage polygon, preserving the mapped outer boundary and holes. It fits a robust plane to 3,459 sidewalk elevation samples (roughly 0.491 m RMS residual) to make a continuous navigation/render surface. This is a documented elevation approximation, not a new ground survey. Raw DBT records and the original survey scene remain intact. Small curbs and detailed ground relief still require better measurements.

Unresolved portico caps remain in the inspection scene/data. Their free-floating placeholder surfaces are hidden and non-colliding in the playable scene until genuine supported geometry replaces them.

## Recognizable architecture

Palazzo della Ragione's north elevation now uses Didier Descouens's 2017 photograph, with separate shop/loggia/hall/eave layers and a curved roof envelope registered to the DBT footprint. The source JPEG is unchanged; cropping/mapping occurs in mesh UVs. Attribution and CC BY-SA 4.0 adaptation terms are in `Data/Architecture/` and beside the Unity asset.

This is **a photographic elevation study**, not a measured 3D reconstruction: lighting and foreground occluders are baked into the photo; layer depths, roof cross-section and registration are approximate. The rear/end elevations and most surrounding buildings are still unfinished. Do not describe these as photogrammetry, scanned façades or complete Padova architecture. The north photo must not be mirrored onto the south façade as if it were a photograph of that side.

The public Sketchfab candidate was inspected: it depicts a physical tactile miniature, complete with a base and Braille labels. It is not a scan of the real building. Downloading it would not resolve architectural accuracy.

## Faster verification without dropping checks

1. Run source/mesh checks, then inspect the actual starting view in Editor Play Mode before a native build. A produced screenshot is not a visual pass; look at it.
2. Use the compiled `gameplay_state`, `gameplay_fixture`, `gameplay_camera`, `gameplay_capture`, `gameplay_grounding` and `gameplay_collision_fixture` commands. They avoid repeated Roslyn compilation, reflection snippets and custom-assembly reference failures.
3. Run `python3 Tools/verify_playable.py --editor --case controls,jump` during iteration. Rerun the affected case after a fix. The suite validates real arrow-key input, run toggle, foot-bone motion, speeds, jump/landing, objective state, building/camera collision and recovery.
4. Use InputAction callbacks for single-press actions. Pipeline explicitly flushes Input System events; polling `wasPressedThisFrame` on a later update can miss them. Held Shift was also unreliable in the Editor's synthetic modifier path, so the Editor speed test uses Tab toggle; the native test independently verifies held Shift.
5. Before native QA, close the prior Player for this exact app path. The descriptor is reused across launches. Wait for its PID to equal the newly launched process, then activate that app with `open -a`. A diagnostic confirmed `Application.isFocused=false` before activation and true afterward; arrow input then moved the player.
6. Refuse reuse of a build whose source/assets fingerprint differs. Record both process ID and build GUID with the result. A queued build is not a successful build.
7. Prefer bounded state conditions over fixed-duration travel assertions. Readiness includes the right scene, actual Play state, grounding and frame progress. Key releases run in `finally` blocks.
8. The final gate is `python3 Tools/verify_playable.py --build --measure`. Native launch, controls, rendering and short performance samples remain mandatory for a gameplay milestone. A representative 20-minute thermal/gameplay benchmark remains a separate acceptance task.

The first complete native run of this revised harness took 26.91 seconds excluding the 11.57-second incremental build, including short counter samples. The remaining five Editor groups took 7.91 seconds. These measurements characterize these runs, not guaranteed timings on every machine.

## Rebuild the presentation

After the base playable builder, run:

```sh
.context/geo-venv/bin/python Tools/geodata/build_walk_surface.py
unity command run_script --file AgentScripts/UpgradePadovaPresentation.cs --entry UpgradePadovaPresentation.Build
```

On a fresh clone the imported photograph and attribution are already workspace assets; the builder only needs the `.context` source download when the photograph is missing. The initial source URL and SHA-256 are recorded in `Data/Architecture/ragione-reference.json`.
