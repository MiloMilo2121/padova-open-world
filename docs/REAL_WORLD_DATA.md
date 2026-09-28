# Central Padova: geographic foundation

The first district covers the historic core around Palazzo della Ragione, Piazza delle Erbe, Piazza della Frutta and Piazza dei Signori. The user requires real street layouts and real buildings, using public sources for now. No procedural replacement architecture, invented street widths, guessed heights, generated façades or fictional windows may be presented as a reconstruction.

## Implemented

For the current exploration game, see [PLAYABLE.md](PLAYABLE.md), [ARCHITECTURE.md](ARCHITECTURE.md) and [expansion provenance](../Data/World/landmarks.md). The photographic Palazzo experiment has been removed; all current façades are geometry. The descriptions below document the separate original **survey inspection scene**, not the current game's architectural detail. `ITERATION_AND_FIDELITY.md` retains historical process findings.

`Assets/Scenes/PadovaCentroSurvey.unity` is a navigable **survey study**, an intermediate geographic foundation, not a finished reconstruction or walking gameplay milestone.

- 1,374 volumetric units: several units can belong to one building. Do not report this as 1,374 buildings.
- 519 road, pedestrian and sidewalk polygon parts with source boundary elevations.
- 333 portico/overhang units shown as amber reference caps. Clearance and supports remain unresolved; no wall is generated across the opening.
- Original polygon outlines, including courtyards, without convex hulls or regularized streets.
- Source IDs and elevation attributes inspectable by clicking geometry.
- Three piazza viewpoints anchored inside the named municipal street polygons.

WASD pans, Q/E changes altitude, Shift moves faster, right mouse drag looks around, and the wheel zooms. F switches to a north-up plan, R resets, and 1/2/3 focus Erbe/Frutta/Signori. This flying inspection camera does not imply tested pedestrian accessibility.

## Source and rights

**Comune di Padova topographic database, “LOTTO COMUNE DI PADOVA”, 2007**, distributed through the Regione del Veneto IDT Geoportal. The `ETRF2000` area archive is named `c0111114_ETRF2000_aree.zip`. Its actual `.prj` is **EPSG:6706 (RDN2008 geographic)**: longitude/latitude, not metres.

- [Geoportal and download interface](https://idt2.regione.veneto.it/idt/webgis/viewer?webgisId=86)
- [Regional database description](https://www.regione.veneto.it/web/ambiente-e-territorio/db-topografico)
- [Regional DBT specification v2.6](https://repository.regione.veneto.it/public/019aa3f327ffb100eb42673cffe94f1a.php?dl=true), volumetric unit definitions on printed pages 39–40.
- [Regional terms: Italian Open Data License 2.0](https://www.regione.veneto.it/web/ambiente-e-territorio/condizioni-di-utilizzo-geoportale)

Attribution: **Comune di Padova / Regione del Veneto, DBT 2007, IODL 2.0. Geographic subset, coordinate conversion and cartographic mesh representation by Padova Open World.** The Player also displays attribution. No endorsement is implied. Code licensing does not replace the data license.

`Data/PadovaCentro/manifest.json` records the download URL, date, CRS, original component SHA-256 hashes, bounds, counts and subset hashes. `source/` preserves original feature attributes and XYZ vertices. Full city archives remain in `.context/`. The versioned subset works offline.

| Layer | Meaning | Representation |
| --- | --- | --- |
| UN_VOL | Building volumetric units | Source footprint and height; flat eave reference cap |
| AR_STR | Road areas | Surface polygon and boundary Z |
| AC_PED | Pedestrian circulation | Surface polygon and boundary Z |
| AR_MARC | Sidewalk areas | Surface polygon and boundary Z |
| TP_STR | Named street areas | IDs and locations for labels; not stacked terrain |

One invalid named-street polygon (`TP_STR:111`) remains in the source snapshot and is explicitly omitted from label generation. It is not silently repaired. See `validation.json` for the import report.

## Accuracy and limits

This represents **2007 records**, not a certified model of today's city. Keep the date visible until changes have been checked against newer evidence.

The regional 2022 “Edifici del Veneto” WFS was investigated first. Its metadata states one-metre positional accuracy, but central records are dated 2007 and lack heights. It is **not** the final import source; do not transfer its accuracy claim to this DBT without verification.

Coordinates transform from EPSG:6706 to EPSG:7791 (RDN2008 / UTM zone 32N), rebased at 11.8744 E, 45.4077 N. Unity X is grid east, Z is grid north, and one unit is one metre. Grid north differs slightly from true north. Y subtracts a 15 m reference offset without redefining the source vertical datum. Bounds are 11.8705–11.8779 E, 45.4057–45.4093 N, roughly 580 × 400 m. Intersecting building units retain complete outlines; road surfaces are clipped at the boundary.

For ground-based units (`UN_VOL_POR=01`), the cartographic representation uses `UN_VOL_QGR` as the upper eave plane and `UN_VOL_QGR - UN_VOL_AV` as its nominal base. These are source attributes, not generated heights. The legacy QGR-to-eaves mapping is inferred from naming and its relationship to height and boundary Z; the newer regional specification uses QG. Confirm the legacy schema before treating these as certified architectural elevations. Polygon Z and the derived nominal base differ by several metres on some units; raw values remain available for audit.

In the original inspection scene, other portion types get reference caps. The later architectural pipeline correctly uses `UN_VOL_INH` for valid suspended portico clearances; it builds actual openings, with column spacing and ornament labelled as typology. All `UN_VOL_QCO` ridge values in the core subset are zero. Roof slopes, façade detail and reusable surface materials in the game are therefore reference-informed or typological, not surveyed ridges or pavement scans. The inspection scene remains diagrammatic.

## Architectural evidence queue

1. Palazzo della Ragione: [municipal museums document a laser-scanned model](https://padovamusei.it/it/news/modellino-3d-palazzo-ragione), September 2026. The page supplies neither the digital asset nor a reuse license. No request has been sent.
2. [Archeologya's Palazzo model](https://sketchfab.com/3d-models/palazzo-della-ragione-padova-7099891d795046c39644466d19eb8aca): public API metadata reports downloadable, CC BY 4.0, 148,770 faces. The official download endpoint requires authentication. Not imported; dimensions and survey provenance remain unverified. A CC license alone does not establish accuracy.
3. [Current municipal planning sheets](https://www.comune.padova.it/piano-degli-interventi-pi-geoportale-ed-elaborati-vigenti) can help check footprint changes, but do not establish authentic façades.

Each architectural asset must have a source and verification method: licensed survey/scan, measured drawings, or calibrated photography checked against control dimensions. Unobserved sides stay unresolved. Public visibility alone does not grant rights to extract imagery or meshes from proprietary mapping services.

## Reproduce

From the repository root:

```sh
python3 -m venv .context/geo-venv
.context/geo-venv/bin/pip install -r Tools/geodata/requirements.txt
.context/geo-venv/bin/python Tools/geodata/padova.py
.context/geo-venv/bin/python -m unittest discover -s Tools/geodata -v
unity status --format json
unity command set_autotick --enable true --interval_ms 50
unity command recompile
unity command recompile_status --format json
unity command run_script --file AgentScripts/BuildPadovaSurvey.cs --entry BuildPadovaSurvey.Build
unity command run_tests --mode editor --format json
python3 Tools/verify_survey.py --build
```

Normal Python runs use pinned local snapshots and validate hashes. `--acquire` explicitly refreshes them from the archive, downloading it if needed. Review changes before accepting upstream data. Unity creates scene, meshes, materials and `.meta` files through its APIs. The builder refuses to replace a scene with unsaved work. Generated mesh data and scene assets are versioned so a fresh clone needs neither Python nor network access to open the district.

Checks cover metric scale, concavity, courtyard holes, upward triangle winding, source hashes, preserved heights and unresolved porticoes. Unity tests verify saved mesh references, counts, anchor distances and dimensions. Player testing additionally checks actual input against camera/view state and captures rendered output. Short-run counters characterize this survey scene only; they do not establish sustained M4 Air game performance.
