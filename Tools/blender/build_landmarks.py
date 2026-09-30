"""Build the Santo and Prato della Valle landmark assets headlessly.

/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
    --python Tools/blender/build_landmarks.py -- [santo] [prato] [--render]

Writes Blender/Landmarks/<Name>.blend (source), Assets/Art/Landmarks/<Name>.fbx (Unity),
Data/Landmarks/<name>-build.json (anchor, counts, bounds) and optional previews in
.context/landmarks-renders/. Runs in its own Blender process: no shared Blender MCP session.
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import importlib  # noqa: E402

import lmcommon as lm  # noqa: E402

ROOT = lm.ROOT
# Register new landmarks here: slug -> module in Tools/blender. Each module defines NAME, VIEWS and
# build(src, ground) -> {anchor, builders, collision, info?, replaces{units, patches, ownGround}, places}.
REGISTRY = ["santo", "prato"]
ASSETS = {slug: (importlib.import_module(slug).NAME, importlib.import_module(slug)) for slug in REGISTRY}


def render(objects, path, eye, target, lens=32, size=(1600, 1000)):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(path)
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1)
    bg.inputs["Strength"].default_value = 0.9
    scene.world = world
    sun = bpy.data.objects.get("Sun") or bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    if sun.name not in scene.collection.objects:
        scene.collection.objects.link(sun)
    sun.data.energy = 4.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    cam = bpy.data.objects.get("Camera") or bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    if cam.name not in scene.collection.objects:
        scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.clip_end = 5000
    cam.location = eye
    d = Vector(target) - Vector(eye)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    wanted = [a for a in argv if a in ASSETS] or list(ASSETS)
    do_render = "--render" in argv
    sources = lm.load_sources()
    for key in wanted:
        name, module = ASSETS[key]
        lm.reset_scene()
        ground = lm.Ground(sources["ground"])
        result = module.build(sources[key], ground)
        col = bpy.context.scene.collection
        mats = lm.materials(sorted({m for b in result["builders"] + [result["collision"]] for m in b.mat}))
        objs = [b.to_object(col, mats) for b in result["builders"] if b.f]
        coll = result["collision"].to_object(col, mats)
        coll.display_type = "WIRE"
        coll.hide_render = True
        root = bpy.data.objects.new(name, None)
        col.objects.link(root)
        for ob in objs + [coll]:
            ob.parent = root
        info = {"name": name, "anchor": [round(v, 3) for v in result["anchor"]],
                "note": "Unity position = anchor (east, up, north); FBX mapped as described in Tools/blender/lmcommon.py.",
                "objects": {b.name: {"triangles": b.triangles, "vertices": len(b.v)} for b in result["builders"] + [result["collision"]]},
                "boundsLocal": {}, "replaces": result.get("replaces", {}), "places": result.get("places", []), **result.get("info", {})}
        for b in result["builders"]:
            if b.v:
                info["boundsLocal"][b.name] = [[round(min(v[i] for v in b.v), 2) for i in range(3)], [round(max(v[i] for v in b.v), 2) for i in range(3)]]
        blend = ROOT / "Blender/Landmarks" / (name + ".blend")
        fbx = ROOT / "Assets/Art/Landmarks" / (name + ".fbx")
        lm.export(objs + [coll, root], blend, fbx)
        (ROOT / "Data/Landmarks" / (key + "-build.json")).write_text(json.dumps(info, indent=2) + "\n")
        print("BUILT", json.dumps(info))
        if do_render:
            out = ROOT / ".context/landmarks-renders"
            out.mkdir(parents=True, exist_ok=True)
            for view, (eye, target, lens) in module.VIEWS.items():
                render(objs, out / f"{key}-{view}.png", eye, target, lens)


def write_manifest():
    """Assets/Art/Landmarks/Landmarks.json, merged from every registered landmark's build report:
    which survey records WorldContext must stop drawing, discovery places, and where models go."""
    manifest = {"note": "Generated by Tools/blender/build_landmarks.py. Survey records here are drawn by the Blender models instead of WorldContext.",
                "replacedUnits": [], "replacedPatches": [], "ownGround": [], "places": [], "models": []}
    for slug in REGISTRY:
        path = ROOT / "Data/Landmarks" / (slug + "-build.json")
        if not path.exists():
            continue
        b = json.loads(path.read_text())
        rep = b.get("replaces", {})
        manifest["replacedUnits"] += rep.get("units", [])
        manifest["replacedPatches"] += rep.get("patches", [])
        manifest["ownGround"] += rep.get("ownGround", [])  # flat list of x0, z0, x1, z1 rectangles
        manifest["places"] += b.get("places", [])
        manifest["models"].append({"name": b["name"], "asset": "Assets/Art/Landmarks/" + b["name"] + ".fbx", "anchor": b["anchor"]})
    for key in ("replacedUnits", "replacedPatches"):
        assert len(manifest[key]) == len(set(manifest[key])), key + " claimed by two landmarks"
    (ROOT / "Assets/Art/Landmarks/Landmarks.json").write_text(json.dumps(manifest, indent=1) + "\n")


if __name__ == "__main__":
    main()
    write_manifest()
