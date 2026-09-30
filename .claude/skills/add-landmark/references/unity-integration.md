# Unity integration and verification

## Contents
1. What the pipeline already does
2. Commands in order
3. Tests to add
4. Native verification
5. Troubleshooting

## 1. What the pipeline already does

- `Tools/blender/build_landmarks.py` merges every registered landmark's `replaces` and `places` into `Assets/Art/Landmarks/Landmarks.json`, and fails if two landmarks claim the same survey record.
- `WorldContext` (`Assets/Scripts/Architecture/WorldContext.cs`) reads that manifest. It skips `replacedUnits` and `replacedPatches`, skips ground cells fully inside `ownGround` rectangles, and appends `places` to the discovery list. `BuildOpenWorld.cs` wires the manifest, so regenerating the world keeps the exclusions.
- `AgentScripts/BuildLandmarks.cs`:
  - `Import()` sets FBX importer options (axis bake, no compression, UInt32 indices when needed). It remaps FBX materials by name onto `Assets/Art/Padova/Materials` and `Assets/Art/Landmarks/Materials`, and is idempotent.
  - `Place()` instantiates every manifest model under `Landmark models` at its anchor, rotated `Euler(90, 0, 0)`. It puts everything on layer 9, adds MeshColliders to `_Collision` (renderer hidden) and `_Ground` (layer 8), and saves `PadovaPlayable.unity`.

## 2. Commands (from the project root; add `--project-path=$PWD` when more than one Editor is open)

```bash
unity status                                                     # Editor ready for THIS project?
unity command set_autotick --enable true --interval_ms 50
unity command run_script --file AgentScripts/BuildLandmarks.cs --entry BuildLandmarks.Build
unity command run_script --file AgentScripts/CaptureViews.cs --entry CaptureViews.Capture \
      --args '["'$PWD'/.context/views", "<view names separated by spaces>"]'
unity command recompile && unity command recompile_status        # after C# edits; check failed/errors
unity command run_tests --mode editor                            # Total > 0, Failed == 0
python3 Tools/verify_world.py --editor --case landmarks,<case>   # quick, Editor Play Mode
python3 Tools/verify_world.py --build --measure                  # native gate
```

`run_script` returns anonymous objects as strings. Return lists of strings or `List<object>` of anonymous objects for readable reports. Scratch probes belong in `.context/scratch/` (Git ignores them). Use the prefix `using System.Linq;` there, since `run_script` compiles one file.

## 3. Tests to add (`Assets/Tests/EditMode/LandmarkModelTests.cs`)

`EveryManifestModelIsPlacedWithHiddenCollisionAndDiscoveryPoint` covers every landmark automatically. Add a focused test per landmark that asserts **survey conformance** and **gameplay**:
- Collision bounds equal the min/max of the replaced units' outlines (x/z within 2 cm), and max/min Y equal the surveyed eave and base.
- Published totals (spire tip, tower height) within 0.1 m of the visual bounds.
- Raycasts: down onto a key surveyed element hits its eave, discovery points have ground, and cut-outs (water, sunken areas) have no layer-8 ground above them.
- Counts (statues, arches) through the build report or mesh sizes when relevant.

Look components up by MeshFilter name (`Part(model, part)` in the file), because the model root shares its name with its main mesh.

## 4. Native verification

`Tools/verify_world.py` includes the `landmarks` case. For every manifest place it teleports with `world_fixture --name at --x --z --yaw` and requires grounding and a new discovery. Add a dedicated case when the landmark has special movement: the Prato case crosses a bridge and asserts the walker never drops toward the surveyed water level. Screenshots go to `.context/world/`, and the report to `.context/playable-verification.json`.

The Player needs keyboard focus. Tests fail with "Player lost focus" when the user is using the Mac. Rerun the failed cases with `--case` without `--build`, since the source fingerprint is reused. Report both runs honestly.

Record for the user: build result, case results, FPS, max frame ms, GPU ms and allocated memory from the `--measure` samples. A short run is not the 20-minute thermal benchmark, so say so.

## 5. Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Model lying on its side or mirrored | Axis rotation changed; `Place()` must use `Euler(90, 0, 0)` with the current `lmcommon.export` settings. |
| Surface white or flat colour close up, fine far away | UVs too large; check the per-face shift in `lmcommon.face_idx` and any custom `uv=`. |
| Materials look like grey Blender defaults | Remap failed. Check the `mapped`/`missing` counts in the Import report. The generic test catches this. |
| Old generic building still visible inside the model | The unit id is missing from `replaces.units` (or the unit is in the core CityPlan, not WorldPlan). |
| Player falls through or floats | Missing `_Ground` or `_Collision` geometry. Ground-owning landmarks must cover the entire `ownGround` rectangles. |
| `No Pipeline instance found` | The Editor closed. Reopen it with `open -n -a /Applications/Unity/Hub/Editor/<ver>/Unity.app --args -projectPath $PWD` and wait for `unity status` → ready. |
