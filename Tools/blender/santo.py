"""Basilica di Sant'Antonio (il Santo): procedural model on the DBT 2007 volume units.

Surveyed: every footprint, courtyard/drum hole, base and eave (unit top), campanile and
turret eaves, Gattamelata pedestal footprint. Published (Wikipedia it, 2026): campanili 68 m,
facade about 28 m, 8 domes, conical dome over the crossing with an angel. Everything above an
eave (dome profiles, cone, lanterns, spires) and all ornament (archetti pensili, windows,
loggia, rose window, portals) is reference-informed typology, not a measurement.
"""
import math

from mathutils import Matrix, Vector

import lmcommon as lm

NAME = "Santo"

BRICK, LEAD, STONE, TRACHYTE = "Brick", "Lead sheet", "Istrian stone", "Trachyte masonry"
GLASS, DARK, DOOR, GOLD, IRON, TILE, BAL = "Window glass", "Interior shadow", "Door wood", "Clock brass", "Wrought iron", "Coppi roof", "Balustrade"
BRONZE = "Bronze"
AXIS = Vector((0.949, 0.315, 0))  # nave axis, facade (west) to apse (east), from the drum centres


def archlets(b, fr, v_top, mat=BRICK, spacing=0.95, depth=0.14):
    """Romanesque corbel table (archetti pensili) hanging below a cornice at height v_top."""
    n = int((fr.L - 0.4) / spacing)
    if n < 1:
        return
    start = (fr.L - n * spacing) / 2
    r = spacing * 0.36
    for k in range(n):
        c = start + (k + 0.5) * spacing
        spring = v_top - 0.2 - r
        pts = [(c + r * math.cos(math.pi * i / 6), spring + r * math.sin(math.pi * i / 6)) for i in range(7)]
        outer = [(c + (r + 0.09) * math.cos(math.pi * i / 6), spring + (r + 0.09) * math.sin(math.pi * i / 6)) for i in range(7)]
        for i in range(6):
            b.quad(fr.P(*pts[i], depth), fr.P(*pts[i + 1], depth), fr.P(*outer[i + 1], depth), fr.P(*outer[i], depth), mat)
            b.quad(fr.P(*outer[i], 0), fr.P(*outer[i], depth), fr.P(*outer[i + 1], depth), fr.P(*outer[i + 1], 0), mat)
        # small corbels under each springing
        for u in (c - r - 0.045, c + r + 0.045):
            b.box(tuple(fr.P(u, spring - 0.12, depth / 2)), (0.12, 0.12, 0.24), mat, rot=math.atan2(fr.t.y, fr.t.x))
    # flat band between arches and cornice
    b.quad(fr.P(0, v_top - 0.2, depth), fr.P(fr.L, v_top - 0.2, depth), fr.P(fr.L, v_top, depth), fr.P(0, v_top, depth), mat)
    b.quad(fr.P(0, v_top - 0.2, 0), fr.P(fr.L, v_top - 0.2, 0), fr.P(fr.L, v_top - 0.2, depth), fr.P(0, v_top - 0.2, depth), mat)


def cornice(b, ring, z, depth=0.35, height=0.35, mat=STONE):
    out = lm.offset_ring(ring, depth)
    for (a, c), (oa, oc) in zip(zip(ring, ring[1:] + ring[:1]), zip(out, out[1:] + out[:1])):
        b.quad((a[0], a[1], z), (c[0], c[1], z), (oc[0], oc[1], z), (oa[0], oa[1], z), mat)
        b.quad((oa[0], oa[1], z), (oc[0], oc[1], z), (oc[0], oc[1], z + height), (oa[0], oa[1], z + height), mat)
        b.quad((oa[0], oa[1], z + height), (oc[0], oc[1], z + height), (c[0], c[1], z + height), (a[0], a[1], z + height), mat)


def walls(b, ring, z0, z1, mat=BRICK):
    for a, c, L, n in lm.edges(ring):
        b.quad((a[0], a[1], z0), (c[0], c[1], z0), (c[0], c[1], z1), (a[0], a[1], z1), mat)


def window(b, fr, u, v0, width, height, pointed=False, frame=STONE, glass=GLASS, depth=0.05):
    shape = lm.arch_outline(u - width / 2, u + width / 2, height - width / 2 * (1.7 if pointed else 1), 10, pointed)
    b.face([fr.P(p[0], v0 + p[1], depth * 0.4) for p in shape], glass)
    lm.arch_ring(fr, u - width / 2, u + width / 2, v0 + height - width / 2 * (1.7 if pointed else 1), 0.16, depth, 0.0, frame, b, 10, pointed)
    b.box(tuple(fr.P(u, v0 - 0.08, 0.08)), (width + 0.4, 0.16, 0.16), frame, rot=math.atan2(fr.t.y, fr.t.x))


def pilaster(b, fr, u, v0, v1, width=0.9, depth=0.28, mat=BRICK):
    rot = math.atan2(fr.t.y, fr.t.x)
    b.box(tuple(fr.P(u, (v0 + v1) / 2, depth / 2)), (width, depth, v1 - v0), mat, rot=rot)


def circle_of(u):
    ring = lm.ring_points(u["outline"], u["ringSizes"], 0)
    cx, cy = lm.centroid(ring)
    r = math.sqrt(abs(lm.area(ring)) / math.pi)
    return (cx, cy), r, ring


def cross(b, x, y, z, size=2.2, mat=IRON):
    t = size * 0.07
    b.box((x, y, z + size / 2), (t, t, size), mat)
    b.box((x, y, z + size * 0.68), (size * 0.62, t, t), mat)
    b.box((x, y, z + size * 0.68), (t, size * 0.62, t), mat)
    b.lathe([(0.0, 0), (0.22, 0.1), (0.25, 0.25), (0.0, 0.45)], (x, y, z - 0.3), GOLD, segments=10)


def ribbed_shell(b, centre, radius, height, mat=LEAD, ribs=32, rows=14, profile="dome", top_radius=0.0):
    """Lead shell with raised standing seams: hemispherical dome or truncated cone."""
    cx, cy, z0 = centre
    seg = ribs * 4
    ring_rows = []
    for j in range(rows + 1):
        t = j / rows
        if profile == "dome":
            ang = t * math.pi / 2 * 0.965
            r = radius * math.cos(ang)
            z = z0 + height * math.sin(ang)
        else:
            r = radius + (top_radius - radius) * t
            z = z0 + height * t
        row = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            bump = 1.0 + (0.012 if i % 4 == 0 else 0.0) * min(1.0, r / max(radius, 1e-3) * 1.5)
            row.append((cx + r * bump * math.cos(a), cy + r * bump * math.sin(a), z))
        ring_rows.append(row)
    b.grid(ring_rows, mat, smooth=True)
    top = ring_rows[-1]
    b.face(top, mat)
    return top[0][2]


def drum_details(b, ring, base, top, windows=8, friezes=(0.0, 5.2)):
    edges = list(lm.edges(ring))
    perimeter = sum(e[2] for e in edges)
    # corbel tables along each (short) edge of the polygonal survey circle
    for a, c, L, n in edges:
        fr = lm.Frame(a, c, 0)
        for drop in friezes:
            archlets(b, fr, top - 0.6 - drop, spacing=L / max(1, round(L / 0.95)) if L > 0.5 else 0.95)
    cornice(b, ring, top - 0.6, depth=0.3, height=0.6, mat=STONE)
    # evenly spaced small arched windows and pilaster strips on the drum
    s = 0.0
    targets = [perimeter * (k + 0.5) / windows for k in range(windows)]
    strips = [perimeter * k / windows for k in range(windows)]
    for a, c, L, n in edges:
        fr = lm.Frame(a, c, 0)
        for t in targets:
            if s <= t < s + L and L > 0.2:
                window(b, fr, t - s, top - 5.0, 0.9, 2.4, frame=BRICK, glass=DARK)
        for t in strips:
            if s <= t < s + L:
                pilaster(b, fr, t - s, top - 10.5, top - 6.2, 0.7, 0.22)
        s += L


def dome(b, u, g, kind):
    (cx, cy), r, ring = circle_of(u)
    base, top = u["base"] - g, u["top"] - g
    walls(b, ring, base, top)
    drum_details(b, ring, base, top, friezes=(0.0, 5.2) if kind != "treasury" else (0.0,))
    if kind == "cone":
        z = ribbed_shell(b, (cx, cy, top), r - 0.25, 14.0, profile="cone", top_radius=1.9, rows=6)
        # octagonal open lantern: eight piers under round arches
        b.lathe([(2.1, 0), (2.1, 0.4)], (cx, cy, z), STONE, segments=8, rot=math.pi / 8)
        for k in range(8):
            a = 2 * math.pi * k / 8
            b.box((cx + 1.75 * math.cos(a), cy + 1.75 * math.sin(a), z + 2.0), (0.42, 0.42, 3.2), STONE, rot=a)
        b.lathe([(1.35, 0), (1.35, 3.2)], (cx, cy, z + 0.4), DARK, segments=8, rot=math.pi / 8, cap_top=False)
        b.lathe([(2.2, 0), (2.2, 0.5), (1.9, 0.7)], (cx, cy, z + 3.6), STONE, segments=8, rot=math.pi / 8)
        b.lathe([(1.75, 0), (0.08, 8.2)], (cx, cy, z + 4.3), LEAD, segments=8, rot=math.pi / 8, smooth=False)
        angel(b, cx, cy, z + 12.5)
    else:
        rise = 0.92 * (r - 0.3) if kind != "treasury" else 0.85 * (r - 0.3)
        z = ribbed_shell(b, (cx, cy, top), r - 0.3, rise)
        b.lathe([(0.9, 0), (0.9, 0.6), (0.5, 0.9)], (cx, cy, z - 0.1), LEAD, segments=12)
        cross(b, cx, cy, z + 1.1, 2.4 if kind != "treasury" else 1.8)
    return top


def angel(b, x, y, z):
    """Gilded weather-vane angel on the conical dome: simplified figure with trumpet."""
    b.lathe([(0.0, 0), (0.3, 0.05), (0.42, 0.9), (0.26, 1.35), (0.22, 1.55), (0.0, 1.6)], (x, y, z), GOLD, segments=10)
    b.lathe([(0.0, 0), (0.18, 0.12), (0.17, 0.32), (0.0, 0.42)], (x, y, z + 1.6), GOLD, segments=10)
    for side in (-1, 1):
        b.face([(x, y + 0.05 * side, z + 1.25), (x - 0.25, y + 1.0 * side, z + 1.95), (x - 0.55, y + 0.9 * side, z + 1.35), (x - 0.2, y + 0.2 * side, z + 0.8)], GOLD)
        b.face([(x - 0.23, y + 0.2 * side, z + 0.8), (x - 0.58, y + 0.9 * side, z + 1.35), (x - 0.28, y + 1.0 * side, z + 1.95), (x - 0.03, y + 0.05 * side, z + 1.25)], GOLD)
    b.lathe([(0.03, 0), (0.03, 0.7), (0.14, 0.95)], (x + 0.2, y, z + 1.5), GOLD, segments=6)


def campanile(b, u, g, total_height):
    ring = lm.ring_points(u["outline"], u["ringSizes"], 0)
    base, top = u["base"] - g, u["top"] - g
    cx, cy = lm.centroid(ring)
    walls(b, ring, base, top)
    for z in (base + 12, base + 24, base + 36, top - 7.5):
        cornice(b, ring, z, 0.12, 0.35, STONE)
    for a, c, L, n in lm.edges(ring):
        fr = lm.Frame(a, c, 0)
        if L > 1.2:
            window(b, fr, L / 2, top - 6.6, min(1.3, L * 0.55), 4.6, frame=STONE, glass=DARK)
            window(b, fr, L / 2, base + 27, min(0.6, L * 0.3), 2.2, frame=STONE, glass=DARK)
            archlets(b, fr, top - 7.6, spacing=L / max(1, round(L / 0.8)))
    cornice(b, ring, top - 0.5, 0.45, 0.5, STONE)
    # balustraded gallery, upper octagonal belfry stage and banded cone spire (published 68 m)
    r_in = math.sqrt(abs(lm.area(ring)) / (2 * math.sqrt(2))) * 0.72
    for d, outward in ((0.32, True), (0.27, False)):  # two single-sided faces, 5 cm apart
        for a, c, L, n in lm.edges(lm.offset_ring(ring, d)):
            fr = lm.Frame(a, c, top)
            if outward:
                b.quad(fr.P(0, 0, 0), fr.P(L, 0, 0), fr.P(L, 1.0, 0), fr.P(0, 1.0, 0), BAL, uv=[(0, 0), (L / 1.1, 0), (L / 1.1, 1), (0, 1)])
            else:
                b.quad(fr.P(L, 0, 0), fr.P(0, 0, 0), fr.P(0, 1.0, 0), fr.P(L, 1.0, 0), BAL, uv=[(L / 1.1, 0), (0, 0), (0, 1), (L / 1.1, 1)])
    b.polygon([ring], top, STONE)
    stage = 4.2
    b.lathe([(r_in, 0), (r_in, stage)], (cx, cy, top), BRICK, segments=8, rot=math.pi / 8, cap_top=False)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        fr = lm.Frame((cx + r_in * math.cos(a - math.pi / 8) * 1.02, cy + r_in * math.sin(a - math.pi / 8) * 1.02),
                      (cx + r_in * math.cos(a + math.pi / 8) * 1.02, cy + r_in * math.sin(a + math.pi / 8) * 1.02), top)
        window(b, fr, fr.L / 2, 0.6, fr.L * 0.55, 2.9, frame=STONE, glass=DARK)
    b.lathe([(r_in + 0.25, 0), (r_in + 0.25, 0.45)], (cx, cy, top + stage), STONE, segments=8, rot=math.pi / 8)
    spire_base = top + stage + 0.45
    tip = base + total_height
    bands = 9
    for k in range(bands):
        z0 = spire_base + (tip - 1.6 - spire_base) * k / bands
        z1 = spire_base + (tip - 1.6 - spire_base) * (k + 1) / bands
        r0 = (r_in + 0.1) * (1 - k / bands)
        r1 = (r_in + 0.1) * (1 - (k + 1) / bands) + 0.02
        b.lathe([(r0, 0), (r1, z1 - z0)], (cx, cy, z0), STONE if k % 2 else BRICK, segments=8, rot=math.pi / 8, smooth=False, cap_top=False)
    cross(b, cx, cy, tip - 1.6, 1.6)


def turret(b, u, g):
    ring = lm.ring_points(u["outline"], u["ringSizes"], 0)
    (cx, cy), r = lm.centroid(ring), math.sqrt(abs(lm.area(ring)) / math.pi)
    base, top = u["base"] - g, u["top"] - g
    walls(b, ring, base, top)
    for z in (top - 4.5, top - 0.4):
        cornice(b, ring, z, 0.15, 0.3, STONE)
    for a, c, L, n in lm.edges(ring):
        if L > 0.8:
            window(b, lm.Frame(a, c, 0), L / 2, top - 3.9, min(0.7, L * 0.5), 2.4, frame=STONE, glass=DARK)
    b.lathe([(r + 0.15, 0), (0.05, max(2.6, r * 2.8))], (cx, cy, top), TILE, segments=12, smooth=False)
    cross(b, cx, cy, top + max(2.6, r * 2.8), 1.0)


def plain_unit(b, u, g, windows=True, roof=LEAD):
    base, top = u["base"] - g, u["top"] - g
    rings = [lm.ring_points(u["outline"], u["ringSizes"], i) for i in range(len(u["ringSizes"]))]
    walls(b, rings[0], base, top)
    b.polygon(rings, top, roof)
    cornice(b, rings[0], top - 0.1, 0.3, 0.4, STONE)
    for a, c, L, n in lm.edges(rings[0]):
        fr = lm.Frame(a, c, 0)
        if L > 2.0:
            archlets(b, fr, top - 0.1)
        if windows and L > 5.5 and top - base > 12:
            count = max(1, int(L / 6.5))
            for k in range(count):
                window(b, fr, L * (k + 0.5) / count, base + (top - base) * 0.35, 1.5, (top - base) * 0.38, pointed=True)
        if L > 9 and top - base > 12:
            for k in range(1, int(L / 9) + 1):
                pilaster(b, fr, L * k / (int(L / 9) + 1), base, top - 1.6, 1.1, 0.3)


def facade(b, units, g):
    """West front on the surveyed front block and its seven projecting loggia bays."""
    front = units["UN_VOL:30788"]
    base = front["base"] - g
    ring = lm.ring_points(front["outline"], front["ringSizes"], 0)
    # Facade line from the westmost surveyed vertices; u runs south to north.
    tvec = Vector((-AXIS.y, AXIS.x, 0))  # north-west-ish, perpendicular to the axis
    proj = [(p[0] * AXIS.x + p[1] * AXIS.y, p[0] * tvec.x + p[1] * tvec.y) for p in ring]
    a_face = min(a for a, _ in proj)  # westmost plane of the surveyed front block
    t0 = min(t for a, t in proj if a < a_face + 3)
    t1 = max(t for a, t in proj if a < a_face + 3)
    def P(a, t):
        return (AXIS.x * a + tvec.x * t, AXIS.y * a + tvec.y * t)
    fr = lm.Frame(P(a_face, t1), P(a_face, t0), 0)  # normal points west (outward)
    W = fr.L
    eave = front["top"] - g
    apex = base + 28.0  # published facade height, about 28 m
    loggia_top = base + 19.58  # surveyed top of the projecting bays (UN_VOL:85827 ...)
    # gable screen from the surveyed eave to the published apex
    b.face([fr.P(0, eave, 0), fr.P(W, eave, 0), fr.P(W / 2, apex, 0)], BRICK)
    b.face([fr.P(W / 2, apex, -1.0), fr.P(W, eave, -1.0), fr.P(0, eave, -1.0)], BRICK)
    for (u0, v0), (u1, v1) in (((0, eave), (W / 2, apex)), ((W / 2, apex), (W, eave))):
        b.quad(fr.P(u0, v0 + 0.05, 0.25), fr.P(u1, v1 + 0.05, 0.25), fr.P(u1, v1 + 0.45, -1.1), fr.P(u0, v0 + 0.45, -1.1), STONE)
        steps = int(math.hypot(u1 - u0, v1 - v0) / 0.95)
        for k in range(steps):
            t = (k + 0.5) / steps
            uu, vv = u0 + (u1 - u0) * t, v0 + (v1 - v0) * t
            b.box(tuple(fr.P(uu, vv - 0.45, 0.08)), (0.55, 0.16, 0.5), BRICK, rot=math.atan2(fr.t.y, fr.t.x))
    cross(b, *fr.P(W / 2, apex + 0.3, -0.4), 2.0)
    # pilaster strips over the full height, in the surveyed gaps between the loggia bays
    bays = sorted([units[i] for i in ["UN_VOL:85828", "UN_VOL:30718", "UN_VOL:85831", "UN_VOL:85829", "UN_VOL:85830", "UN_VOL:85832", "UN_VOL:85827"]],
                  key=lambda u: (Vector((u["cx"], u["cz"], 0)) - fr.a).dot(fr.t))
    spans, fronts = [], []
    for u in bays:
        r = lm.ring_points(u["outline"], u["ringSizes"], 0)
        us = [(Vector((p[0], p[1], 0)) - fr.a).dot(fr.t) for p in r]
        spans.append((min(us), max(us)))
        fronts.append(max((Vector((p[0], p[1], 0)) - fr.a).dot(fr.n) for p in r))
    gaps = [(spans[i][1], spans[i + 1][0]) for i in range(len(spans) - 1) if spans[i + 1][0] - spans[i][1] > 0.8]
    for g0, g1 in gaps:
        c = (g0 + g1) / 2
        v_rake = eave + (apex - eave) * (1 - abs(c - W / 2) / (W / 2))
        pilaster(b, fr, c, base, v_rake - 0.3, g1 - g0, 1.1)
    # upper zone: rose window and two biforas between loggia and gable
    cu = W / 2
    cv = (loggia_top + eave) / 2 + 0.6
    R = min(2.6, (eave - loggia_top) / 2 - 0.4)
    segs = 32
    b.face([fr.P(cu + R * math.cos(2 * math.pi * k / segs), cv + R * math.sin(2 * math.pi * k / segs), 0.03) for k in range(segs)], GLASS)
    for rr, w in ((R, 0.35), (R * 0.35, 0.18)):
        for k in range(segs):
            a0, a1 = 2 * math.pi * k / segs, 2 * math.pi * (k + 1) / segs
            b.quad(fr.P(cu + rr * math.cos(a0), cv + rr * math.sin(a0), 0.2), fr.P(cu + rr * math.cos(a1), cv + rr * math.sin(a1), 0.2),
                   fr.P(cu + (rr + w) * math.cos(a1), cv + (rr + w) * math.sin(a1), 0.2), fr.P(cu + (rr + w) * math.cos(a0), cv + (rr + w) * math.sin(a0), 0.2), STONE)
    for k in range(8):  # radial tracery spokes
        a = 2 * math.pi * k / 8
        ca, sa, w = math.cos(a), math.sin(a), 0.09
        r0, r1 = R * 0.35, R
        b.quad(fr.P(cu + ca * r0 - sa * w, cv + sa * r0 + ca * w, 0.16), fr.P(cu + ca * r1 - sa * w, cv + sa * r1 + ca * w, 0.16),
               fr.P(cu + ca * r1 + sa * w, cv + sa * r1 - ca * w, 0.16), fr.P(cu + ca * r0 + sa * w, cv + sa * r0 - ca * w, 0.16), STONE)
    for side in (-1, 1):
        u = cu + side * min(7.0, W * 0.2)
        for du in (-0.55, 0.55):
            window(b, fr, u + du, loggia_top + 1.3, 0.85, 3.2, frame=STONE)
        lm.arch_ring(fr, u - 1.2, u + 1.2, loggia_top + 3.4, 0.22, 0.12, 0.0, BRICK, b)
    # projecting loggia bays: portals below, gallery arcade above, balustrade on top
    rot = math.atan2(fr.t.y, fr.t.x)
    for (u0, u1), u, front_w in zip(spans, bays, fronts):
        width = u1 - u0
        wf = front_w + 0.01  # surveyed outer face of this bay
        c = (u0 + u1) / 2
        if width > 3.4:  # five recessed portal arches (published); the narrow corner bays stay closed
            pw = min(4.4, width - 1.4) if width < 6 else min(4.4, width * 0.45)
            ph = 7.8 if width < 6 else 6.8
            shape = lm.arch_outline(c - pw / 2, c + pw / 2, ph - pw / 2)
            b.face([fr.P(p[0], base + p[1], wf + 0.02) for p in shape], DARK)
            lm.arch_ring(fr, c - pw / 2, c + pw / 2, base + ph - pw / 2, 0.45, 0.2, wf, STONE, b, 12)
            dw = min(2.6, pw * 0.6)
            b.quad(fr.P(c - dw / 2, base, wf + 0.04), fr.P(c + dw / 2, base, wf + 0.04), fr.P(c + dw / 2, base + min(4.6, ph - 1.8), wf + 0.04),
                   fr.P(c - dw / 2, base + min(4.6, ph - 1.8), wf + 0.04), DOOR)
        # gallery: dark recess with colonnettes and small arches (loggia typology)
        g0, g1 = base + 12.8, loggia_top - 1.3
        n = max(1, round(width / 1.45))
        step = width / n
        b.quad(fr.P(u0, g0, wf + 0.02), fr.P(u1, g0, wf + 0.02), fr.P(u1, g1, wf + 0.02), fr.P(u0, g1, wf + 0.02), DARK)
        for k in range(n):
            a0, a1 = u0 + k * step + 0.12, u0 + (k + 1) * step - 0.12
            lm.arch_ring(fr, a0, a1, g1 - (a1 - a0) / 2 - 0.25, 0.12, 0.3, wf + 0.02, STONE, b, 8)
            b.face([fr.P(a0 - 0.12, g1 - 0.25, wf + 0.3), fr.P(a1 + 0.12, g1 - 0.25, wf + 0.3), fr.P(a1 + 0.12, g1 + 0.2, wf + 0.3), fr.P(a0 - 0.12, g1 + 0.2, wf + 0.3)], BRICK)
        for k in range(n + 1):
            b.lathe([(0.13, 0), (0.1, 0.25), (0.1, g1 - g0 - (step / 2) - 0.7), (0.16, g1 - g0 - (step / 2) - 0.45)],
                    tuple(fr.P(u0 + k * step, g0, wf + 0.2)), STONE, segments=8)
        for v in (g0, loggia_top - 1.05):
            b.box(tuple(fr.P(c, v - 0.12, wf + 0.35)), (width, 0.7, 0.24), STONE, rot=rot)
            b.quad(fr.P(u0, v, wf + 0.6), fr.P(u1, v, wf + 0.6), fr.P(u1, v + 1.0, wf + 0.6), fr.P(u0, v + 1.0, wf + 0.6), BAL,
                   uv=[(0, 0), (width / 1.1, 0), (width / 1.1, 1), (0, 1)])
        b.box(tuple(fr.P(c, base + 0.3, wf + 0.1)), (width + 0.1, 0.4, 0.6), TRACHYTE, rot=rot)
        b.box(tuple(fr.P(c, g0 - 0.9, wf + 0.12)), (width, 0.3, 0.35), STONE, rot=rot)
    return fr


def gattamelata(b, gm, g):
    """Donatello's monument: DBT pedestal footprint, published proportions (base 7.8 m, statue 3.4 x 3.9 m)."""
    ring = gm["outline"]
    cx, cy = lm.centroid(ring)
    longest = max(lm.edges(ring), key=lambda e: e[2])
    d = Vector((longest[1][0] - longest[0][0], longest[1][1] - longest[0][1], 0)).normalized()
    # face away from the basilica front (west-north-west)
    if d.dot(AXIS) > 0:
        d = -d
    yaw = math.atan2(d.y, d.x)
    z0 = min(g(x, y) for x, y in ring) - g.anchor
    b.polygon([lm.offset_ring(ring, 0.9)], z0 + 0.35, TRACHYTE)
    walls(b, lm.offset_ring(ring, 0.9), z0 - 0.2, z0 + 0.35, TRACHYTE)
    walls(b, ring, z0 + 0.35, z0 + 7.8 - 0.6, STONE)
    b.polygon([ring], z0 + 7.8, STONE)
    cornice(b, ring, z0 + 7.8 - 0.6, 0.2, 0.6, STONE)
    cornice(b, ring, z0 + 0.35, 0.18, 0.5, STONE)
    for a, c, L, n in lm.edges(ring):
        if L > 2.5:
            fr = lm.Frame(a, c, 0)
            lm.arch_ring(fr, L * 0.3, L * 0.7, z0 + 4.2, 0.1, 0.08, 0, STONE, b)
            b.face([fr.P(p[0], z0 + 2.6 + p[1], 0.02) for p in lm.arch_outline(L * 0.3, L * 0.7, 1.6)], DARK)
    horse = lm.Builder("h")
    def piece(profile, segments, matrix):
        part = lm.Builder("p")
        part.lathe(profile, (0, 0, 0), BRONZE, segments=segments)
        horse.transformed(part, matrix)
    lie = Matrix.Rotation(math.pi / 2, 4, "Y")  # lathe axis (Z) -> +X, the horse's length
    # figure built facing +X, about 3.9 m long and 3.4 m tall above the pedestal
    piece([(0.0, 0), (0.5, 0.25), (0.66, 1.1), (0.6, 2.1), (0.42, 2.5), (0.0, 2.6)], 12, Matrix.Translation((-1.3, 0, 1.55)) @ lie)
    for sx in (-0.85, 0.85):
        for sy in (-0.28, 0.28):
            piece([(0.13, 0), (0.08, 0.5), (0.1, 1.05), (0.15, 1.3)], 6, Matrix.Translation((sx, sy, 0)))
    piece([(0.34, 0), (0.26, 0.8), (0.2, 1.25)], 8, Matrix.Translation((1.05, 0, 1.75)) @ Matrix.Rotation(0.6, 4, "Y"))
    piece([(0.2, 0), (0.17, 0.5), (0.1, 0.8)], 8, Matrix.Translation((1.7, 0, 2.75)) @ Matrix.Rotation(2.3, 4, "Y"))
    piece([(0.1, 0), (0.05, 1.0)], 6, Matrix.Translation((-1.3, 0, 1.75)) @ Matrix.Rotation(-2.6, 4, "Y"))
    piece([(0.3, 0), (0.3, 0.2), (0.27, 0.8), (0.18, 0.95)], 10, Matrix.Translation((-0.1, 0, 2.15)))
    piece([(0.0, 0), (0.15, 0.08), (0.14, 0.3), (0.0, 0.36)], 10, Matrix.Translation((-0.1, 0, 3.1)))
    for side in (-1, 1):
        piece([(0.1, 0), (0.08, 0.8)], 6, Matrix.Translation((0.05, 0.36 * side, 1.5)) @ Matrix.Rotation(-0.3, 4, "Y"))
    piece([(0.04, 0), (0.03, 1.1)], 6, Matrix.Translation((0.1, 0.3, 2.55)) @ Matrix.Rotation(1.1, 4, "Y"))
    b.transformed(horse, Matrix.Translation((cx, cy, z0 + 7.8)) @ Matrix.Rotation(yaw, 4, "Z"))


def build(src, g):
    units = {u["id"]: u for u in src["units"]}
    anchor_unit = units["UN_VOL:30736"]
    ax, az = circle_of(anchor_unit)[0]
    ay = anchor_unit["base"]
    g.anchor = ay
    shell = lm.Builder("Santo")
    for u in src["units"]:
        role = u["role"]
        if role in ("dome", "cone", "treasury"):
            dome(shell, u, ay, role)
        elif role == "campanile":
            campanile(shell, u, ay, 68.0)
        elif role == "turret":
            turret(shell, u, ay)
        elif role == "pier":
            plain_unit(shell, u, ay, windows=False, roof=STONE)
        else:
            plain_unit(shell, u, ay, windows=role not in ("front",), roof=LEAD)
    facade(shell, units, ay)
    monument = lm.Builder("Gattamelata")
    if src.get("gattamelata"):
        gattamelata(monument, src["gattamelata"], g)
    # recentre on the anchor (crossing drum centre, surveyed base)
    for bld in (shell, monument):
        for v in bld.v:
            v.x -= ax
            v.y -= az
    collision = lm.Builder("Santo_Collision")
    for u in src["units"]:
        rings = [lm.ring_points(u["outline"], u["ringSizes"], i) for i in range(len(u["ringSizes"]))]
        ring = [(x - ax, y - az) for x, y in rings[0]]
        walls(collision, ring, u["base"] - ay, u["top"] - ay, BRICK)
        collision.polygon([ring], u["top"] - ay, BRICK)
    place = (round(ax - AXIS.x * 57, 2), round(az - AXIS.y * 57, 2))  # Piazza del Santo, 12 m in front of the facade
    return {"anchor": [ax, ay, az], "builders": [shell, monument], "collision": collision,
            "replaces": {"units": [u["id"] for u in src["units"]]},
            "places": [{"name": "Basilica di Sant'Antonio", "x": place[0], "z": place[1],
                        "source": "Piazza del Santo, 12 m in front of the DBT facade (UN_VOL:30788)"}]}


# Preview cameras in anchor-relative Blender coordinates: (eye, target, lens mm)
VIEWS = {
    "front": ((-118.0, -40.0, 4.0), (-30.0, -8.0, 22.0), 30),
    "aerial": ((-150.0, -150.0, 110.0), (0.0, 0.0, 12.0), 38),
    "domes": ((95.0, 85.0, 42.0), (0.0, 0.0, 30.0), 35),
}
