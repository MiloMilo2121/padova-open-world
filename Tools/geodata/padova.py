"""Acquire the public Padova DBT, or rebuild Unity mesh inputs from its pinned subset.

Run with the Python environment described in docs/REAL_WORLD_DATA.md.
Source coordinates/attributes are retained separately from render geometry.
"""
import argparse
import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile

import mapbox_earcut
import numpy as np
import shapefile
from pyproj import Transformer
from shapely.geometry import shape, mapping, box, Polygon, MultiPolygon
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Data/PadovaCentro"
BOUNDS = (11.8705, 45.4057, 11.8779, 45.4093)
ORIGIN = (11.8744, 45.4077)
VERTICAL_ORIGIN = 15.0  # reference offset only; all source elevations are preserved
LAYERS = ("UN_VOL", "AR_STR", "AC_PED", "AR_MARC", "TP_STR")
URL = "https://idt2.regione.veneto.it/idt/download/layerDownload/downloadGeoDBT?" + urllib.parse.urlencode(
    {"lotto": "LOTTO COMUNE DI PADOVA", "rif": "ETRF2000", "type": "aree"})
PROJECT = Transformer.from_crs(6706, 7791, always_xy=True)
E0, N0 = PROJECT.transform(*ORIGIN)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def acquire(archive):
    if not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL, timeout=120) as response:
            archive.write_bytes(response.read())
    region = box(*BOUNDS)
    manifest = {"dataset": "LOTTO COMUNE DI PADOVA", "surveyYear": 2007,
                "downloadUrl": URL, "sourceCrs": "EPSG:6706", "metricCrs": "EPSG:7791",
                "license": "IODL-2.0", "licenseUrl": "https://www.regione.veneto.it/web/ambiente-e-territorio/condizioni-di-utilizzo-geoportale",
                "retrieved": datetime.datetime.now(datetime.timezone.utc).date().isoformat(), "boundsLonLat": BOUNDS,
                "originLonLat": ORIGIN, "originEastingNorthing": [E0, N0],
                "verticalOriginMetres": VERTICAL_ORIGIN, "layers": []}
    with zipfile.ZipFile(archive) as z:
        for layer in LAYERS:
            parts = {ext: z.read(f"ComunePadova_aree/{layer}.{ext}") for ext in ("shp", "shx", "dbf", "prj")}
            reader = shapefile.Reader(**{ext: io.BytesIO(parts[ext]) for ext in ("shp", "shx", "dbf")}, encoding="latin1")
            features = []
            for record in reader.iterShapeRecords(bbox=BOUNDS):
                geometry = record.shape.__geo_interface__
                # Pyshp's geo interface discards Z; restore each ring from the original vertices.
                zs = {tuple(p): float(z) for p, z in zip(record.shape.points, record.shape.z)}
                def restore(coords):
                    if isinstance(coords[0], (int, float)):
                        return [coords[0], coords[1], zs[tuple(coords)]]
                    return [restore(c) for c in coords]
                geometry["coordinates"] = restore(geometry["coordinates"])
                if not shape(geometry).intersects(region):
                    continue
                attrs = record.record.as_dict()
                ident = f"{layer}:{attrs.get('OBJECTID', record.record.oid)}"
                features.append({"type": "Feature", "id": ident, "properties": attrs, "geometry": geometry})
            target = DATA / "source" / f"{layer}.geojson"
            write_json(target, {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "EPSG:6706"}}, "features": features})
            manifest["layers"].append({"name": layer, "features": len(features),
                "sourceFilesSha256": {ext: digest(value) for ext, value in parts.items()},
                "subsetSha256": digest(target.read_bytes()), "sourceWkt": parts["prj"].decode().strip()})
    write_json(DATA / "manifest.json", manifest)


def local(lon, lat, z=None):
    e, n = PROJECT.transform(lon, lat)
    return (e - E0, n - N0) if z is None else (e - E0, n - N0, z)


def polygons(geometry):
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    return [p for g in getattr(geometry, "geoms", []) for p in polygons(g)]


def triangulate(poly):
    rings = [list(poly.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in poly.interiors]
    coords = np.array([v[:2] for r in rings for v in r], dtype=np.float64)
    ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
    indices = mapbox_earcut.triangulate_float64(coords, ends).tolist()
    cross = lambda a, b: a[0] * b[1] - a[1] * b[0]
    area = sum(abs(cross(coords[indices[i+1]] - coords[indices[i]],
                            coords[indices[i+2]] - coords[indices[i]])) / 2 for i in range(0, len(indices), 3))
    if abs(area - poly.area) > max(0.001, poly.area * 1e-7):
        raise ValueError(f"Triangulation changed polygon area: {poly.area} -> {area}")
    # Unity X east, Y up, Z north: reverse any downward-facing triangle.
    for i in range(0, len(indices), 3):
        a, b, c = (coords[indices[i+j]] for j in range(3))
        if cross(b-a, c-a) > 0:
            indices[i+1], indices[i+2] = indices[i+2], indices[i+1]
    return rings, indices


def rebuild():
    manifest = json.loads((DATA / "manifest.json").read_text())
    clip = transform(local, box(*BOUNDS))
    meshes, labels, rejected = [], [], []
    for entry in manifest["layers"]:
        path = DATA / "source" / f"{entry['name']}.geojson"
        if digest(path.read_bytes()) != entry["subsetSha256"]:
            raise ValueError(f"Source hash mismatch: {path}")
        for feature in json.loads(path.read_text())["features"]:
            layer, attrs = entry["name"], feature["properties"]
            geom = transform(local, shape(feature["geometry"]))
            if not geom.is_valid:
                # Do not silently repair cadastral geometry or invent a hull.
                rejected.append({"id": feature["id"], "reason": "Invalid source polygon; retained in source, omitted from scene"})
                continue
            if layer == "TP_STR":
                geom = geom.intersection(clip)
                if not geom.is_empty and geom.area > 4:
                    point = geom.representative_point()
                    labels.append({"id": feature["id"], "name": attrs["TP_STR_SNO"], "x": point.x, "z": point.y})
                continue
            volume = layer == "UN_VOL"
            if not volume:
                geom = geom.intersection(clip)
            top = float(attrs.get("UN_VOL_QGR", 0))
            height = float(attrs.get("UN_VOL_AV", 0))
            portion = attrs.get("UN_VOL_POR", "")
            if volume and not (0 < height < 150 and top > height):
                rejected.append({"id": feature["id"], "reason": "Missing or invalid elevation; no height invented"})
                continue
            for index, poly in enumerate(polygons(geom)):
                if poly.area < 0.01:
                    continue
                rings, triangles = triangulate(poly)
                coordinates = [v for ring in rings for v in ring]
                # Eave caps are explicitly cartographic planes, never claimed to be roof meshes.
                vertices = [[v[0], (top if volume else v[2]) - VERTICAL_ORIGIN, v[1]] for v in coordinates]
                # Portico/overhang clearance is not supplied: leave these as caps rather than seal the passages.
                walls = volume and portion == "01"
                if walls:
                    for ring in rings:
                        for a, b in zip(ring, ring[1:] + ring[:1]):
                            start = len(vertices)
                            vertices.extend([[a[0], top-height-VERTICAL_ORIGIN, a[1]],
                                             [b[0], top-height-VERTICAL_ORIGIN, b[1]],
                                             [b[0], top-VERTICAL_ORIGIN, b[1]],
                                             [a[0], top-VERTICAL_ORIGIN, a[1]]])
                            # Double-sided in material: source ring winding is retained.
                            triangles.extend([start, start+1, start+2, start, start+2, start+3])
                centre = poly.representative_point()
                meshes.append({"id": feature["id"] + f":{index}", "sourceId": feature["id"],
                    "layer": layer, "portion": portion, "area": poly.area,
                    "eave": top, "height": height, "walls": walls,
                    "x": centre.x, "z": centre.y,
                    "vertices": [{"x": round(v[0], 4), "y": round(v[1], 4), "z": round(v[2], 4)} for v in vertices],
                    "triangles": triangles})
    output = {"schemaVersion": 1, "sourceYear": 2007, "originEasting": E0, "originNorthing": N0,
              "verticalOrigin": VERTICAL_ORIGIN, "meshes": meshes, "labels": labels}
    write_json(DATA / "derived" / "district.json", output)
    report = {"meshes": len(meshes), "buildingVolumes": sum(m["layer"] == "UN_VOL" for m in meshes),
              "porticoOrOverhangCaps": sum(m["layer"] == "UN_VOL" and not m["walls"] for m in meshes),
              "surfacePolygons": sum(m["layer"] != "UN_VOL" for m in meshes),
              "triangles": sum(len(m["triangles"])//3 for m in meshes),
              "labels": len(labels), "rejected": rejected,
              "districtSha256": digest((DATA / "derived" / "district.json").read_bytes())}
    write_json(DATA / "validation.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquire", action="store_true", help="Explicitly refresh source snapshots before rebuilding")
    parser.add_argument("--archive", type=Path, default=ROOT / ".context/geodata/padova-aree.zip")
    args = parser.parse_args()
    if args.acquire:
        acquire(args.archive)
    rebuild()
