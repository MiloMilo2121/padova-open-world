# Real building shapes — Padova research queue

Research started 2026-09-12, following the user's request to substantially improve geometry.
The current map already has OSM footprints; the missing information is roof geometry,
facade relief, arcades and accurate landmark silhouettes. Blender is an asset processing
and authoring tool, not a source of surveyed city geometry.

## Verified initial candidates

- [Palazzo della Ragione, archeologya](https://sketchfab.com/3d-models/palazzo-della-ragione-padova-7099891d795046c39644466d19eb8aca).
  Author page advertises a downloadable model, CC Attribution, 148.8k triangles / 74.9k vertices.
  Published November 2024. Actual downloadable file, texture weight, orientation and coverage
  still to inspect. No claim of inclusion in the game yet.
- [Padova Musei, September 2026 laser-scanned Palazzo della Ragione](https://padovamusei.it/it/news/modellino-3d-palazzo-ragione).
  Official museum describes a detailed digital laser scan used for a tactile model.
  The news page does not establish a downloadable asset or reusable license.
- [Municipal cartographic portal](https://www.comune.padova.it/servizi/catasto-e-urbanistica/portale-cartografico-del-piano-degli-interventi-e-del-piano-di).
  Candidate for footprint and urban-planning data; 3D geometry and reuse not yet verified.

## Next searches

Regione Veneto Geoportale / regional topographic database and LiDAR DSM/DTM coverage;
University of Padova photogrammetry collections; author-owned downloadable landmark scans;
Blender glTF workflow and decimation with 3 LODs. Check sources per dataset, not per portal.

## Integration gate

Each imported GLB must include author, exact source, license, expected dimensions and orientation.
Inspect visual fidelity, triangle and texture budgets, ground alignment and collision proxy.
Only V2 assets may change. Never download or extract proprietary viewer tiles as if they
were an unrestricted reusable model. No contact with authors is authorized by this research task.

## Regional data follow-up

- [Regione Veneto: DTM derived from LiDAR](https://idt2.regione.veneto.it/nuovo-dtm-derivato-da-dati-lidar/)
  describes a 5 m terrain product. DTM measures ground: it does not provide
  building roofs or facades. It is a terrain improvement candidate, not a city mesh.
- [Regional download catalogue](https://idt2.regione.veneto.it/idt/downloader/download)
  and [topographic database](https://www.regione.veneto.it/web/ambiente-e-territorio/db-topografico)
  are the next source checks for building footprints and heights. Check the
  individual dataset metadata, actual Padova coverage and license before import.

## Practical asset queue

1. Start with Palazzo della Ragione: obtain the advertised downloadable asset,
   retain the author's attribution, inspect it in Blender, check dimensions,
   normals, missing walls and texture resolution. No model is imported yet.
2. Produce GLB variants with proposed triangle caps of 50k / 15k / 3k, one or two
   materials and a maximum 2048-pixel texture atlas. Preserve the silhouette while
   decimating; do not flatten important arcades into collision walls.
3. Align the model with the existing OSM footprint and authored landmark group.
   Use a separate simple collision proxy, then compare street-level views and
   measured frame cost before making it the default.
4. Repeat for Santo, Scrovegni and Specola only where a reusable asset is available;
   otherwise improve the existing authored landmark against lawful references.

Meanwhile V2 now adds procedural plinths, cornices, window frames, shutters and
some balconies along real OSM footprint edges. These details improve depth but
are invented architectural variation, not a claim to reproduce surveyed facades.
