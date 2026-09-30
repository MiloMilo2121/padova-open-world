"""Prato della Valle: canal, parapets, 78 statues, 8 obelisks, 4 bridges and fountain.

Surveyed (DBT 2007): canal outline (AB_CDA) and water-edge elevation, bridge outlines and
deck elevations (PONTE), fountain outline (MN_EDI_NOVOL 0411). Statue/obelisk numbering and
positions: OpenStreetMap artwork nodes (ODbL), snapped onto the canal edge; positions 49/50
(absent from OSM) are interpolated; 45 and 88 are empty pedestals and 11, 12, 33, 34, 55, 56,
77, 78 are obelisks (Wikipedia it). Figures, pedestals, parapets, bridge arches and
balustrades, canal depth and the fountain's form are typology, not measurements.
"""
import math

from mathutils import Matrix, Vector, geometry

import lmcommon as lm

NAME = "PratoDellaValle"

STONE, TRACHYTE, PAVING, GROUND = "Istrian stone", "Trachyte masonry", "Trachyte paving", "Courtyard brick"
WATER, RINGS, DARK = "Canal water", "Ring balustrade", "Interior shadow"
OBELISKS = {11, 12, 33, 34, 55, 56, 77, 78}
EMPTY = {45, 88}
PARAPET_W, PARAPET_H, BARRIER_H = 0.7, 0.55, 1.6


def nearest_on_ring(ring, x, y):
    best = None
    s = 0.0
    for a, c in zip(ring, ring[1:] + ring[:1]):
        dx, dy = c[0] - a[0], c[1] - a[1]
        L2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2)) if L2 else 0.0
        px, py = a[0] + dx * t, a[1] + dy * t
        d = math.hypot(px - x, py - y)
        if best is None or d < best[0]:
            best = (d, px, py, s + t * math.sqrt(L2))
        s += math.sqrt(L2)
    return best


def at_arclength(ring, s):
    total = sum(math.dist(a, c) for a, c in zip(ring, ring[1:] + ring[:1]))
    s %= total
    for a, c in zip(ring, ring[1:] + ring[:1]):
        L = math.dist(a, c)
        if s <= L:
            t = s / L
            return a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t
        s -= L
    return ring[0]


def vertical_polygon(b, frame_pts, mat, flip=False):
    """frame_pts: list of (point3d, u, v) on a vertical plane; triangulated in (u, v)."""
    loop = [Vector((u, v, 0)) for _, u, v in frame_pts]
    for tri in geometry.tessellate_polygon([loop]):
        pts = [frame_pts[i][0] for i in tri]
        a, c, d = loop[tri[0]], loop[tri[1]], loop[tri[2]]
        ccw = (c - a).cross(d - a).z > 0
        if ccw == flip:
            pts.reverse()
        b.face(pts, mat)


def statue(b, x, y, z, facing, variant):
    """Stylised robed figure about 2.6 m tall (typology; the real 78 statues are individual works)."""
    fig = lm.Builder("s")
    sway = [0.0, 0.05, -0.04, 0.03][variant % 4]
    fig.lathe([(0.0, 0), (0.36, 0.0), (0.36, 0.1), (0.3, 0.2), (0.27, 0.8), (0.23, 1.3), (0.24, 1.5), (0.29, 1.66), (0.19, 1.82), (0.08, 1.88), (0.0, 1.9)],
              (0, 0, 0), STONE, segments=12)
    fig.lathe([(0.0, 0), (0.11, 0.03), (0.14, 0.17), (0.12, 0.31), (0.0, 0.37)], (0.02, sway, 1.86), STONE, segments=10)
    arm = lm.Builder("a")
    arm.lathe([(0.09, 0), (0.08, 0.55), (0.07, 0.62)], (0, 0, 0), STONE, segments=6)
    poses = [((0.25, 1.1), (-0.9, 0.3)), ((1.9, 0.2), (-0.3, 0.2)), ((0.6, 0.9), (0.6, -0.9)), ((2.4, -0.3), (-0.2, 0.1))]
    for side, (pitch, roll) in zip((1, -1), poses[variant % 4]):
        fig.transformed(arm, Matrix.Translation((0.04, 0.3 * side, 1.62)) @ Matrix.Rotation(math.pi - pitch, 4, "Y") @ Matrix.Rotation(roll * side, 4, "X"))
    if variant % 2 == 0:  # cloak falling from one shoulder
        fig.face([(0.25, -0.31, 1.66), (0.25, 0.31, 1.66), (0.35, 0.26, 0.2), (0.37, -0.18, 0.18)], STONE)
        fig.face([(0.35, -0.18, 0.18), (0.33, 0.26, 0.2), (0.23, 0.31, 1.66), (0.23, -0.31, 1.66)], STONE)
    else:  # book or scroll
        fig.box((0.3, 0.1, 1.2), (0.1, 0.3, 0.4), STONE)
    b.transformed(fig, Matrix.Translation((x, y, z)) @ Matrix.Rotation(facing, 4, "Z"))


def pedestal(b, x, y, z, rot):
    b.box((x, y, z + 0.15), (1.25, 1.25, 0.3), STONE, rot)
    b.lathe([(0.56, 0), (0.56, 0.12), (0.46, 0.28), (0.42, 0.5), (0.4, 1.35), (0.46, 1.5), (0.58, 1.66), (0.58, 1.78)], (x, y, z + 0.3), STONE, segments=14)
    b.box((x, y, z + 2.16), (1.2, 1.2, 0.16), STONE, rot)
    return z + 2.24


def obelisk(b, x, y, z, rot):
    """Stone obelisk on a bridge-end pedestal (about 6.5 m; proportions from reference photographs)."""
    b.box((x, y, z + 0.75), (1.15, 1.15, 1.5), STONE, rot)
    b.box((x, y, z + 1.6), (1.3, 1.3, 0.2), STONE, rot)
    c, s = math.cos(rot), math.sin(rot)
    for dx in (-0.36, 0.36):
        for dy in (-0.36, 0.36):
            b.lathe([(0.0, 0), (0.15, 0.04), (0.17, 0.16), (0.0, 0.32)], (x + dx * c - dy * s, y + dx * s + dy * c, z + 1.7), STONE, segments=8)
    b.box((x, y, z + 1.85), (0.8, 0.8, 0.3), STONE, rot)
    b.lathe([(0.34, 0), (0.22, 4.2), (0.0, 4.65)], (x, y, z + 2.0), STONE, segments=4, rot=rot + math.pi / 4, smooth=False)


def bridge(b, col, br, centre, canal_outer, canal_inner, g, ay):
    pts = [(p[0], p[1]) for p in br["outline"]]
    cx, cy = lm.centroid(pts)
    radial = Vector((cx - centre[0], cy - centre[1], 0)).normalized()
    lateral = Vector((-radial.y, radial.x, 0))
    rs = [(Vector((x - cx, y - cy, 0))).dot(radial) for x, y in pts]
    ws = [(Vector((x - cx, y - cy, 0))).dot(lateral) for x, y in pts]
    r0, r1, w0, w1 = min(rs), max(rs), min(ws), max(ws)
    deck_top = max(p[2] for p in br["outline"]) - ay
    def world(r, w):
        return (cx + radial.x * r + lateral.x * w, cy + radial.y * r + lateral.y * w)
    def G(r, w):
        x, y = world(r, w)
        return g(x, y) - ay
    # canal edges along the bridge axis (intersections with the surveyed canal rings)
    def crossing(ring):
        best = None
        for a, c in zip(ring, ring[1:] + ring[:1]):
            p = geometry.intersect_line_line_2d(Vector(world(-60, 0)), Vector(world(60, 0)), Vector(a), Vector(c))
            if p:
                r = (Vector((p.x - cx, p.y - cy, 0))).dot(radial)
                if best is None or abs(r) < abs(best):
                    best = r
        return best
    e_in, e_out = sorted([crossing(canal_inner), crossing(canal_outer)])
    water = g.water - ay
    spring, crown = water + 0.25, deck_top - 0.55
    span = e_out - e_in
    def deck(r):
        t = (r - r0) / (r1 - r0)
        ends = G(r0, 0) * (1 - t) + G(r1, 0) * t
        return ends + (deck_top - ends) * math.sin(math.pi * t) ** 0.6
    def intrados(r):
        t = (r - e_in) / span
        return spring + (crown - spring) * math.sin(math.pi * t) ** 0.8
    N = 16
    top = [r0 + (r1 - r0) * k / N for k in range(N + 1)]
    arch = [e_in + span * k / N for k in range(N + 1)]
    for w, flip in ((w0, True), (w1, False)):
        poly = [(r, deck(r)) for r in top]
        poly += [(r1, G(r1, w) - 0.05)]
        poly += [(e_out, G(e_out, w) - 0.05)]
        poly += [(r, intrados(r)) for r in reversed(arch)]
        poly += [(e_in, G(e_in, w) - 0.05), (r0, G(r0, w) - 0.05)]
        frame = [(Vector((*world(r, w), v)), r, v) for r, v in poly]
        vertical_polygon(b, frame, STONE, flip=flip)
        # archivolt band along the intrados edge
        for k in range(N):
            ra, rb = arch[k], arch[k + 1]
            off = 0.12 if flip else -0.12
            b.quad((*world(ra, w + off), intrados(ra)), (*world(rb, w + off), intrados(rb)), (*world(rb, w + off), intrados(rb) + 0.45), (*world(ra, w + off), intrados(ra) + 0.45), STONE)
    for k in range(N):
        ra, rb = top[k], top[k + 1]
        b.quad((*world(ra, w0), deck(ra)), (*world(rb, w0), deck(rb)), (*world(rb, w1), deck(rb)), (*world(ra, w1), deck(ra)), PAVING)
        col.quad((*world(ra, w0), deck(ra)), (*world(rb, w0), deck(rb)), (*world(rb, w1), deck(rb)), (*world(ra, w1), deck(ra)), PAVING)
        ia, ib = arch[k], arch[k + 1]
        b.quad((*world(ia, w1), intrados(ia)), (*world(ib, w1), intrados(ib)), (*world(ib, w0), intrados(ib)), (*world(ia, w0), intrados(ia)), STONE)
    # ring balustrades with stone posts and handrail, plus invisible safety barrier
    for w in (w0 + 0.25, w1 - 0.25):
        for k in range(N):
            ra, rb = top[k], top[k + 1]
            L = math.dist(world(ra, w), world(rb, w))
            u0 = (ra - r0) / 1.0
            u1 = (rb - r0) / 1.0
            for flip in (False, True):
                ww = w + (0.03 if flip else -0.03)  # separate the two faces: no z-fighting
                q = [(*world(ra, ww), deck(ra) + 0.1), (*world(rb, ww), deck(rb) + 0.1), (*world(rb, ww), deck(rb) + 1.0), (*world(ra, ww), deck(ra) + 1.0)]
                uv = [(u0, 0), (u1, 0), (u1, 1), (u0, 1)]
                if flip:
                    q.reverse(); uv.reverse()
                b.face(q, RINGS, uv=uv)
            b.quad((*world(ra, w - 0.2), deck(ra) + 1.0), (*world(rb, w - 0.2), deck(rb) + 1.0), (*world(rb, w + 0.2), deck(rb) + 1.0), (*world(ra, w + 0.2), deck(ra) + 1.0), STONE)
            b.quad((*world(ra, w - 0.2), deck(ra) + 1.12), (*world(rb, w - 0.2), deck(rb) + 1.12), (*world(rb, w + 0.2), deck(rb) + 1.12), (*world(ra, w + 0.2), deck(ra) + 1.12), STONE)
            for s in (-0.2, 0.2):
                b.quad((*world(ra, w + s), deck(ra) + 1.0), (*world(rb, w + s), deck(rb) + 1.0), (*world(rb, w + s), deck(rb) + 1.12), (*world(ra, w + s), deck(ra) + 1.12), STONE)
            col.quad((*world(ra, w), deck(ra)), (*world(rb, w), deck(rb)), (*world(rb, w), deck(rb) + BARRIER_H), (*world(ra, w), deck(ra) + BARRIER_H), STONE)
            col.quad((*world(rb, w), deck(rb)), (*world(ra, w), deck(ra)), (*world(ra, w), deck(ra) + BARRIER_H), (*world(rb, w), deck(rb) + BARRIER_H), STONE)
        for r in (top[0], (top[0] + top[-1]) / 2, top[-1]):
            b.box((*world(r, w), deck(r) + 0.6), (0.45, 0.45, 1.2), STONE, math.atan2(radial.y, radial.x))
    return {"id": br["id"], "centre": [cx, cy], "radial": [radial.x, radial.y], "span": round(span, 2), "deckTop": round(deck_top, 3),
            "ends": [world(r0, 0), world(r1, 0)], "rect": (r0, r1, w0, w1), "frame": (cx, cy, radial, lateral)}


def inside_bridge(info, x, y, margin):
    cx, cy, radial, lateral = info["frame"]
    r0, r1, w0, w1 = info["rect"]
    v = Vector((x - cx, y - cy, 0))
    return r0 - margin <= v.dot(radial) <= r1 + margin and w0 - margin <= v.dot(lateral) <= w1 + margin


def build(src, g):
    fountain = src["fountain"]["outline"]
    ax, az = lm.centroid(fountain)
    ay = g(ax, az)
    g.water = src["waterLevel"]
    outer, inner = [tuple(p) for p in src["canalOuter"]], [tuple(p) for p in src["canalInner"]]
    body = lm.Builder("Prato")
    ground = lm.Builder("Prato_Ground")
    water = lm.Builder("Prato_Water")
    col = lm.Builder("Prato_Collision")
    def Y(x, y):
        return g(x, y) - ay
    # 1. Ground cells, re-cut around the surveyed canal (replaces WorldContext ground there)
    for part in src["ground"]:
        v = part["v"]
        xyz = [(v[2 * i], v[2 * i + 1], Y(v[2 * i], v[2 * i + 1]) - 0.025) for i in range(len(v) // 2)]
        ground.indexed(xyz, part["t"], GROUND)
    # 2. Water at the surveyed water-edge level, embankment walls and a hidden bed
    wv = src["water"]["v"]
    wxyz = [(wv[2 * i], wv[2 * i + 1], g.water - ay) for i in range(len(wv) // 2)]
    water.indexed(wxyz, src["water"]["t"], WATER)
    col.indexed([(x, y, z - 1.0) for x, y, z in wxyz], src["water"]["t"], TRACHYTE)
    for ring in (outer, inner):
        for a, c, L, n in lm.edges(ring):
            # face the water: reverse the solid-outward winding
            q = [(c[0], c[1], g.water - ay - 1.2), (a[0], a[1], g.water - ay - 1.2), (a[0], a[1], Y(*a) - 0.02), (c[0], c[1], Y(*c) - 0.02)]
            ground.face(q, TRACHYTE)
            col.face(q, TRACHYTE)
    # 3. Bridges
    centre = (ax, az)
    bridges = [bridge(body, col, br, centre, outer, inner, g, ay) for br in src["bridges"]]
    # 4. Parapets along both canal edges, interrupted at bridges; invisible barrier above them
    for ring in (outer, inner):
        off = lm.offset_ring(ring, PARAPET_W)
        mid = lm.offset_ring(ring, PARAPET_W / 2)
        n = len(ring)
        for i in range(n):
            a, c = ring[i], ring[(i + 1) % n]
            oa, oc = off[i], off[(i + 1) % n]
            mx, my = (mid[i][0] + mid[(i + 1) % n][0]) / 2, (mid[i][1] + mid[(i + 1) % n][1]) / 2
            if any(inside_bridge(bi, mx, my, 0.4) for bi in bridges):
                continue
            za, zc = Y(*a), Y(*c)
            h = PARAPET_H
            body.quad((a[0], a[1], za + h), (c[0], c[1], zc + h), (oc[0], oc[1], zc + h), (oa[0], oa[1], za + h), STONE)
            body.quad((c[0], c[1], za - 0.1), (a[0], a[1], za - 0.1), (a[0], a[1], za + h), (c[0], c[1], zc + h), STONE)
            body.quad((oa[0], oa[1], za - 0.1), (oc[0], oc[1], zc - 0.1), (oc[0], oc[1], zc + h), (oa[0], oa[1], za + h), STONE)
            # coping lip over the water
            body.quad((a[0], a[1], za + h), (c[0], c[1], zc + h), (c[0], c[1], zc + h - 0.12), (a[0], a[1], za + h - 0.12), STONE)
            for q in ([(mid[i][0], mid[i][1], za), (mid[(i + 1) % n][0], mid[(i + 1) % n][1], zc), (mid[(i + 1) % n][0], mid[(i + 1) % n][1], zc + BARRIER_H), (mid[i][0], mid[i][1], za + BARRIER_H)],):
                col.face(q, STONE)
                col.face(list(reversed(q)), STONE)
    # 5. Statues and obelisks at the 88 numbered positions
    numbered = {}
    for p in src["osm"]:
        if p["ref"].isdigit() and 1 <= int(p["ref"]) <= 88 and p["kind"] in ("statue", None, "obelisk"):
            numbered[int(p["ref"])] = (p["x"], p["z"], p["name"], p["id"])
    placed, deviations, outliers = [], [], []
    lines = {"outer": lm.offset_ring(outer, PARAPET_W / 2), "inner": lm.offset_ring(inner, PARAPET_W / 2)}
    def snap(ref):
        line = lines["outer" if ref <= 44 else "inner"]
        x, y = numbered[ref][:2]
        d, px, py, s = nearest_on_ring(line, x, y)
        return px, py, s, d
    for ref in sorted(numbered):
        if snap(ref)[3] > 4.0:  # OSM node far from the canal edge: treat as unknown, interpolate
            outliers.append({"ref": ref, "osm": numbered[ref][3], "metres": round(snap(ref)[3], 2)})
    for o in outliers:
        del numbered[o["ref"]]
    for ref in range(1, 89):
        line = lines["outer" if ref <= 44 else "inner"]
        if ref in numbered:
            px, py, s, d = snap(ref)
            deviations.append(d)
            name, source = numbered[ref][2], numbered[ref][3]
        else:
            first, last = (1, 44) if ref <= 44 else (45, 88)
            wrap = lambda k: first + (k - first) % (last - first + 1)
            lo, hi, steps_lo, steps_hi = wrap(ref - 1), wrap(ref + 1), 1, 1
            while lo not in numbered:
                lo, steps_lo = wrap(lo - 1), steps_lo + 1
            while hi not in numbered:
                hi, steps_hi = wrap(hi + 1), steps_hi + 1
            s0, s1 = snap(lo)[2], snap(hi)[2]
            total = sum(math.dist(a, c) for a, c in zip(line, line[1:] + line[:1]))
            if abs(s1 - s0) > total / 2:
                s1 += total if s1 < s0 else -total
            px, py = at_arclength(line, s0 + (s1 - s0) * steps_lo / (steps_lo + steps_hi))
            name, source = "", "interpolated between OSM refs %d and %d" % (lo, hi)
        z = Y(px, py)
        dirx, diry = centre[0] - px, centre[1] - py
        to_centre = math.atan2(diry, dirx)
        facing = to_centre if ref <= 44 else to_centre + math.pi  # face the canal
        kind = "obelisk" if ref in OBELISKS else "empty pedestal" if ref in EMPTY else "statue"
        if kind == "obelisk":
            obelisk(body, px, py, z, facing)
            col.box((px, py, z + 1.0), (1.4, 1.4, 2.0), STONE, facing)
        else:
            top = pedestal(body, px, py, z, facing)
            col.box((px, py, z + 1.1), (1.2, 1.2, 2.2), STONE, facing)
            if kind == "statue":
                statue(body, px, py, top, facing, ref)
        placed.append({"ref": ref, "kind": kind, "name": name, "source": source, "x": round(px, 2), "z": round(py, 2)})
    # 6. Fountain (surveyed basin outline; rim, jet and bowl are typology)
    fz = Y(ax, az)
    rim_in = lm.offset_ring(fountain, -0.5)
    walls_ring = [(p[0], p[1]) for p in fountain]
    for a, c, L, n in lm.edges(walls_ring):
        body.quad((a[0], a[1], fz - 0.05), (c[0], c[1], fz - 0.05), (c[0], c[1], fz + 0.5), (a[0], a[1], fz + 0.5), STONE)
    for (a, c), (ia, ic) in zip(zip(walls_ring, walls_ring[1:] + walls_ring[:1]), zip(rim_in, rim_in[1:] + rim_in[:1])):
        body.quad((a[0], a[1], fz + 0.5), (c[0], c[1], fz + 0.5), (ic[0], ic[1], fz + 0.5), (ia[0], ia[1], fz + 0.5), STONE)
        body.quad((ic[0], ic[1], fz + 0.5), (ia[0], ia[1], fz + 0.5), (ia[0], ia[1], fz + 0.1), (ic[0], ic[1], fz + 0.1), STONE)
    water.polygon([rim_in], fz + 0.32, WATER)
    body.lathe([(0.9, 0), (0.7, 0.4), (0.45, 0.6), (0.4, 1.3), (1.6, 1.5), (1.7, 1.75), (0.3, 1.8), (0.2, 2.4), (0.0, 2.5)], (ax, az, fz), STONE, segments=20)
    water.lathe([(0.25, 0), (0.12, 1.6), (0.0, 2.1)], (ax, az, fz + 2.3), WATER, segments=10)
    for bld in (body, ground, water, col):
        for v in bld.v:
            v.x -= ax
            v.y -= az
    info = {"statues": sum(p["kind"] == "statue" for p in placed), "obelisks": sum(p["kind"] == "obelisk" for p in placed),
            "emptyPedestals": sum(p["kind"] == "empty pedestal" for p in placed),
            "osmOutliersInterpolated": outliers, "osmSnapMetres": {"max": round(max(deviations), 2), "mean": round(sum(deviations) / len(deviations), 2)},
            "bridges": [{k: bi[k] for k in ("id", "span", "deckTop")} for bi in bridges],
            "waterLevel": g.water, "groundRect": src["groundRect"], "positions": placed}
    return {"anchor": [ax, ay, az], "builders": [body, ground, water], "collision": col, "info": info,
            "replaces": {"patches": [c["id"] for c in src["canal"]], "ownGround": src["groundRect"]},
            "places": [{"name": "Prato della Valle", "x": round(ax, 3), "z": round(az, 3), "source": "DBT MN_EDI_NOVOL fountain; Blender model"}]}


VIEWS = {
    "aerial": ((-170.0, -190.0, 120.0), (0.0, 0.0, 0.0), 40),
    "canal": ((-66.0, -40.0, 2.4), (-35.0, 25.0, 2.0), 28),
    "bridge": ((-90.0, -5.0, 3.0), (-60.0, -16.0, 1.0), 35),
}
