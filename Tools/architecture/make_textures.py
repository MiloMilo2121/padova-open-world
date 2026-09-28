"""Build the Padova material textures.

Photographic PBR sources are Poly Haven CC0 downloads (see docs/THIRD_PARTY_ASSETS.md). Pattern
textures (trachyte masegni, portico checkerboard, shutters, lead sheeting, the Ragione's banded
masonry and railings) are generated here so their module sizes match the real materials.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / ".context/polyhaven"
OUT = ROOT / "Assets/Art/Padova/Textures"
rng = np.random.default_rng(1307)


def save(name, arr, quality=92):
    OUT.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8))
    path = OUT / name
    if name.endswith(".png"):
        img.save(path, optimize=True)
    else:
        img.save(path, quality=quality)
    print(path.relative_to(ROOT), img.size)


def load(name, size=None):
    img = Image.open(SRC / name).convert("RGB")
    if size:
        img = img.resize((size, size), Image.LANCZOS)
    return np.asarray(img).astype(np.float32) / 255


def noise(shape, scale, octaves=4, seed=0):
    """Tileable value noise via FFT-filtered white noise."""
    r = np.random.default_rng(seed)
    out = np.zeros(shape, np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        white = r.standard_normal(shape)
        fy = np.fft.fftfreq(shape[0])[:, None]
        fx = np.fft.fftfreq(shape[1])[None, :]
        f = np.sqrt(fx * fx + fy * fy)
        cutoff = 1.0 / (scale / (2 ** o))
        filt = np.exp(-(f / cutoff) ** 2)
        layer = np.real(np.fft.ifft2(np.fft.fft2(white) * filt))
        layer /= layer.std() + 1e-8
        out += amp * layer
        total += amp
        amp *= 0.5
    return out / total


def normal_from_height(h, strength):
    dy, dx = np.gradient(h)
    n = np.dstack([-dx * strength, dy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def copy_pbr():
    for src, dst in [("roof_09", "RoofCoppi"), ("marble_01", "IstrianStone"), ("medieval_red_brick", "Brick"),
                     ("herringbone_brick", "CourtyardBrick")]:
        for m, suffix in (("Diffuse", "_Albedo.jpg"), ("nor_gl", "_Normal.jpg")):
            Image.open(SRC / f"{src}_{m}_2k.jpg").save(OUT / (dst + suffix), quality=92)
            print(dst + suffix)
    # Neutral lime plaster: keep the source's stains and trowel marks, remove its hue so
    # each material can tint it with a documented Padova wall colour.
    a = load("white_plaster_rough_01_Diffuse_2k.jpg")
    b = load("painted_plaster_wall_Diffuse_2k.jpg")
    lum = (0.6 * a.mean(axis=2) + 0.4 * b.mean(axis=2))
    lum = (lum - lum.mean()) * 1.35 + 0.86
    grime = noise(lum.shape, 180, 3, 7)
    lum = lum - 0.035 * np.clip(grime, 0, None)
    save("Plaster_Albedo.jpg", np.dstack([lum * 1.0, lum * 0.985, lum * 0.955]))
    Image.open(SRC / "white_plaster_rough_01_nor_gl_2k.jpg").save(OUT / "Plaster_Normal.jpg", quality=92)


def slabs(size, metres, row_heights, lengths, base, var, joint_px, seed, tone=(1.0, 1.0, 1.0)):
    """Tileable courses of rectangular stone slabs (Padova's trachyte masegni)."""
    r = np.random.default_rng(seed)
    px = size / metres
    albedo = np.zeros((size, size, 3), np.float32)
    height = np.zeros((size, size), np.float32)
    ys, xs = np.mgrid[0:size, 0:size]
    rows = []
    y = 0.0
    while y < metres - 1e-6:
        h = row_heights[r.integers(len(row_heights))]
        h = min(h, metres - y)
        rows.append((y, h))
        y += h
    grain = noise((size, size), 3, 3, seed + 1)
    speck = r.random((size, size)).astype(np.float32)
    for ry, rh in rows:
        n = max(2, int(round(metres / np.mean(lengths))))
        cuts = np.sort(r.uniform(0, metres, n))
        offset = r.uniform(0, metres)
        edges = np.sort((cuts + offset) % metres)
        y0, y1 = int(round(ry * px)), int(round((ry + rh) * px))
        band = (ys >= y0) & (ys < y1)
        for k in range(len(edges)):
            a, b = edges[k], edges[(k + 1) % len(edges)]
            ax, bx = int(round(a * px)), int(round(b * px))
            if bx > ax:
                inside = band & (xs >= ax) & (xs < bx)
                dxl, dxr = xs - ax, bx - 1 - xs
            else:
                inside = band & ((xs >= ax) | (xs < bx))
                dxl = np.where(xs >= ax, xs - ax, xs + size - ax)
                dxr = np.where(xs < bx, bx - 1 - xs, bx - 1 - xs + size)
            v = r.normal(0, var)
            warm = r.normal(0, 0.012)
            col = np.array([base + v + warm, base + v, base + v - warm]) * np.array(tone)
            edge = np.minimum(np.minimum(dxl, dxr), np.minimum(ys - y0, y1 - 1 - ys)).astype(np.float32)
            bevel = np.clip(edge / (joint_px * 2.5), 0, 1)
            albedo[inside] = col
            height[inside] = (0.6 + 0.4 * bevel[inside]) + r.normal(0, 0.05)
            joint = inside & (edge < joint_px)
            albedo[joint] *= 0.55
            height[joint] = 0.0
    albedo *= (1 + 0.10 * grain)[..., None]
    albedo *= (0.9 + 0.2 * speck)[..., None]
    wear = noise((size, size), 60, 3, seed + 2)
    albedo *= (1 - 0.06 * np.clip(wear, 0, None))[..., None]
    height += 0.08 * grain + 0.04 * speck
    return albedo, height


def ground_textures():
    # Piazza/street trachyte from the Euganean hills: grey courses of ~45-55 cm, slab lengths 60-110 cm.
    alb, h = slabs(2048, 4.0, [0.44, 0.5, 0.55], [0.6, 0.8, 1.1], 0.43, 0.035, 5, 11, tone=(0.99, 1.0, 1.03))
    save("Trachyte_Albedo.jpg", alb)
    save("Trachyte_Normal.jpg", normal_from_height(Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)) and np.asarray(Image.fromarray((np.clip(h, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255, 6))
    # Sidewalk: smaller, lighter stone courses.
    alb, h = slabs(2048, 3.0, [0.3, 0.33, 0.36], [0.45, 0.6, 0.7], 0.55, 0.03, 4, 21, tone=(1.02, 1.0, 0.97))
    save("Sidewalk_Albedo.jpg", alb)
    save("Sidewalk_Normal.jpg", normal_from_height(np.asarray(Image.fromarray((np.clip(h, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255, 5))
    # Portico floors: red Verona and white Istrian stone squares, a common Padova portico paving.
    size, squares = 1024, 4
    ys, xs = np.mgrid[0:size, 0:size]
    cell = size // squares
    checker = ((xs // cell + ys // cell) % 2).astype(np.float32)
    grain = noise((size, size), 6, 4, 31)
    veins = np.abs(noise((size, size), 40, 3, 32))
    red = np.dstack([0.62 + 0.05 * grain, 0.36 + 0.04 * grain, 0.30 + 0.03 * grain]) * (1 - 0.15 * np.clip(veins - 1.2, 0, 1))[..., None]
    white = np.dstack([0.86 + 0.03 * grain, 0.83 + 0.03 * grain, 0.77 + 0.03 * grain]) * (1 - 0.12 * np.clip(veins - 1.4, 0, 1))[..., None]
    alb = np.where(checker[..., None] > 0.5, red, white)
    edge = np.minimum(np.minimum(xs % cell, cell - 1 - xs % cell), np.minimum(ys % cell, cell - 1 - ys % cell))
    alb[edge < 2] *= 0.6
    wear = noise((size, size), 30, 3, 33)
    alb *= (1 - 0.08 * np.clip(wear, 0, None))[..., None]
    save("PorticoFloor_Albedo.jpg", alb)
    h = np.clip(edge / 5.0, 0, 1) * 0.8 + 0.05 * grain
    save("PorticoFloor_Normal.jpg", normal_from_height(h.astype(np.float32), 3))


def detail_textures():
    # Venetian persiane: horizontal louvres ~7 cm, 8 per tile (tile = 0.56 m).
    size = 256
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    phase = (ys % 32) / 32
    louver = np.where(phase < 0.82, 0.55 + 0.45 * phase / 0.82, 0.25)
    grain = noise((size, size), 20, 2, 41)
    alb = np.dstack([louver] * 3) * (1 + 0.05 * grain)[..., None]
    save("Shutter_Albedo.png", alb)
    save("Shutter_Normal.png", normal_from_height(louver.astype(np.float32), 8))
    # Lead sheet roofing with standing seams every 0.6 m and staggered cross seams (tile = 2.4 m).
    size = 1024
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    seam_x = np.abs(((xs / size * 4) % 1) - 0.5) > 0.49
    row = np.floor(ys / size * 2)
    cross = np.abs((((ys / size * 2) % 1)) - 0.0) < 0.004
    cross |= np.abs(((ys / size * 2) % 1) - 1.0) < 0.004
    patina = noise((size, size), 90, 4, 51)
    streak = noise((size, size), 12, 2, 52) * 0.5
    base = 0.60 + 0.06 * patina + 0.03 * streak
    alb = np.dstack([base * 0.97, base, base * 1.02])
    alb[seam_x] *= 1.12
    alb[cross] *= 0.8
    save("Lead_Albedo.jpg", alb)
    h = np.zeros((size, size), np.float32)
    h[seam_x] = 1
    h = np.asarray(Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    h -= 0.3 * cross
    save("Lead_Normal.jpg", normal_from_height(h + 0.05 * patina, 10))
    # Palazzo della Ragione upper walls: warm brick courses with white stone bands (tile 4 m x 2 m).
    w, hgt = 2048, 1024
    ys, xs = np.mgrid[0:hgt, 0:w].astype(np.float32)
    course = np.floor(ys / 16)
    brick_x = (xs + (course % 2) * 32) % 64
    mortar = (ys % 16 < 2) | (brick_x < 2)
    stone_band = (course % 8) >= 6
    grain = noise((hgt, w), 5, 3, 61)
    tone = np.random.default_rng(62).normal(0, 0.05, (int(hgt / 16) + 1, int(w / 32) + 2))
    btone = tone[course.astype(int), ((xs + (course % 2) * 32) // 64).astype(int)]
    brick = np.dstack([0.74 + btone, 0.56 + btone * 0.8, 0.45 + btone * 0.6])
    stone = np.dstack([0.88 + 0.02 * grain, 0.85 + 0.02 * grain, 0.79 + 0.02 * grain])
    alb = np.where(stone_band[..., None], stone, brick) * (1 + 0.06 * grain)[..., None]
    alb[mortar & ~stone_band] = [0.80, 0.76, 0.68]
    save("RagioneMasonry_Albedo.jpg", alb)
    hh = np.where(mortar & ~stone_band, 0.0, 1.0).astype(np.float32) + 0.1 * grain
    save("RagioneMasonry_Normal.jpg", normal_from_height(hh, 3))
    # Wrought-iron railing: alpha-tested bars (tile = 1 m wide, 1 m tall).
    size = 256
    ys, xs = np.mgrid[0:size, 0:size]
    bars = (xs % 32) < 3
    rails = (ys < 8) | ((ys > 120) & (ys < 126)) | (ys > size - 10)
    alpha = (bars | rails).astype(np.float32)
    rgba = np.dstack([np.full((size, size), 0.12), np.full((size, size), 0.12), np.full((size, size), 0.13), alpha])
    Image.fromarray((rgba * 255).astype(np.uint8), "RGBA").save(OUT / "Railing.png")
    # Balustrade for the Ragione loggia: white stone balusters (tile = 1.2 m wide, 1 m tall).
    size = 256
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    cx = (xs % 43) - 21.5
    prof = 9 + 5 * np.sin((ys - 30) / 180 * np.pi) ** 2 - 4 * np.exp(-((ys - 60) / 12) ** 2)
    baluster = (np.abs(cx) < prof) & (ys > 28) & (ys < 228)
    rails = (ys < 28) | (ys > 228)
    alpha = (baluster | rails).astype(np.float32)
    shade = 0.9 - 0.25 * (np.abs(cx) / 16) ** 2
    rgba = np.dstack([0.92 * shade, 0.90 * shade, 0.84 * shade, alpha])
    rgba[rails, :3] = [0.9, 0.88, 0.82]
    Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA").save(OUT / "Balustrade.png")
    print("railing/balustrade")


def sky():
    import shutil
    dst = OUT.parent / "Sky"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "kloofendal_48d_partly_cloudy_puresky_4k.hdr", dst / "Kloofendal_PartlyCloudy_4k.hdr")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    steps = sys.argv[1:] or ["pbr", "ground", "detail", "sky"]
    if "pbr" in steps:
        copy_pbr()
    if "ground" in steps:
        ground_textures()
    if "detail" in steps:
        detail_textures()
    if "sky" in steps:
        sky()
