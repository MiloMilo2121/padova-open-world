# Landmark modelling sources

All geometry is anchored to existing DBT 2007 units. These are reference-informed models, not laser scans or measured elevation surveys. No photograph is used as a façade texture. Dimensions not supplied by the DBT are explicitly approximations.

| Landmark | Public evidence | Model and limits |
| --- | --- | --- |
| Torre dell'Orologio | [Municipal museum](https://padovamusei.it/en/node/493) | Units 42159/42143. Modelled gateway, four entrance columns, 24-hour Roman dial, concentric rings, 11 symbolic zodiac markers, corner apertures and top cap. Zodiac glyphs, ornament and dial proportions are simplified, not exact reproductions. Source footprint and maximum elevations retained. |
| Palazzo del Capitanio | [Municipal clock-tower location](https://padovacultura.padovanet.it/en/musei/clock-tower-0) | Southern wing 44273 beside the clock, with pilasters and horizontal stone bands. Northern 44720 is the adjoining Camerlenghi frontage. Window/ornament dimensions are typology, not a measured elevation. |
| Duomo | [Comune di Padova](https://www.comune.padova.it/vivere-il-comune/luoghi/duomo-di-padova), [local tourism office](https://www.turismopadova.it/en/places/duomo-di-padova-cattedrale-di-s-maria-assunta/) | Source dome/lantern units 41276/36949/40598 replace generic roofs. Unfinished brick front, three principal portals and two circular windows. Curvature and façade details are reference-informed approximations inside surveyed limits. |
| Baptistery | [Local tourism office](https://www.turismopadova.it/en/places/cathedral-baptistery/) | Unit 33889: circular drum, pilasters and dome; simplified architectural detail. |
| Palazzo del Bo | [University: Ancient Courtyard](https://www.unipd.it/en/cortile-antico), [New Courtyard](https://heritage.unipd.it/en/bo-cortilenuovo/) | Ancient Courtyard unit 45916 receives a double colonnade and simplified stone shields. The shields do not claim to reproduce individual coats of arms. Other Bo volumes retain institutional typology. The newer courtyard is not confused with the Ancient Courtyard. |

Palazzo della Ragione retains Claude's existing full geometric model and its earlier provenance in `docs/ARCHITECTURE.md`.

## Surroundings and street life

`WorldPlan.json` contains 19,355 additional **volume units**, not 19,355 separate buildings. Original IDs, complete rings, eave values (`QGR - 15`), heights (`AV`) and valid suspended clearances (`INH`) are retained. `manifest.json` records hashes of the original municipal files. Roofs use the same CGAL typology as the core; a 0.10 m simplification applies only to roof construction, never wall outlines or courtyards.

The 3,000 × 2,600 m envelope is local grid metres around the existing origin. Outer ground interpolates nearby nominal base elevations (`QGR - AV`) on a 50 m grid and blends into the existing core over 120 m. This is a navigation approximation, not measured terrain. One low source volume remains below that interpolation; source heights are retained. Street/green/water boundaries are municipal polygons. Source age remains 2007.

The named road network is Regione Veneto WFS `rv:c01070240012_elementostradale`, requested in EPSG:4326 over 11.850,45.390,11.899,45.425. Endpoint: `https://idt2-geoserver.regione.veneto.it/geoserver/wfs`. License: IODL 2.0, as with the regional geographic data. Landmark names also use the existing OpenStreetMap snapshot (ODbL).

6,530 trees are deterministic authored placements inside **surveyed green areas**, not a survey of individual trees. Twelve market stalls, eleven lamps, six benches, pedestrians, cars and aircraft are original game dressing with authored placements. Car locations follow the regional centre lines for Via Dante, Corso Milano and Via Roma. No claim is made that those cars, stalls or lamps occupied those positions in the real city.

Credits: Comune di Padova / Regione del Veneto, DBT 2007 and road network, IODL 2.0; names © OpenStreetMap contributors, ODbL; surface textures/sky Poly Haven CC0; character and three skins Kenney CC0.
