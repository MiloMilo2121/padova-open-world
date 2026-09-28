"""Plan Padova's architecture from the municipal survey for the Unity city builder.

Evidence used, per element:
- Footprints, courtyards, eave elevations (UN_VOL_QGR) and heights (UN_VOL_AV): Comune di Padova DBT 2007.
- Porticoes: DBT "suspended" units (UN_VOL_POR 03/02) and their surveyed underside height (UN_VOL_INH).
- Street, pedestrian and sidewalk areas: DBT AR_STR / AC_PED / AR_MARC.
- Landmark identity (name, church/theatre use, Palazzo della Ragione's 35 m height): OpenStreetMap, ODbL.
- Hipped roofs: CGAL straight skeleton of each surveyed footprint at the Veneto coppi pitch. The survey
  records no ridge heights (UN_VOL_QCO is 0), so roof pitch is a regional typology, flagged as such.

The output is a compact plan (outlines, exposure intervals, roof triangles). Unity expands façade
detail from it at load time, so no multi-megabyte generated meshes are stored in Git.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import mapbox_earcut
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon, box, shape
from shapely.geometry.polygon import orient
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Tools/geodata"))
import padova  # noqa: E402

OUT = ROOT / "Assets/Geography/PadovaCentro/CityPlan.json"
OSM = ROOT / "Data/PadovaCentro/osm/landmarks.json"
SKELETON_SRC = Path(__file__).with_name("roof_skeleton.cpp")
SKELETON_BIN = ROOT / ".context/bin/roof_skeleton"
ROOF_SLOPE = 0.34          # ~19 degrees: Veneto coppi roofs (30-36 % slope); typology, not survey
TOWER_SLOPE = 1.1
CHURCH_SLOPE = 0.45
OVERHANG = 0.75            # eave projection on exposed edges
MERGE_TOLERANCE = 0.35     # neighbouring eaves within survey precision share one roof
SAMPLE = 0.9
PROBE = 0.35
PLANE = json.loads((padova.DATA / "derived/walk-surface.json").read_text())["plane"]
STREET, UPPER, PORTICO_BACK, BLANK, ARCADE = range(5)
RAGIONE = {"hall": ["UN_VOL:50321", "UN_VOL:43684", "UN_VOL:47642"],
           "north_loggia": ["UN_VOL:47695", "UN_VOL:47699"], "south_loggia": ["UN_VOL:45910", "UN_VOL:45915"],
           "north_shops": ["UN_VOL:47702"], "south_shops": ["UN_VOL:45907"]}


def ground(x, z):
    return PLANE[0] * x + PLANE[1] * z + PLANE[2]


def r3(v):
    return round(float(v), 3)


def polys(g):
    return [orient(p, 1.0) for p in padova.polygons(g) if p.area > 0.5]


def clean(poly, tolerance=0.08):
    p = orient(poly.buffer(0).simplify(tolerance, preserve_topology=True), 1.0)
    if isinstance(p, MultiPolygon):
        p = max(p.geoms, key=lambda q: q.area)
    return p


def rings(poly):
    return [list(poly.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in poly.interiors]


def earcut(poly):
    rs = rings(poly)
    coords = np.array([v[:2] for r in rs for v in r], dtype=np.float64)
    ends = np.cumsum([len(r) for r in rs]).astype(np.uint32)
    return coords, mapbox_earcut.triangulate_float64(coords, ends).tolist()


# ---------------------------------------------------------------- landmarks (OpenStreetMap)
def load_landmarks():
    """Named buildings/uses from OSM (ODbL). Only identity/use is taken; geometry stays the DBT's."""
    if OSM.exists():
        return [(e["name"], e["building"], Polygon(e["outline"])) for e in json.loads(OSM.read_text())["buildings"]]
    raw = json.loads((ROOT / ".context/osm/buildings.json").read_text())
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in raw["elements"] if e["type"] == "node"}
    ways = {e["id"]: e for e in raw["elements"] if e["type"] == "way"}
    out = []
    for e in raw["elements"]:
        tags = e.get("tags", {})
        if e["type"] not in ("way", "relation") or "name" not in tags:
            continue
        members = [e] if e["type"] == "way" else [ways[m["ref"]] for m in e["members"]
                                                  if m["type"] == "way" and m.get("role") == "outer" and m["ref"] in ways]
        parts = []
        for w in members:
            pts = [padova.local(*nodes[n]) for n in w["nodes"] if n in nodes]
            if len(pts) >= 4 and Polygon(pts).is_valid:
                parts.append(Polygon(pts))
        if not parts:
            continue
        outline = unary_union(parts)
        outline = max(padova.polygons(outline), key=lambda p: p.area)
        out.append({"name": tags["name"], "building": tags.get("building", "yes"), "osm": f"{e['type']}/{e['id']}",
                    "height": tags.get("height"), "outline": [[r3(x), r3(z)] for x, z in outline.exterior.coords]})
    OSM.parent.mkdir(parents=True, exist_ok=True)
    OSM.write_text(json.dumps({"source": "OpenStreetMap contributors, https://www.openstreetmap.org/copyright",
                               "license": "ODbL-1.0", "retrieved": "2026-09-28",
                               "use": "Names and building use only; geometry and heights come from the Comune di Padova DBT.",
                               "buildings": out}, ensure_ascii=False, indent=1) + "\n")
    return [(e["name"], e["building"], Polygon(e["outline"])) for e in out]


# ---------------------------------------------------------------- survey units
class Unit:
    def __init__(self, fid, poly, props):
        self.id = fid
        self.raw = poly
        self.poly = clean(poly)
        self.por = props["UN_VOL_POR"]
        self.top = props["UN_VOL_QGR"] - padova.VERTICAL_ORIGIN
        self.height = props["UN_VOL_AV"]
        c = self.poly.representative_point()
        self.cx, self.cz = c.x, c.y
        self.ground = ground(c.x, c.y)
        inh = props["UN_VOL_INH"]
        # Suspended units span a surveyed void (portico/passage) from ground to their underside.
        self.suspended = self.por in ("02", "03") and 2.0 < inh < self.top - self.ground - 1.5
        self.under = self.ground + inh if self.suspended else None
        self.name, self.use = "", ""
        self.group = None
        self.roof_top = self.top

    def solid(self):
        return (self.under if self.suspended else -math.inf, self.roof_top)


def load_units(landmarks):
    features = json.loads((padova.DATA / "source/UN_VOL.geojson").read_text())["features"]
    units = []
    for f in features:
        p = f["properties"]
        if not (0 < p["UN_VOL_AV"] < 150 and p["UN_VOL_QGR"] > p["UN_VOL_AV"]):
            continue
        g = transform(padova.local, shape(f["geometry"]))
        if not g.is_valid:
            continue
        for i, poly in enumerate(polys(g)):
            if poly.area < 2:
                continue
            u = Unit(f["id"] + ("" if i == 0 else f"#{i}"), poly, p)
            if u.poly.area < 1.5:
                continue
            units.append(u)
    for name, use, outline in landmarks:
        for u in units:
            if u.raw.intersects(outline) and u.raw.intersection(outline).area > 0.5 * u.raw.area:
                u.name, u.use = name, use
                if name == "Palazzo della Ragione":
                    # Its covered external stairs carry INH values above the stair roof; keep them solid.
                    u.suspended, u.under = False, None
    return units


def merge_roof_groups(units, tree):
    """Adjacent units whose eaves agree within survey precision share one continuous roof."""
    parent = list(range(len(units)))
    lo = [u.top for u in units]
    hi = [u.top for u in units]

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, u in enumerate(units):
        if u.name == "Palazzo della Ragione":
            continue
        for j in tree.query(u.raw.buffer(0.05)):
            v = units[j]
            if j <= i or v.name == "Palazzo della Ragione" or abs(u.top - v.top) > MERGE_TOLERANCE:
                continue
            if tower(u) != tower(v) or (u.use == "church") != (v.use == "church"):
                continue
            if u.raw.buffer(0.05).intersection(v.raw.buffer(0.05)).length > 0 or u.raw.distance(v.raw) < 0.05:
                shared = u.raw.buffer(0.08).intersection(v.raw.buffer(0.08)).area
                a, b = find(i), find(j)
                # Never let chained neighbours stretch a shared roof beyond survey tolerance.
                if shared > 0.4 and a != b and max(hi[a], hi[b]) - min(lo[a], lo[b]) <= MERGE_TOLERANCE:
                    parent[a] = b
                    lo[b], hi[b] = min(lo[a], lo[b]), max(hi[a], hi[b])
    groups = {}
    for i, u in enumerate(units):
        groups.setdefault(find(i), []).append(u)
    for members in groups.values():
        top = max(m.top for m in members)
        for m in members:
            m.roof_top = top
            m.group = members
    return list(groups.values())


def tower(u):
    return u.poly.area < 140 and u.top - u.ground > 24 and (u.top - u.ground) / math.sqrt(u.poly.area) > 2.4


# ---------------------------------------------------------------- exposure of every wall
def subtract(interval, covers):
    lo, hi = interval
    out = []
    for a, b in sorted(covers):
        if b <= lo or a >= hi:
            continue
        if a > lo:
            out.append((lo, min(a, hi)))
        lo = max(lo, b)
        if lo >= hi:
            break
    if lo < hi:
        out.append((lo, hi))
    return [(a, b) for a, b in out if b - a > 0.15]


def exposure_segments(u, units, tree, walkable):
    """Split each outline edge by what lies outside it at every height."""
    segs = []
    s0, s1 = u.solid()
    for ring in rings(u.poly):
        for a, b in zip(ring, ring[1:] + ring[:1]):
            a, b = np.array(a[:2]), np.array(b[:2])
            d = b - a
            length = float(np.hypot(*d))
            if length < 0.25:
                continue
            e = d / length
            n = np.array([e[1], -e[0]])  # outward for CCW exterior and CW holes
            count = max(2, int(math.ceil(length / SAMPLE)))
            states = []
            for k in range(count):
                t = (k + 0.5) / count
                p = a + d * t + n * PROBE
                pt = Point(*p)
                covers, ground_neighbour, void_neighbour, top_covered = [], False, False, False
                for j in tree.query(pt):
                    v = units[j]
                    if v is u or not v.raw.contains(pt):
                        continue
                    lo, hi = v.solid()
                    covers.append((lo, hi))
                    if lo == -math.inf:
                        ground_neighbour = True
                    else:
                        void_neighbour = True
                exposed = subtract((s0, s1), covers)
                street = walkable.contains(pt)
                arcade = u.suspended and not ground_neighbour and not void_neighbour
                key = (tuple((round(lo, 1) if lo != -math.inf else -999, round(hi, 1)) for lo, hi in exposed),
                       arcade, street)
                states.append((t, key, exposed))
            start = 0
            for k in range(1, count + 1):
                if k < count and states[k][1] == states[start][1]:
                    continue
                t0 = 0.0 if start == 0 else (states[start - 1][0] + states[start][0]) / 2
                t1 = 1.0 if k == count else (states[k - 1][0] + states[k][0]) / 2
                p0, p1 = a + d * t0, a + d * t1
                _, (_, arcade, street), exposed = states[start]
                flags_base = 0 if street else 2  # bit1: faces a courtyard/private space
                for lo, hi in exposed:
                    reaches_top = hi >= s1 - 0.05
                    flags = flags_base | (1 if reaches_top else 0)
                    if lo == -math.inf:
                        y0 = u.ground - 0.4
                        if reaches_top:
                            kind = STREET
                        else:
                            kind = PORTICO_BACK if hi - u.ground > 2.2 else BLANK
                    else:
                        y0 = lo
                        if reaches_top and hi - lo >= 2.6:
                            kind = UPPER
                            if u.suspended and abs(lo - u.under) < 0.05:
                                flags |= 4  # façade carried by the portico below
                        else:
                            kind = BLANK
                    segs.append([p0[0], p0[1], p1[0], p1[1], y0, hi, kind, flags])
                if arcade:
                    segs.append([p0[0], p0[1], p1[0], p1[1], u.ground, u.under, ARCADE, flags_base])
                start = k
    return segs


# ---------------------------------------------------------------- roofs
def skeleton_binary():
    if not SKELETON_BIN.exists() or SKELETON_BIN.stat().st_mtime < SKELETON_SRC.stat().st_mtime:
        SKELETON_BIN.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["clang++", "-std=c++17", "-O2", "-I/opt/homebrew/include", str(SKELETON_SRC),
                        "-L/opt/homebrew/lib", "-lgmp", "-lmpfr", "-o", str(SKELETON_BIN)], check=True)
    return SKELETON_BIN


def run_skeletons(shapes):
    lines = [str(len(shapes))]
    for key, poly in shapes:
        rs = rings(poly)
        lines.append(f"{key} {len(rs)}")
        for i, r in enumerate(rs):
            pts = r if i == 0 else r  # shapely orient(): exterior CCW, holes CW
            lines.append(f"{len(pts)} " + " ".join(f"{x:.4f} {z:.4f}" for x, z, *_ in pts))
    out = subprocess.run([str(skeleton_binary())], input="\n".join(lines) + "\n", capture_output=True,
                         text=True, check=True, timeout=600).stdout.split("\n")
    result, i = {}, 0
    while i < len(out):
        head = out[i].split()
        i += 1
        if len(head) < 2:
            continue
        if head[1] == "FAIL":
            result[head[0]] = None
            continue
        faces = []
        for _ in range(int(head[1])):
            vals = list(map(float, out[i].split()))
            i += 1
            faces.append(np.array(vals[1:]).reshape(-1, 3))
        result[head[0]] = faces
    return result


def roof_mesh(poly, faces, base, slope, exposed_edge):
    """Roof tiles (with eave overhang on exposed edges) plus fascia/soffit geometry."""
    tv, tt, wv, wt = [], [], [], []
    cos = 1 / math.sqrt(1 + slope * slope)
    for face in faces:
        zero = [k for k in range(len(face)) if face[k, 2] < 1e-6]
        if len(zero) < 2:
            continue
        # Defining contour edge: consecutive zero-time vertices, oriented CCW.
        m = len(face)
        pair = next(((zero[k], zero[(k + 1) % len(zero)]) for k in range(len(zero))
                     if (zero[(k + 1) % len(zero)] - zero[k]) % m == 1), None)
        if pair is None:
            continue
        a, b = face[pair[0], :2], face[pair[1], :2]
        edge = b - a
        length = float(np.hypot(*edge))
        if length < 1e-4:
            continue
        e = edge / length
        inward = np.array([-e[1], e[0]])
        pts2 = face[:, :2]
        try:
            idx = mapbox_earcut.triangulate_float64(pts2.astype(np.float64), np.array([m], dtype=np.uint32)).tolist()
        except Exception:
            continue
        start = len(tv) // 5
        for (x, z, t) in face:
            p = np.array([x, z])
            tv += [x, base + t * slope, z, float(np.dot(p - a, e)), float(np.dot(p - a, inward)) / cos]
        for k in range(0, len(idx), 3):
            tt += [start + idx[k], start + idx[k + 2], start + idx[k + 1]]  # upward winding for Unity
        if exposed_edge(a, b):
            o = OVERHANG
            outward = -inward
            drop = o * slope
            qa, qb = a + outward * o, b + outward * o
            s = len(tv) // 5
            for p, y, v in ((a, base, 0.0), (b, base, 0.0), (qb, base - drop, -o / cos), (qa, base - drop, -o / cos)):
                tv += [p[0], y, p[1], float(np.dot(p - a, e)), v]
            tt += [s, s + 1, s + 2, s, s + 2, s + 3]
            # Corner fans so neighbouring overhangs meet at convex corners.
            for corner, sign in ((a, -1), (b, 1)):
                qc = corner + outward * o + e * o * sign
                qe = corner + outward * o
                s = len(tv) // 5
                for p, y in ((corner, base), (qe, base - drop), (qc, base - drop)):
                    tv += [p[0], y, p[1], float(np.dot(p - a, e)), float(np.dot(p - a, inward)) / cos]
                tt += [s, s + 2, s + 1] if sign < 0 else [s, s + 1, s + 2]
            # Fascia board and soffit in wood.
            s = len(wv) // 5
            fy = base - drop
            for p, y in ((qa, fy), (qb, fy), (qb, fy - 0.2), (qa, fy - 0.2)):
                wv += [p[0], y, p[1], float(np.dot(p - a, e)), y]
            wt += [s, s + 1, s + 2, s, s + 2, s + 3]  # faces outward (Unity clockwise front faces)
            s = len(wv) // 5
            for p, y in ((a, base - 0.25), (b, base - 0.25), (qb, fy - 0.2), (qa, fy - 0.2)):
                wv += [p[0], y, p[1], float(np.dot(p - a, e)), float(np.dot(p - a, outward))]
            wt += [s, s + 2, s + 1, s, s + 3, s + 2]  # soffit faces down
    return tv, tt, wv, wt


# ---------------------------------------------------------------- ground
def load_layer(name, clip):
    out = []
    for f in json.loads((padova.DATA / "source" / f"{name}.geojson").read_text())["features"]:
        g = transform(padova.local, shape(f["geometry"]))
        if g.is_valid:
            out.append(g.intersection(clip))
    return unary_union(out)


def ground_plan(units, extent, clip):
    solid = unary_union([u.raw for u in units if not u.suspended]).buffer(0)
    portico = unary_union([u.raw for u in units if u.suspended]).buffer(0).difference(solid)
    sidewalk = load_layer("AR_MARC", clip).difference(solid).difference(portico)
    road = load_layer("AR_STR", clip).difference(solid).difference(portico).difference(sidewalk)
    piazza = load_layer("AC_PED", clip).difference(solid).difference(portico).difference(sidewalk).difference(road)
    open_inside = clip.difference(solid).difference(portico).difference(sidewalk).difference(road).difference(piazza)
    outside = extent.difference(clip).difference(solid).difference(portico)
    classes = [("road", 0.0, road), ("piazza", 0.0, piazza), ("sidewalk", 0.12, sidewalk),
               ("portico", 0.14, portico), ("courtyard", 0.02, open_inside), ("outer", 0.0, outside)]
    patches, curbs = [], []
    level_regions = []
    for name, level, geom in classes:
        for poly in polys(geom.buffer(0)):
            if poly.area < 0.3:
                continue
            poly = orient(poly.simplify(0.03, preserve_topology=True), 1.0)
            if not poly.is_valid or poly.area < 0.3:
                continue
            coords, idx = earcut(poly)
            patches.append({"mat": name, "level": level,
                            "v": [r3(c) for xy in coords for c in xy],
                            "t": [idx[k + j] for k in range(0, len(idx), 3) for j in (0, 2, 1)]})
            level_regions.append((poly, level))
    # Curbs: vertical faces where a raised surface meets a lower one.
    tree = STRtree([p for p, _ in level_regions])
    for poly, level in level_regions:
        if level < 0.05:
            continue
        for ring in rings(poly):
            for a, b in zip(ring, ring[1:] + ring[:1]):
                a, b = np.array(a[:2]), np.array(b[:2])
                length = float(np.hypot(*(b - a)))
                if length < 0.05:
                    continue
                e = (b - a) / length
                n = np.array([e[1], -e[0]])
                probe = Point(*((a + b) / 2 + n * 0.15))
                other = [level_regions[j][1] for j in tree.query(probe) if level_regions[j][0].contains(probe)]
                low = min(other) if other else None
                if low is not None and low < level - 0.05:
                    curbs += [r3(a[0]), r3(a[1]), r3(b[0]), r3(b[1]), r3(low), r3(level)]
    return patches, curbs


# ---------------------------------------------------------------- Palazzo della Ragione frame
def ragione_frame(units):
    by_id = {u.id: u for u in units}
    hall = unary_union([by_id[i].raw for i in RAGIONE["hall"]])
    rect = np.array(hall.minimum_rotated_rectangle.exterior.coords)[:4, :2]
    edges = [rect[(i + 1) % 4] - rect[i] for i in range(4)]
    long_i = int(np.argmax([np.hypot(*e) for e in edges]))
    axis = edges[long_i] / np.hypot(*edges[long_i])
    if axis[0] < 0:
        axis = -axis
    north = np.array([-axis[1], axis[0]])  # left of the east-pointing axis: roughly north
    c = rect.mean(axis=0)

    def extent(ids):
        pts = np.vstack([np.array(by_id[i].raw.exterior.coords)[:, :2] for i in ids])
        rel = pts - c
        return [r3(np.min(rel @ axis)), r3(np.max(rel @ axis)), r3(np.min(rel @ north)), r3(np.max(rel @ north))]
    def gap(ids):
        spans = sorted(extent([i]) for i in ids)
        return r3((spans[0][1] + spans[1][0]) / 2) if len(spans) > 1 else 0.0
    frame = {"cx": r3(c[0]), "cz": r3(c[1]), "ax": r3(axis[0]), "az": r3(axis[1]), "ground": r3(ground(*c)),
             "hall": extent(RAGIONE["hall"]), "northLoggia": extent(RAGIONE["north_loggia"]),
             "southLoggia": extent(RAGIONE["south_loggia"]), "northShops": extent(RAGIONE["north_shops"]),
             "southShops": extent(RAGIONE["south_shops"]),
             "northGap": gap(RAGIONE["north_loggia"]), "southGap": gap(RAGIONE["south_loggia"]),
             "hallEave": r3(by_id["UN_VOL:47642"].top), "loggiaEave": r3(by_id["UN_VOL:47695"].top),
             "shopEave": r3(by_id["UN_VOL:47702"].top),
             # OSM way 29494033 records height=35 m for the hull roof.
             "ridge": r3(ground(*c) + 35.0),
             "sources": "Footprint and eaves: DBT units " + ", ".join(sum(RAGIONE.values(), [])) +
                        "; ridge: OSM height 35 m; elevation rhythm: Descouens 2017 photograph (CC BY-SA 4.0) used as a drawing reference only."}
    return frame, set(sum(RAGIONE.values(), []))


def main():
    landmarks = load_landmarks()
    units = load_units(landmarks)
    clip = transform(padova.local, box(*padova.BOUNDS))
    minx, minz, maxx, maxz = unary_union([u.raw for u in units]).bounds
    extent = box(minx - 40, minz - 40, maxx + 40, maxz + 40)
    tree = STRtree([u.raw for u in units])
    groups = merge_roof_groups(units, tree)
    walkable = unary_union([load_layer(n, clip) for n in ("AR_STR", "AC_PED", "AR_MARC")]).buffer(0.2)
    frame, ragione_ids = ragione_frame(units)
    special = {u.id for u in units if u.id in ragione_ids}

    plan_units = []
    for u in units:
        if u.id in special:
            continue
        segs = exposure_segments(u, units, tree, walkable)
        coords, idx = earcut(u.poly) if u.suspended else (None, None)
        plan_units.append({
            "id": u.id, "name": u.name, "use": "tower" if tower(u) else u.use, "suspended": u.suspended,
            "ground": r3(u.ground), "top": r3(u.roof_top), "surveyTop": r3(u.top),
            "under": r3(u.under) if u.suspended else 0.0, "area": r3(u.poly.area),
            "cx": r3(u.cx), "cz": r3(u.cz),
            "outline": [r3(c) for r in rings(u.poly) for x, z, *_ in r for c in (x, z)],
            "ringSizes": [len(r) for r in rings(u.poly)],
            "segs": [r3(v) if k % 8 < 6 else int(v) for s in segs for k, v in enumerate(s)],
            "ceiling": [r3(c) for xy in coords for c in xy] if u.suspended else [],
            "ceilingTris": [idx[k + j] for k in range(0, len(idx), 3) for j in (0, 1, 2)] if u.suspended else [],
        })

    # Roofs per merged group.
    shapes, meta = [], {}
    for gi, members in enumerate(groups):
        members = [m for m in members if m.id not in special]
        if not members:
            continue
        outline = unary_union([m.raw.buffer(0.06, join_style=2) for m in members]).buffer(-0.06, join_style=2)
        for pi, poly in enumerate(polys(outline)):
            poly = clean(poly, 0.12)
            if poly.area < 2:
                continue
            key = f"g{gi}_{pi}"
            shapes.append((key, poly))
            use = "tower" if any(tower(m) for m in members) else ("church" if any(m.use == "church" for m in members) else "")
            meta[key] = (poly, members, use)
    skeletons = run_skeletons(shapes)
    roofs, failed = [], []
    for key, (poly, members, use) in meta.items():
        faces = skeletons.get(key)
        if not faces:
            failed.append(key)
            continue
        top = members[0].roof_top
        slope = TOWER_SLOPE if use == "tower" else CHURCH_SLOPE if use == "church" else ROOF_SLOPE

        def exposed_edge(a, b, top=top, self_ids={m.id for m in members}):
            d = b - a
            length = float(np.hypot(*d))
            n = np.array([d[1], -d[0]]) / length
            hits = 0
            for t in (0.25, 0.5, 0.75):
                pt = Point(*(a + d * t + n * PROBE))
                for j in tree.query(pt):
                    v = units[j]
                    if v.id not in self_ids and v.raw.contains(pt) and v.solid()[1] > top - 0.3:
                        hits += 1
                        break
            return hits < 2
        tv, tt, wv, wt = roof_mesh(poly, faces, top, slope, exposed_edge)
        c = poly.representative_point()
        roofs.append({"key": key, "use": use, "cx": r3(c.x), "cz": r3(c.y), "base": r3(top),
                      "v": [r3(x) for x in tv], "t": tt, "wv": [r3(x) for x in wv], "wt": wt,
                      "units": [m.id for m in members]})

    patches, curbs = ground_plan(units, extent, clip)
    plan = {"version": 1, "plane": PLANE, "roofSlope": ROOF_SLOPE,
            "extent": [r3(minx - 40), r3(minz - 40), r3(maxx + 40), r3(maxz + 40)],
            "units": plan_units, "roofs": roofs, "ground": patches, "curbs": curbs, "ragione": frame,
            "attribution": "Survey: Comune di Padova / Regione del Veneto DBT 2007 (IODL 2.0). "
                           "Landmark names/uses: OpenStreetMap contributors (ODbL)."}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(plan, separators=(",", ":")) + "\n")
    kinds = np.bincount([s for u in plan_units for s in u["segs"][6::8]], minlength=5)
    report = {"units": len(plan_units), "ragioneUnitsModelledSeparately": len(special), "roofGroups": len(roofs),
              "roofFailures": failed, "segments": dict(zip(["street", "upper", "porticoBack", "blank", "arcade"], map(int, kinds))),
              "porticoUnits": sum(u["suspended"] for u in plan_units), "groundPatches": len(patches),
              "curbEdges": len(curbs) // 6, "bytes": OUT.stat().st_size,
              "named": sorted({u["name"] for u in plan_units if u["name"]})}
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
