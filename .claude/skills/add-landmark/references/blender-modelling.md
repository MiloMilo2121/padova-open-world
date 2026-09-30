# Blender modelling conventions

## Contents
1. Module contract
2. `lmcommon` API
3. Reusable architectural helpers (in `santo.py` / `prato.py`)
4. Style and budget
5. Visual QA checklist
6. Pitfalls already paid for

## 1. Module contract

`Tools/blender/<slug>.py`, registered in `REGISTRY` of `Tools/blender/build_landmarks.py`:

```python
NAME = "SantaGiustina"                      # FBX / Unity object name (no spaces)
VIEWS = {"front": (eye, target, lens_mm)}  # anchor-relative Blender coords for --render previews

def build(src, g):                         # src = sources.json[slug]; g = lm.Ground (game ground height)
    ...
    return {"anchor": [x, y, z],           # game coords of the model origin (east, up, north)
            "builders": [visual, ...],     # lm.Builder objects -> mesh objects
            "collision": col,              # simple survey volumes -> <NAME>_Collision
            "info": {...},                 # counts, snap stats, conflicts: goes to <slug>-build.json
            "replaces": {"units": [...], "patches": [...], "ownGround": [x0, z0, x1, z1, ...]},
            "places": [{"name": "...", "x": .., "z": .., "source": "..."}]}
```

Build everything in absolute game-grid coordinates (x = east, y = north, z = height relative to the anchor's Y), then subtract the anchor x/y at the end (see `santo.build`). Heights: `u["base"] - anchor_y` and `u["top"] - anchor_y` for surveyed units; `g(x, y) - anchor_y` for terrain-following elements. Builder names ending in `_Ground` become walkable layer-8 colliders, `_Water` gets no collider, `_Collision` is hidden.

## 2. `lmcommon` API (Tools/blender/lmcommon.py)

- `Builder(name)`: `face(pts, mat)`, `quad`, `polygon(rings, z, mat)` (flat with holes), `indexed(xyz, tris, mat)`, `grid(rows, mat)` (smooth shared-vertex surface, metric UVs), `lathe(profile[(r, z)], centre, mat, segments, rot)`, `box(centre, size, mat, rot)`, `transformed(other_builder, Matrix)` (instance a sub-model), `.triangles`.
- Geometry: `ring_points(outline, sizes, i)`, `edges(ring)` → (a, b, L, outward normal), `offset_ring(ring, d)` (mitred; +d = away from the solid), `centroid`, `area`, `point_in`, `Frame(a, b)` → `P(u, v, w)` for work on a wall plane (w = outward offset), `arch_outline(u0, u1, spring, pointed=)`, `arch_ring(...)`.
- `Ground(sources["ground"])`: exact port of `WorldPlan.GroundAt`.
- `materials(names)`: Blender preview materials read from the Unity `.mat` files (colour, texture, tiling) plus `EXTRA` for new ones.
- `export(objects, blend, fbx)`: FBX with the axis settings `BuildLandmarks` expects; saves the `.blend` without `.blend1` backups.

## 3. Reusable helpers

Copy or import from existing modules rather than re-inventing:
- `santo.py`: `walls`, `cornice`, `archlets` (Romanesque corbel table), `window` (round/pointed with stone surround), `pilaster`, `ribbed_shell` (lead dome or cone with standing seams), `dome` (drum + dome/cone + lantern + cross), `campanile` (bands, belfry, balustraded gallery, octagonal stage, striped spire), `turret`, `plain_unit` (surveyed volume + roof + cornice + windows + pilasters), `facade` (portals, loggia gallery, rose window, biforas, gable), `gattamelata` (pedestal + figure from lathe pieces), `angel`, `cross`.
- `prato.py`: `statue` (4 pose variants), `pedestal`, `obelisk`, `bridge` (deck profile from surveyed Z, segmental arch from surveyed canal edges, balustrades, barrier), `vertical_polygon`, `nearest_on_ring`/`at_arclength` (snap and interpolate numbered items along a line).
- Ground re-cut: `extract_sources.ground_cells_minus` + `Prato_Ground` pattern when the landmark changes ground (canals, sunken courts, raised platforms).

## 4. Style and budget

- The game look: tiling PBR materials from `Assets/Art/Padova/Materials`, modelled relief (cornices, arches, windows as dark/glass panels with stone surrounds), no baked lighting, no photo textures. Match ornament density to neighbouring buildings; readable silhouettes matter more than tiny detail.
- Ornament must stay within ~0.5 m of a surveyed wall unless the element genuinely projects (balustrade galleries, porches).
- Budget per landmark ≈ 50–120k triangles, one visual mesh per logical part plus a collision mesh of a few thousand triangles. Statues/figures ≈ 600–1200 triangles each.

## 5. Visual QA checklist (renders vs photos)

Render with `--render` (Eevee, 1600×1000) from at least a street-level front view, an aerial view and a signature detail. Then check:
- Every item on the signature list is present and roughly where the photos put it; counts match.
- Heights read right: compare ratios (tower/dome/façade) against the photo with a ruler, not by eye.
- No feature hidden inside a wall (common when offsets are computed from the wrong plane).
- No z-fighting (coincident opposite faces), no floating or sunken props, no holes between surveyed volumes and above-eave forms.
- Materials are the intended ones (brick vs stone vs lead) — in Unity, close-ups too.
- Triangle count in `<slug>-build.json` within budget.

## 6. Pitfalls already paid for

- UV magnitude: `face_idx` shifts box-projected UVs per face by 8.8 m periods. Custom `uv=` arguments should also stay small (< ~50 m).
- Two-sided thin elements: build two faces a few cm apart (see balustrades, cloaks, angel wings).
- `Frame` normals: `Frame(a, b)` normal is `(t.y, −t.x)` — outward for CCW rings; decorating holes (CW) flips it.
- Interpolating numbered series: wrap within the series (outer 1–44 / inner 45–88) or the search never ends.
- Blender runs in ~1–10 s per landmark; if a build takes minutes, suspect a loop, not geometry size.
