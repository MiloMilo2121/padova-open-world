"""Extract the municipal survey evidence used by the Blender landmark models.

Usage: extract_sources.py [slug ...]   (default: every slug in EXTRACTORS; other keys are kept)

Writes Data/Landmarks/sources.json: the exact DBT 2007 records (local metres, Y = Z - 15)
for the Basilica del Santo and Prato della Valle, plus the WorldPlan ground model so the
Blender generator can seat geometry on the same surface the game uses. Nothing here is
modelled or regularised; Tools/blender/build_landmarks.py reads only this file.
Run with the geo venv: .context/geo-venv/bin/python Tools/landmarks/extract_sources.py
"""
import hashlib
import json
import sys
from pathlib import Path

import mapbox_earcut
import numpy as np
import shapefile
from shapely.geometry import shape, box
from shapely.geometry.polygon import orient
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Tools/geodata"))
import padova  # noqa: E402

SURVEY = ROOT / ".context/geodata/padova-dbt"
OUT = ROOT / "Data/Landmarks/sources.json"
WORLD = ROOT / "Data/World/WorldPlan.json"

# Church volume units read from the DBT plan (see Data/Landmarks/README.md for roles).
SANTO_UNITS = {
    "UN_VOL:30694": "body", "UN_VOL:30788": "front", "UN_VOL:30877": "ambulatory", "UN_VOL:30982": "chapels",
    "UN_VOL:30785": "aisle", "UN_VOL:33179": "aisle", "UN_VOL:30521": "aisle", "UN_VOL:23920": "aisle",
    "UN_VOL:31103": "annex",
    "UN_VOL:30619": "dome", "UN_VOL:26182": "dome", "UN_VOL:30736": "cone", "UN_VOL:30849": "dome",
    "UN_VOL:23960": "dome", "UN_VOL:30759": "dome", "UN_VOL:25375": "dome", "UN_VOL:24007": "treasury",
    "UN_VOL:30830": "campanile", "UN_VOL:30659": "campanile", "UN_VOL:23928": "turret", "UN_VOL:26860": "turret",
    "UN_VOL:85827": "pier", "UN_VOL:85828": "pier", "UN_VOL:85829": "pier", "UN_VOL:85830": "pier",
    "UN_VOL:85831": "pier", "UN_VOL:85832": "pier", "UN_VOL:30718": "pier", "UN_VOL:19872": "pier",
    "UN_VOL:30045": "pier",
}
PRATO_AREA = box(90, -1180, 320, -860)
FOUNTAIN_AREA = box(190, -1035, 215, -1010)
GATTAMELATA_AREA = box(490, -675, 505, -660)
CELL = 25  # WorldContext surrounding-ground cell size; Prato ground replaces whole cells
OSM = ROOT / ".context/landmarks/prato-osm.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(layer, area):
    reader = shapefile.Reader(str(SURVEY / (layer + ".shp")), encoding="latin1")
    for record in reader.iterShapeRecords():
        geom = transform(lambda x, y, z=None: padova.local(x, y), shape(record.shape.__geo_interface__))
        if geom.intersects(area):
            zs = list(record.shape.z) if hasattr(record.shape, "z") else []
            yield record, geom, zs


def ring(poly):
    poly = orient(poly, 1)
    return [[round(x, 3), round(y, 3)] for x, y in list(poly.exterior.coords)[:-1]]


def rings_of(poly):
    poly = orient(poly, 1)
    return [list(poly.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in poly.interiors]


def triangulate(poly):
    rs = rings_of(poly)
    coords = np.array([v[:2] for r in rs for v in r], dtype=np.float64)
    ends = np.cumsum([len(r) for r in rs]).astype(np.uint32)
    tris = mapbox_earcut.triangulate_float64(coords, ends).tolist()
    return [round(float(v), 3) for v in coords.ravel()], tris


def osm_points(transformer):
    """OpenStreetMap artwork/obelisk/fountain points (ODbL): identity and approximate position only."""
    if not OSM.exists():
        return []
    points = []
    for e in json.loads(OSM.read_text())["elements"]:
        tags = e.get("tags") or {}
        if e["type"] != "node" or not tags:
            continue
        x, z = transformer(e["lon"], e["lat"])
        kind = tags.get("artwork_type") or tags.get("man_made") or tags.get("amenity") or tags.get("historic")
        points.append({"id": "node/" + str(e["id"]), "ref": tags.get("ref", ""), "kind": kind, "name": tags.get("name", ""),
                       "x": round(x, 3), "z": round(z, 3)})
    return points


def world_units(world, ids):
    """Copy WorldPlan units (already DBT-derived) with their survey attributes; role is caller metadata."""
    units = {u["id"]: u for u in world["units"]}
    return [{"id": fid, "role": role, "ground": units[fid]["ground"], "top": units[fid]["top"], "base": units[fid]["surveyBase"],
             "height": units[fid]["surveyHeight"], "cx": units[fid]["cx"], "cz": units[fid]["cz"], "area": units[fid]["area"],
             "outline": units[fid]["outline"], "ringSizes": units[fid]["ringSizes"]} for fid, role in ids.items()]


def ground_cells_minus(world, hole):
    """Whole WorldContext ground cells (CELL m) around `hole`, re-cut so the landmark can own that ground."""
    x0, z0 = world["extent"][0], world["extent"][1]
    minx, minz, maxx, maxz = hole.buffer(3).bounds
    i0, i1 = int((minx - x0) // CELL), int((maxx - x0) // CELL) + 1
    j0, j1 = int((minz - z0) // CELL), int((maxz - z0) // CELL) + 1
    parts = []
    for i in range(i0, i1):
        for j in range(j0, j1):
            rest = box(x0 + i * CELL, z0 + j * CELL, x0 + (i + 1) * CELL, z0 + (j + 1) * CELL).difference(hole)
            for poly in getattr(rest, "geoms", [rest]):
                if poly.area > 1e-4:
                    v, t = triangulate(poly)
                    parts.append({"v": v, "t": t})
    return [x0 + i0 * CELL, z0 + j0 * CELL, x0 + i1 * CELL, z0 + j1 * CELL], parts


def extract_santo(world):
    gattamelata = None
    for rec, geom, zs in read("MN_UVOL", GATTAMELATA_AREA):
        p = rec.record.as_dict()
        gattamelata = {"id": "MN_UVOL:" + str(rec.record.oid), "outline": ring(geom), "surveyTop": round(p["MN_UVO_QGR"] - 15, 3),
                       "surveyHeight": p["MN_UVO_ALT"]}
    return {"units": world_units(world, SANTO_UNITS), "gattamelata": gattamelata}, ["UN_VOL", "MN_UVOL"]


def extract_prato(world):
    canal, bridges, fountain = [], [], None
    for rec, geom, zs in read("AB_CDA", PRATO_AREA):
        if geom.area < 100 or rec.record.as_dict()["AB_CDA_TY"] != "51":
            continue
        canal.append({"id": "AB_CDA:" + str(rec.record.oid), "outline": ring(geom),
                      "waterZ": [round(min(zs) - 15, 3), round(max(zs) - 15, 3)]})
    for rec, geom, zs in read("PONTE", PRATO_AREA):
        pts = [padova.local(lon, lat) + (z - 15,) for (lon, lat), z in zip(rec.shape.points, zs)][:-1]
        if sum((b[0] - a[0]) * (b[1] + a[1]) for a, b in zip(pts, pts[1:] + pts[:1])) > 0:
            pts.reverse()  # counter-clockwise, as the other rings
        bridges.append({"id": "PONTE:" + str(rec.record.oid), "outline": [[round(x, 3), round(z, 3), round(y, 3)] for x, z, y in pts],
                        "deckZ": [round(min(zs) - 15, 3), round(max(zs) - 15, 3)]})
    for rec, geom, zs in read("MN_EDI_NOVOL", FOUNTAIN_AREA):
        fountain = {"id": "MN_EDI_NOVOL:" + str(rec.record.oid), "category": rec.record.as_dict()["MNNV_CAT"],
                    "outline": ring(geom), "z": [round(min(zs) - 15, 3), round(max(zs) - 15, 3)]}
    # Surveyed canal = union of the arc and under-bridge water polygons: one annulus.
    water = unary_union([shape({"type": "Polygon", "coordinates": [c["outline"]]}) for c in canal]).buffer(0)
    annulus = max(getattr(water, "geoms", [water]), key=lambda g: g.area)
    wv, wt = triangulate(annulus)
    rect, ground_parts = ground_cells_minus(world, annulus)
    return {"canal": canal, "bridges": bridges, "fountain": fountain,
            "canalOuter": [[round(x, 3), round(y, 3)] for x, y in rings_of(annulus)[0]],
            "canalInner": [[round(x, 3), round(y, 3)] for x, y in rings_of(annulus)[1]],
            "water": {"v": wv, "t": wt},
            "waterLevel": round(float(np.median([z for c in canal for z in c["waterZ"]])), 3),
            "groundRect": rect, "ground": ground_parts,
            "osm": osm_points(padova.local)}, ["AB_CDA", "PONTE", "MN_EDI_NOVOL"]  # WGS84 read as RDN2008: sub-metre


# Register new landmarks here: slug -> function(world) returning (evidence dict, DBT layers read).
EXTRACTORS = {"santo": extract_santo, "prato": extract_prato}


def main(slugs):
    world = json.loads(WORLD.read_text())
    out = json.loads(OUT.read_text()) if OUT.exists() else {"schema": 2, "sourceSha256": {}}
    out.update({"schema": 2, "attribution": "Comune di Padova / Regione del Veneto, DBT 2007, IODL 2.0.",
                "note": "Local grid metres (X east, Z north); Y is source elevation minus 15 m. One key per landmark slug.",
                "worldPlanSha256": sha(WORLD),
                "ground": {k: world[k] for k in ["extent", "plane", "coreExtent", "terrain", "terrainStep", "terrainNX", "terrainNZ"]}})
    for slug in slugs or list(EXTRACTORS):
        evidence, layers = EXTRACTORS[slug](world)
        out[slug] = evidence
        out["sourceSha256"].update({layer: sha(SURVEY / (layer + ".shp")) for layer in layers})
        print(slug, {k: (len(v) if isinstance(v, list) else bool(v)) for k, v in evidence.items()})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
