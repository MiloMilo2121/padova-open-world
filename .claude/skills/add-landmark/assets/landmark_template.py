"""<Display name>: procedural model on the DBT 2007 survey.

Surveyed: <units/layers>. Published: <figures + sources>. Typology: <everything else>.
See Data/Landmarks/<slug>-evidence.md.
"""
import math

from mathutils import Matrix, Vector

import lmcommon as lm
import santo  # reuse walls, cornice, archlets, window, pilaster, ribbed_shell, plain_unit, cross ...

NAME = "<FbxName>"
BRICK, LEAD, STONE = "Brick", "Lead sheet", "Istrian stone"


def build(src, g):
    units = src["units"]
    ay = min(u["base"] for u in units)
    ax, az = lm.centroid(lm.ring_points(units[0]["outline"], units[0]["ringSizes"], 0))
    body = lm.Builder(NAME)
    for u in units:
        santo.plain_unit(body, u, ay)  # replace per role with specific architecture
    col = lm.Builder(NAME + "_Collision")
    for u in units:
        ring = lm.ring_points(u["outline"], u["ringSizes"], 0)
        santo.walls(col, ring, u["base"] - ay, u["top"] - ay, BRICK)
        col.polygon([ring], u["top"] - ay, BRICK)
    for b in (body, col):
        for v in b.v:
            v.x -= ax
            v.y -= az
    return {"anchor": [ax, ay, az], "builders": [body], "collision": col, "info": {},
            "replaces": {"units": [u["id"] for u in units]},
            "places": [{"name": "<Display name>", "x": round(ax, 2), "z": round(az, 2), "source": "<open ground near the entrance>"}]}


VIEWS = {"aerial": ((-120.0, -120.0, 90.0), (0.0, 0.0, 10.0), 38)}
