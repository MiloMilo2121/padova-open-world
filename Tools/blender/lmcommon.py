"""Shared helpers for the procedural Blender landmark models.

Coordinates: Blender X = grid east, Y = grid north, Z = up, in metres relative to an
asset anchor. Game/Unity coordinates are X = east, Y = up, Z = north. UVs are metric
(1 UV unit = 1 m) like the game's MeshSink, so the game's tiling materials line up.
"""
import json
import math
import re
from pathlib import Path

import bpy
from mathutils import Vector, geometry

ROOT = Path(__file__).resolve().parents[2]
MATERIALS = ROOT / "Assets/Art/Padova/Materials"
TEXTURES = ROOT / "Assets/Art/Padova/Textures"
LANDMARK_TEXTURES = ROOT / "Assets/Art/Landmarks/Textures"


def load_sources():
    return json.loads((ROOT / "Data/Landmarks/sources.json").read_text())


class Ground:
    """Python port of WorldPlan.GroundAt (Assets/Scripts/Architecture/WorldContext.cs)."""

    def __init__(self, g):
        self.g = g

    def __call__(self, x, z):
        g = self.g
        ex, st, nx, nz, t, pl, ce = g["extent"], g["terrainStep"], g["terrainNX"], g["terrainNZ"], g["terrain"], g["plane"], g["coreExtent"]
        original = pl[0] * x + pl[1] * z + pl[2]
        fx = min(max((x - ex[0]) / st, 0), nx - 1.001)
        fz = min(max((z - ex[1]) / st, 0), nz - 1.001)
        i, j = int(fx), int(fz)
        a, b = fx - i, fz - j
        h = (t[j * nx + i] * (1 - a) + t[j * nx + i + 1] * a) * (1 - b) + (t[(j + 1) * nx + i] * (1 - a) + t[(j + 1) * nx + i + 1] * a) * b
        dx = max(ce[0] - x, 0, x - ce[2])
        dz = max(ce[1] - z, 0, z - ce[3])
        blend = min(1.0, math.hypot(dx, dz) / 120)
        blend = blend * blend * (3 - 2 * blend)
        return original * (1 - blend) + h * blend


def newell(pts):
    n = Vector((0, 0, 0))
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)
    return n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))


def box_uv(p, n):
    ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
    if az >= ax and az >= ay:
        return (p.x, p.y)
    if ax >= ay:
        return (p.y * (1 if n.x > 0 else -1), p.z)
    return (-p.x * (1 if n.y > 0 else -1), p.z)


class Builder:
    """Accumulates one mesh. Faces carry a material name; vertices are shared only when asked."""

    def __init__(self, name):
        self.name = name
        self.v, self.f, self.mat, self.smooth, self.uv = [], [], [], [], []

    def verts(self, pts):
        base = len(self.v)
        self.v.extend(Vector(p) for p in pts)
        return base

    def face_idx(self, idx, mat, smooth=False, uv=None):
        if len(idx) < 3:
            return
        pts = [self.v[i] for i in idx]
        n = newell(pts)
        self.f.append(tuple(idx))
        self.mat.append(mat)
        self.smooth.append(smooth)
        if uv is None:
            # Metric box projection, shifted per face by whole 8.8 m periods (4 brick tiles) so UV
            # magnitudes stay small: large absolute UVs lose fragment precision on Metal and
            # render as a single texel.
            uv = [box_uv(p, n) for p in pts]
            du = math.floor(min(u for u, _ in uv) / 8.8) * 8.8
            dv = math.floor(min(v for _, v in uv) / 8.8) * 8.8
            uv = [(u - du, v - dv) for u, v in uv]
        self.uv.append(uv)

    def face(self, pts, mat, uv=None, smooth=False):
        pts = [Vector(p) for p in pts]
        base = self.verts(pts)
        self.face_idx(list(range(base, base + len(pts))), mat, smooth, uv)

    def quad(self, a, b, c, d, mat, uv=None):
        self.face([a, b, c, d], mat, uv)

    def grid(self, rows, mat, closed=True, smooth=True, uvscale=(1, 1), flip=False):
        """rows[j][i]: rings of points bottom-to-top; faces outward for CCW rings (seen from above)."""
        nj, ni = len(rows), len(rows[0])
        base = self.verts([p for row in rows for p in row])
        # Metric UVs: arc length around, slant length up.
        us = [[0.0] * (ni + 1) for _ in range(nj)]
        vs = [[0.0] * (ni + 1) for _ in range(nj)]
        for j in range(nj):
            for i in range(1, ni + 1):
                us[j][i] = us[j][i - 1] + (Vector(rows[j][i % ni]) - Vector(rows[j][i - 1])).length
            for i in range(ni + 1):
                vs[j][i] = vs[j - 1][i] + (Vector(rows[j][i % ni]) - Vector(rows[j - 1][i % ni])).length if j else 0.0
        cols = ni if closed else ni - 1
        for j in range(nj - 1):
            for i in range(cols):
                i2 = (i + 1) % ni
                idx = [base + j * ni + i, base + j * ni + i2, base + (j + 1) * ni + i2, base + (j + 1) * ni + i]
                uv = [(us[j][i] * uvscale[0], vs[j][i] * uvscale[1]), (us[j][i + 1] * uvscale[0], vs[j][i + 1] * uvscale[1]),
                      (us[j + 1][i + 1] * uvscale[0], vs[j + 1][i + 1] * uvscale[1]), (us[j + 1][i] * uvscale[0], vs[j + 1][i] * uvscale[1])]
                if flip:
                    idx.reverse(); uv.reverse()
                self.face_idx(idx, mat, smooth, uv)

    def polygon(self, rings, z, mat, up=True):
        """Flat polygon with holes at height z. rings: [outer, hole...] as (x, y) lists."""
        loops = [[Vector((x, y, z)) for x, y in r] for r in rings]
        flat = [p for loop in loops for p in loop]
        for tri in geometry.tessellate_polygon(loops):
            pts = [flat[i] for i in tri]
            n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
            if (n.z > 0) != up:
                pts.reverse()
            self.face(pts, mat)

    def indexed(self, xyz, tris, mat, up=True):
        base = self.verts(xyz)
        for a, b, c in zip(tris[0::3], tris[1::3], tris[2::3]):
            n = (self.v[base + b] - self.v[base + a]).cross(self.v[base + c] - self.v[base + a])
            idx = [base + a, base + b, base + c]
            if (n.z > 0) != up:
                idx.reverse()
            self.face_idx(idx, mat)

    def box(self, centre, size, mat, rot=0.0):
        cx, cy, cz = centre
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        c, s = math.cos(rot), math.sin(rot)
        def P(x, y, z):
            return Vector((cx + x * c - y * s, cy + x * s + y * c, cz + z))
        v = [P(-sx, -sy, -sz), P(sx, -sy, -sz), P(sx, sy, -sz), P(-sx, sy, -sz), P(-sx, -sy, sz), P(sx, -sy, sz), P(sx, sy, sz), P(-sx, sy, sz)]
        for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
            self.face([v[i] for i in f], mat)

    def lathe(self, profile, centre, mat, segments=16, smooth=True, cap_top=True, cap_bottom=False, rot=0.0):
        """profile: [(radius, z)] bottom to top, revolved around vertical axis through centre."""
        cx, cy, cz = centre
        rows = [[(cx + r * math.cos(rot + 2 * math.pi * i / segments), cy + r * math.sin(rot + 2 * math.pi * i / segments), cz + z)
                 for i in range(segments)] for r, z in profile]
        self.grid(rows, mat, smooth=smooth)
        if cap_top and profile[-1][0] > 1e-4:
            self.face(rows[-1], mat)
        if cap_bottom and profile[0][0] > 1e-4:
            self.face(list(reversed(rows[0])), mat)

    def transformed(self, other, matrix):
        base = self.verts([matrix @ v for v in other.v])
        for f, m, sm, uv in zip(other.f, other.mat, other.smooth, other.uv):
            self.face_idx([base + i for i in f], m, sm, uv)

    def to_object(self, collection, materials):
        names = sorted(set(self.mat))
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([tuple(v) for v in self.v], [], self.f)
        for n in names:
            me.materials.append(materials[n])
        index = {n: i for i, n in enumerate(names)}
        me.polygons.foreach_set("material_index", [index[m] for m in self.mat])
        me.polygons.foreach_set("use_smooth", self.smooth)
        uvl = me.uv_layers.new(name="UVMap")
        flat = [c for face in self.uv for uv in face for c in uv]
        uvl.data.foreach_set("uv", flat)
        me.validate(clean_customdata=False)
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        return ob

    @property
    def triangles(self):
        return sum(len(f) - 2 for f in self.f)


# ---------------------------------------------------------------- geometry helpers
def ring_points(outline, sizes, index):
    start = sum(sizes[:index])
    return [(outline[2 * i], outline[2 * i + 1]) for i in range(start, start + sizes[index])]


def area(ring):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:] + ring[:1]))


def centroid(ring):
    a = area(ring)
    cx = sum((p[0] + q[0]) * (p[0] * q[1] - q[0] * p[1]) for p, q in zip(ring, ring[1:] + ring[:1])) / (6 * a)
    cy = sum((p[1] + q[1]) * (p[0] * q[1] - q[0] * p[1]) for p, q in zip(ring, ring[1:] + ring[:1])) / (6 * a)
    return cx, cy


def edges(ring):
    """Yield (a, b, length, outward normal) for a CCW ring (normal points out of the solid)."""
    for a, b in zip(ring, ring[1:] + ring[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L > 1e-6:
            yield a, b, L, (dy / L, -dx / L)


def offset_ring(ring, d, limit=3.0):
    """Mitred offset; positive d moves CCW exterior outward."""
    out = []
    n = len(ring)
    for i in range(n):
        p0, p1, p2 = ring[i - 1], ring[i], ring[(i + 1) % n]
        def nrm(a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            return dy / L, -dx / L
        n1, n2 = nrm(p0, p1), nrm(p1, p2)
        mx, my = n1[0] + n2[0], n1[1] + n2[1]
        m = math.hypot(mx, my)
        if m < 1e-6:
            mx, my, scale = n1[0], n1[1], 1
        else:
            mx, my = mx / m, my / m
            scale = min(limit, 1 / max(0.2, mx * n1[0] + my * n1[1]))
        out.append((p1[0] + mx * d * scale, p1[1] + my * d * scale))
    return out


def point_in(ring, x, y):
    inside = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            inside = not inside
    return inside


class Frame:
    """Wall frame: u along the edge a->b, v up from z0, w outward along the normal."""

    def __init__(self, a, b, z0=0.0):
        self.a = Vector((a[0], a[1], 0))
        d = Vector((b[0] - a[0], b[1] - a[1], 0))
        self.L = d.length
        self.t = d / self.L
        self.n = Vector((self.t.y, -self.t.x, 0))
        self.z0 = z0

    def P(self, u, v, w=0.0):
        p = self.a + self.t * u + self.n * w
        return Vector((p.x, p.y, self.z0 + v))


def arch_outline(u0, u1, spring, segments=10, pointed=False):
    """Closed opening outline in (u, v): rectangle with a round or pointed (equilateral) head."""
    r = (u1 - u0) / 2
    c = (u0 + u1) / 2
    pts = [(u0, 0.0), (u1, 0.0), (u1, spring)]
    if pointed:
        R = 2 * r
        half = segments // 2
        apex = math.acos((R - r) / R)
        right = [(c - (R - r) + R * math.cos(apex * k / half), spring + R * math.sin(apex * k / half)) for k in range(1, half + 1)]
        left = [(2 * c - x, y) for x, y in reversed(right[:-1])]
        pts += right + left
    else:
        pts += [(c + r * math.cos(math.pi * k / segments), spring + r * math.sin(math.pi * k / segments)) for k in range(1, segments)]
    pts.append((u0, spring))
    return pts


def arch_ring(fr, u0, u1, spring, thickness, depth, w, mat, b, segments=10, pointed=False):
    """Projecting archivolt band around an opening head, on frame fr at offset w."""
    head = arch_outline(u0, u1, spring, segments, pointed)[2:]
    outer = arch_outline(u0 - thickness, u1 + thickness, spring, segments, pointed)[2:]
    for i in range(len(head) - 1):
        a, c = head[i], head[i + 1]
        o1, o2 = outer[i], outer[i + 1]
        b.quad(fr.P(a[0], a[1], w + depth), fr.P(o1[0], o1[1], w + depth), fr.P(o2[0], o2[1], w + depth), fr.P(c[0], c[1], w + depth), mat)
        b.quad(fr.P(o1[0], o1[1], w), fr.P(o1[0], o1[1], w + depth), fr.P(o2[0], o2[1], w + depth), fr.P(o2[0], o2[1], w), mat)
        b.quad(fr.P(a[0], a[1], w), fr.P(c[0], c[1], w), fr.P(c[0], c[1], w + depth), fr.P(a[0], a[1], w + depth), mat)


# ---------------------------------------------------------------- materials
def _unity_material(name):
    """Read base colour, albedo texture and tiling from a Unity .mat so Blender previews match."""
    path = MATERIALS / (name + ".mat")
    if not path.exists():
        return None
    text = path.read_text()
    info = {"color": (0.8, 0.8, 0.8, 1), "texture": None, "scale": 1.0, "smooth": 0.2, "clip": "_AlphaClip: 1" in text}
    m = re.search(r"_BaseColor: \{r: ([\d.]+), g: ([\d.]+), b: ([\d.]+), a: ([\d.]+)\}", text)
    if m:
        info["color"] = tuple(float(x) for x in m.groups())
    m = re.search(r"_Smoothness: ([\d.]+)", text)
    if m:
        info["smooth"] = float(m.group(1))
    m = re.search(r"- _BaseMap:\s+m_Texture: \{fileID: \d+, guid: (\w+), type: 3\}\s+m_Scale: \{x: ([\d.]+)", text)
    if m:
        guid, info["scale"] = m.group(1), float(m.group(2))
        for meta in list(TEXTURES.glob("*.meta")) + list(LANDMARK_TEXTURES.glob("*.meta")):
            if "guid: " + guid in meta.read_text():
                info["texture"] = str(meta.with_suffix(""))
    return info


# Materials that do not exist in the game yet: created in Unity by AgentScripts/BuildLandmarks.cs.
EXTRA = {
    "Canal water": {"color": (0.19, 0.27, 0.25, 1), "texture": None, "scale": 1, "smooth": 0.92, "clip": False},
    "Bronze": {"color": (0.23, 0.2, 0.15, 1), "texture": None, "scale": 1, "smooth": 0.55, "clip": False, "metal": 0.85},
    "Ring balustrade": {"color": (0.93, 0.92, 0.88, 1), "texture": str(LANDMARK_TEXTURES / "RingBalustrade.png"), "scale": 1, "smooth": 0.2, "clip": True},
}


def materials(names):
    out = {}
    for name in names:
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        info = EXTRA.get(name) or _unity_material(name) or {"color": (0.8, 0.8, 0.8, 1), "texture": None, "scale": 1, "smooth": 0.2, "clip": False}
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = info["color"]
        bsdf.inputs["Roughness"].default_value = 1 - info["smooth"]
        bsdf.inputs["Metallic"].default_value = info.get("metal", 0.0)
        mat.diffuse_color = info["color"]
        if info["texture"] and Path(info["texture"]).exists():
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = bpy.data.images.load(info["texture"], check_existing=True)
            mapping = nt.nodes.new("ShaderNodeMapping")
            mapping.inputs["Scale"].default_value = (info["scale"], info["scale"], 1)
            coord = nt.nodes.new("ShaderNodeTexCoord")
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1
            mix.inputs[7].default_value = info["color"]
            nt.links.new(coord.outputs["UV"], mapping.inputs["Vector"])
            nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
            nt.links.new(tex.outputs["Color"], mix.inputs[6])
            nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
            if info["clip"]:
                nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
                mat.blend_method = "CLIP" if hasattr(mat, "blend_method") else None
        out[name] = mat
    return out


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def export(objects, blend_path, fbx_path):
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    fbx_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    # Measured with Unity 6000.3 (bakeAxisConversion): these settings import Blender (x, y, z)
    # as Unity (x, y, -z). AgentScripts/BuildLandmarks.cs rotates each instance +90 degrees
    # about X, giving Unity (x, z, y) = (east, up, north).
    bpy.ops.export_scene.fbx(filepath=str(fbx_path), use_selection=True, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Z", axis_up="Y",
                             object_types={"MESH", "EMPTY"}, mesh_smooth_type="FACE", use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_space_transform=False, path_mode="STRIP")
    if blend_path.exists():
        blend_path.unlink()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)
