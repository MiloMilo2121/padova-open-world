# Evidence: finding, ranking and freezing sources

## Contents
1. Locating a landmark in game coordinates
2. Tier 1 — survey data (DBT) and how to read it
3. Tier 2 — OpenStreetMap
4. Tier 3 — published dimensions
5. Tier 4 — reference photographs and proportion extraction
6. Conflicts
7. Landmarks outside the current world
8. Freezing into `Data/Landmarks/sources.json`

## 1. Locating

Game coordinates are EPSG:7791 (RDN2008 / UTM 32N) metres rebased at 11.8744 E, 45.4077 N: Unity X = east, Z = north, Y = source elevation − 15 m. Convert with the project's transformer:

```python
# .context/geo-venv/bin/python
import sys; sys.path.insert(0, "Tools/geodata"); import padova
x, z = padova.local(lon, lat)          # WGS84 lon/lat ≈ RDN2008 to < 1 m
```

Then find the survey units around it (`Assets/World/WorldPlan.json` → `units` with `cx, cz, top, surveyBase, surveyHeight, outline, ringSizes`) and render a quick plan (PIL) labelled with unit ids and heights — the plan makes roles obvious (round units = drums/rotundas, tall 20 m² units = towers, holes = drums or courtyards). Units inside the core (`coreExtent`) live in `Assets/Geography/PadovaCentro/CityPlan.json` instead and are drawn by `PadovaCity`/`LandmarkBuilder`, not `WorldContext`; replacing those needs a change there, so flag it.

## 2. Tier 1 — DBT survey

Raw shapefiles: `.context/geodata/padova-dbt/*.shp` (Comune di Padova / Regione del Veneto DBT 2007, IODL 2.0, lon/lat EPSG:6706, Z in metres). Useful layers:

| Layer | Content | Key attributes |
| --- | --- | --- |
| UN_VOL | building volume units | QGR eave (abs), AV height, QCO ridge (usually 0 = missing), POR (01 ground, 02/03 suspended/projecting), INH clearance |
| EDIFC | whole buildings, use codes | EDIFC_USO |
| MN_UVOL / MN_EDI_VOL | volumetric monuments (statues, columns) | MN_UVO_QGR, MN_UVO_ALT |
| MN_EDI_NOVOL | flat structures (fountains 0411 …) | MNNV_CAT |
| PONTE | bridges | polygon Z = deck |
| AB_CDA | water areas | polygon Z = water edge |
| AR_VRD, AR_STR, AC_PED, AR_MARC | green, roads, pedestrian, sidewalks | Z |
| MU_SOST, SCARPT, ATTR_SP | walls, slopes, sports | |

Read with `shapefile` + `shapely` in the geo venv, transforming via `padova.local`. Survey semantics that bite:
- `top = QGR − 15` is the **eave**, not the roof ridge; nothing above it is surveyed.
- A church may be a single body unit with holes where the drums are; drum units can have eaves *below* the body eave.
- Suspended/projecting units (POR 02/03) with INH > 2 are porticoes; POR 03 with INH 0 can be projecting façade bays.
- A monument's MN_UVOL height can disagree with published figures — note it, don't silently pick.

## 3. Tier 2 — OpenStreetMap (ODbL)

Overpass is often busy; retry with mirrors and validate JSON before overwriting:

```bash
for ep in https://overpass.private.coffee/api/interpreter https://overpass-api.de/api/interpreter https://maps.mail.ru/osm/tools/overpass/api/interpreter; do
  curl -s -m 80 -A "PadovaOpenWorld/0.1 (<user email>)" --data-urlencode 'data=[out:json][timeout:50];(node["tourism"="artwork"](S,W,N,E);node["man_made"="obelisk"](S,W,N,E););out body;' $ep -o /tmp/osm.json
  python3 -c "import json;assert len(json.load(open('/tmp/osm.json'))['elements'])" && break; done
```

Good for: identities and `ref` numbers of statues/columns, `building:part` + `height`/`roof:shape` for well-mapped monuments (cross-check against DBT eaves), counts. Snap point features to surveyed lines (canal edge, parapet) and report snap statistics; treat points > ~4 m off as outliers and interpolate them, listing them.

## 4. Tier 3 — published dimensions

Prefer, in order: official owner/municipality/museum pages, `catalogo.beniculturali.it` (Catalogo generale dei Beni Culturali), UNESCO/heritage documentation, Wikipedia it (dimension infobox + text), scholarly guides. Quote exact figures and the page in the ledger. Typical useful numbers: tower/spire total height, dome interior height, façade height/width, counts of domes/arches/statues, monument base and statue dimensions.

## 5. Tier 4 — photographs (drawing reference only)

Search Wikimedia Commons via the API (namespace 6) and download thumbnails with `Special:FilePath/<name>?width=1280` into `.context/landmarks-ref/` (outside Git). Never texture them onto geometry and never redistribute. Record file names in `docs/THIRD_PARTY_ASSETS.md`.

Extracting proportions: pick a near-orthographic view, measure pixel spans of an element whose real size is anchored (a surveyed drum diameter, a published height), then scale other spans in the same depth plane. Prefer ratios between adjacent elements (cone height / drum diameter, loggia height / façade height). Upward-looking photos compress heights — use two photos and take the more frontal one. Write the ratio, photo name and anchor in the ledger.

Also build a **signature list**: the 5–10 features that make the landmark recognisable (e.g. Santo: conical crossing dome with gilded angel, minaret-like campanili with striped cones, seven lead domes with crosses, façade loggia gallery + rose window, Gattamelata). The model must show all of them.

## 6. Conflicts

Decision order: survey > published > photo ratio > typology default. When the survey's own values make the landmark look unlike photos (flat roof between domes, flattened gable), keep the survey and explain. When survey and a published figure disagree on the *same* measured quantity (Gattamelata 18.7 m vs ≈ 11 m), choose, justify and list it under "Known conflicts" in `Data/Landmarks/README.md` and the final report.

## 7. Outside the current world

`WorldPlan.extent` is ±1500 m east × ±1300 m north around the origin. A landmark elsewhere in Padova needs `Tools/world/expand.py` rerun with a larger extent (performance budget!). A landmark in another city needs that city's regional topographic database (e.g. Veneto IDT geoportal for other Veneto comuni; Lombardia, Emilia-Romagna, Toscana, Lazio each publish DBT/CTR data under open licences), a new origin and a new district/scene — a project decision. Explain the options and ask before starting.

## 8. Freezing

Add `extract_<slug>(world)` to `Tools/landmarks/extract_sources.py`, register it in `EXTRACTORS`, and run `.context/geo-venv/bin/python Tools/landmarks/extract_sources.py <slug>`. Store: source ids, outlines as local rings (CCW exterior), surveyed Z values (−15), any OSM points, any ground cells the landmark will own (`ground_cells_minus`). The script records SHA-256 hashes of every layer read and of WorldPlan.
