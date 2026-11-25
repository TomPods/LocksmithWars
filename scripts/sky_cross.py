"""Assemble la croix de controle des raccords du ciel SKY_Warm et mesure les sauts aux bords.
Usage : uv run --with pillow python scripts/sky_cross.py
Croix :      Up
          Lf Ft Rt Bk
             Dn
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "exports" / "SKY"
N = 1024
f = {k: Image.open(D / f"SKY_Warm_Skybox{k}.png").convert("RGB") for k in
     ("Ft", "Bk", "Lf", "Rt", "Up", "Dn")}
for k, im in f.items():
    assert im.size == (N, N), (k, im.size)

cross = Image.new("RGB", (4 * N, 3 * N), (40, 40, 40))
pos = {"Up": (1, 0), "Lf": (0, 1), "Ft": (1, 1), "Rt": (2, 1), "Bk": (3, 1), "Dn": (1, 2)}
for k, (cx, cy) in pos.items():
    cross.paste(f[k], (cx * N, cy * N))
cross.resize((2048, 1536), Image.LANCZOS).save(ROOT / "renders" / "session7_SKY_croix.png")


def col(im, x):
    return [im.getpixel((x, y)) for y in range(N)]


def row(im, y):
    return [im.getpixel((x, y)) for x in range(N)]


def diff(a, b):
    d = [max(abs(p[c] - q[c]) for c in range(3)) for p, q in zip(a, b)]
    return round(sum(d) / len(d), 2), max(d)


# Up : haut image = +Z (Bk), droite = +X (Rt). Dn : haut image = -Z (Ft), droite = +X.
checks = {
    "Lf|Ft": diff(col(f["Lf"], N - 1), col(f["Ft"], 0)),
    "Ft|Rt": diff(col(f["Ft"], N - 1), col(f["Rt"], 0)),
    "Rt|Bk": diff(col(f["Rt"], N - 1), col(f["Bk"], 0)),
    "Bk|Lf": diff(col(f["Bk"], N - 1), col(f["Lf"], 0)),
    "Up/Ft": diff(row(f["Up"], N - 1), row(f["Ft"], 0)),
    "Up/Lf": diff(col(f["Up"], 0), row(f["Lf"], 0)),
    "Up/Rt": diff(col(f["Up"], N - 1), row(f["Rt"], 0)[::-1]),
    "Up/Bk": diff(row(f["Up"], 0), row(f["Bk"], 0)[::-1]),
    "Ft/Dn": diff(row(f["Ft"], N - 1), row(f["Dn"], 0)),
}
for k, v in checks.items():
    print(f"{k:8s} ecart moyen {v[0]:6.2f}  max {v[1]}")
