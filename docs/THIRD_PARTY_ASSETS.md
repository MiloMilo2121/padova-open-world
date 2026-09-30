# Playable asset sources

## Character

[Animated Characters Protagonists by Kenney](https://kenney.nl/assets/animated-characters-protagonists), CC0. Imported `characterMedium.fbx`, `skaterMaleA.png`, and idle/run/jump animations. Original license is in `Assets/Art/Kenney/License.txt`. The skater is a playable fictional character; it is not a reconstruction of a real Padova resident. Derived Unity animation clips remap skeleton paths, and the model is scaled to 1.75 m.

## Surface materials

- [Rectangular Paving by Dimitrios Savva / Poly Haven](https://polyhaven.com/a/rectangular_paving): 1K diffuse and OpenGL normal maps, CC0.
- [Rough Plaster 03 by Rob Tuytel / Poly Haven](https://polyhaven.com/a/rough_plaster_03): 1K diffuse map, CC0.
- [Poly Haven license](https://polyhaven.com/license).

Textures are imported through Unity, mipmapped, and tiled in metric world-space-derived UV coordinates. They are temporary surface materials and **not photographs of the buildings or paving in this district**. This must remain clear until replaced by verified site-specific assets.

The municipality's [Piazza delle Erbe colour-plan sheets](https://www.comune.padova.it/piano-colore-centro-storico/STRADE/ERBE.PDF) and [colour-plan rules](https://www.comune.padova.it/piano-colore-centro-storico/NORME.PDF) document trachyte and local façade/portico treatments. They are research references, not imported game textures. Their photographic content has not been extracted or redistributed.

See `Data/PlayableAssets/manifest.json` for original download URLs and SHA-256 hashes of imported files. Geographic data attribution remains Comune di Padova / Regione del Veneto, DBT 2007, IODL 2.0; see [REAL_WORLD_DATA.md](REAL_WORLD_DATA.md).

## Palazzo della Ragione drawing reference

Didier Descouens, *Exterior of Palazzo della Ragione (Padua).jpg*, 24 May 2017. [Source](https://commons.wikimedia.org/wiki/File:Exterior_of_Palazzo_della_Ragione_(Padua).jpg), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The earlier photo-projection experiment was removed. The current geometric model uses the photograph as a drawing reference for elevation rhythm; the image is not a façade texture in the game. The local research copy is under `.context/architecture/`, outside Git.

## Padova architecture materials (added 2026-09-28)

Poly Haven, CC0 (https://polyhaven.com/license), 2k JPG maps downloaded via api.polyhaven.com into `.context/polyhaven/`, then copied or processed by `Tools/architecture/make_textures.py` into `Assets/Art/Padova/Textures/`:

| Asset | Used as | Source SHA-256 (diffuse) |
| --- | --- | --- |
| roof_09 | Coppi roof tiles | 09c72186e2787dc4b77c21386eb2e2bf0349354af4747c6343c5aa344451601d |
| white_plaster_rough_01 + painted_plaster_wall | Neutral lime plaster (tinted per building) | 194545715b5c03e8715cbedf2f3ae9de164789ad7eb6c7a74a640f6483b0a89d / 6fd812ed8dd5be1873c29aeef38ce9bf1fb30a22c6d4b3a12db725e98c26a1be |
| marble_01 | Istrian stone trims, columns; tinted as trachyte masonry | d403786171716f86718bdd67eba923d4fb6125c0636bacef0e6a21dd5d623a48 |
| medieval_red_brick | Churches, towers, exposed brick | 6115ef3edd7c27a68dce57606ac6050b60313262565dcdc473c9a2ba8fd421e7 |
| herringbone_brick | Courtyards | 3872561d19083dea949277ad77324b1b786a883970d7875e24a835a89b17e51b |
| kloofendal_48d_partly_cloudy_puresky (4k HDR) | Sky, ambient light, reflections | 3061c00a16ecae748e84fd6c44c04804f539c118bb66325db858bad87b11bf88 |

Trachyte paving, sidewalk stone, portico checkerboard, shutters, lead sheeting, the Ragione banded masonry, railing and balustrade textures are generated procedurally by the same script. Landmark names/uses: OpenStreetMap contributors, ODbL 1.0 (`Data/PadovaCentro/osm/landmarks.json`).

The earlier Palazzo della Ragione photographic billboard (Descouens, CC BY-SA 4.0) has been removed from the game. The photograph remains only as a drawing reference in `.context/architecture/`.

## Santo and Prato della Valle landmark models (added 2026-09-29)

These models use only the existing Padova materials above, plus three new ones in `Assets/Art/Landmarks/Materials`:
- canal water and bronze, both flat colours;
- ring balustrade, an original procedurally drawn texture.

Statue and obelisk positions and names: © OpenStreetMap contributors, ODbL 1.0 (snapshot recorded in `Data/Landmarks/sources.json`). Dimensions: Wikipedia it, CC BY-SA.

Wikimedia Commons photographs served as drawing references only and are neither redistributed nor textured:
- *Basilica Di Sant'Antonio di Padova - Facciata.jpg*
- *Basilica di Sant'Antonio di Padova - Cupole.jpg*
- *Basilica di Sant'Antonio di Padova, August 2024.jpg*
- *Prato della Valle - Bridges 01.jpg*
- *Prato della Valle in Padua.JPG*
- *Prato della Valle-Pianta Statue.jpg*

Local copies are in `.context/landmarks-ref/`, outside Git.
