"""Locksmith Wars - categorie FX (effets et recompenses).

FX_GoldPile_S / M / L : tas d'or (monticule facette + grosses pieces + lingots), une seule piece
`Pile` #F2C12E Metal. Les trois tailles sortent de la meme fonction `_gold_pile()` : memes tailles
reelles de pieces et de lingots, seule la composition (liste `layout`) change.
FX_Coin, FX_AlarmBeacon, FX_Shield_Dome, FX_Shield_Ring : voir chaque build_*.
"""
import math
import random

import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import lw_common as lw

CATEGORY = "FX"
GOLD = "#F2C12E"
SHIELD = "#4FC3FF"
ALARM = "#FF2A2A"

COIN_D = 0.80        # diametre (cercle circonscrit de l'octogone), exagere
COIN_T = 0.19        # epaisseur : la tranche fait lire "piece"
COIN_SIDES = 8
INGOT = (1.1, 0.55, 0.36)  # petit ING_Bar (meme trapeze, dessus a 78 %)

K_MOUND, K_COIN, K_BOTTOM, K_INGOT = 0, 1, 2, 3
UP = Vector((0.0, 0.0, 1.0))


# ------------------------------------------------------------ briques
def _coin(bm, kind, center, axis, spin=0.0, d=COIN_D, t=COIN_T, sides=COIN_SIDES):
    """Disque epais d'axe `axis` centre en `center`. Renvoie la face du dessous."""
    rot = UP.rotation_difference(Vector(axis).normalized()).to_matrix()
    center = Vector(center)
    top, bot = [], []
    for i in range(sides):
        a = spin + 2.0 * math.pi * i / sides
        x, y = math.cos(a) * d / 2.0, math.sin(a) * d / 2.0
        top.append(bm.verts.new(center + rot @ Vector((x, y, t / 2.0))))
        bot.append(bm.verts.new(center + rot @ Vector((x, y, -t / 2.0))))
    faces = [bm.faces.new(top)]
    bottom = bm.faces.new(list(reversed(bot)))
    for i in range(sides):
        j = (i + 1) % sides
        faces.append(bm.faces.new((bot[i], bot[j], top[j], top[i])))
    for f in faces:
        f[kind] = K_COIN
    bottom[kind] = K_BOTTOM
    return bottom


def _ingot(bm, kind, matrix, size=INGOT, taper=0.78):
    """Lingot trapezoidal (forme de ING_Bar, sans biseau : invisible a cette taille)."""
    sx, sy, sz = size
    res = bmesh.ops.create_cube(bm, size=1.0)
    for v in res["verts"]:
        k = taper if v.co.z > 0.0 else 1.0
        v.co = matrix @ Vector((v.co.x * sx * k, v.co.y * sy * k, v.co.z * sz))
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f[kind] = K_INGOT


def _mound(bm, kind, rng, radius, height, rings=2, sides=8):
    """Cone facette franc (triangule), sommet marque, sans fond (pose au sol, invisible)."""
    profile = {2: ((1.0, 0.0), (0.56, 0.60)),
               3: ((1.0, 0.0), (0.70, 0.42), (0.36, 0.80))}[rings]
    loops = []
    for n, (kr, kz) in enumerate(profile):
        ring = []
        for i in range(sides):
            a = 2.0 * math.pi * (i + 0.5 * n) / sides
            r = radius * kr * rng.uniform(0.95, 1.05)
            z = height * kz * (rng.uniform(0.95, 1.05) if kz else 1.0)
            ring.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)))
        loops.append(ring)
    apex = bm.verts.new((0.0, 0.0, height))
    faces = []
    for n, (lo, hi) in enumerate(zip(loops, loops[1:])):
        for i in range(sides):
            a, b = lo[i], lo[(i + 1) % sides]
            if n % 2 == 0:      # anneau superieur decale d'un demi-pas : bandes en zigzag
                faces.append(bm.faces.new((a, b, hi[i])))
                faces.append(bm.faces.new((b, hi[(i + 1) % sides], hi[i])))
            else:
                faces.append(bm.faces.new((a, b, hi[(i + 1) % sides])))
                faces.append(bm.faces.new((a, hi[(i + 1) % sides], hi[i])))
    top = loops[-1]
    for i in range(sides):
        faces.append(bm.faces.new((top[i], top[(i + 1) % sides], apex)))
    for f in faces:
        f[kind] = K_MOUND


def _polar(ang_deg, rho):
    a = math.radians(ang_deg)
    return Vector((math.cos(a) * rho, math.sin(a) * rho, 0.0))


# ------------------------------------------------------- fonction commune
def _gold_pile(asset, size, mound, layout, seed=1, tolerance=0.05, notes="",
               keep_bottoms=False):
    """Tas d'or : une piece `Pile`, base centree, encombrement `size` a +/- `tolerance` (aucun
    etirement : les pieces restent rondes).

    size   : (X, Y, Z) vise, en studs.
    mound  : (rayon, hauteur, nombre d'anneaux 2 ou 3) du monticule central.
    layout : composition, angles en degres (0 = +X, -90 = avant), rho = distance au centre :
        ("scale", ang, rho[, lift])      piece couchee sur la pente (ecaille)
        ("stand", ang, rho, yaw[, sink]) piece debout sur la tranche, face tournee vers `yaw`
        ("flat", ang, rho)               piece a plat au sol
        ("lean", ang, rho, tilt)         piece au sol appuyee contre le tas, inclinee de `tilt`
        ("column", ang, rho, n)          colonne droite de n pieces
        ("ingot", x, y, z, yaw, pitch, roll)  lingot (centre, angles ; pitch > 0 : bout +X en bas)
    seed   : graine des petites irregularites (monticule, rotation des pieces).
    keep_bottoms : garde le dessous des pieces inclinees ("scale", "lean"), visible en vue
        rasante ; seul le dessous des pieces a plat au sol est alors supprime.
    """
    rng = random.Random(seed)
    coll = lw.reset_collection(asset)
    mr, mh, rings = mound

    bm = bmesh.new()
    kind = bm.faces.layers.int.new("kind")
    _mound(bm, kind, rng, mr, mh, rings)
    bm.normal_update()
    bvh = BVHTree.FromBMesh(bm)

    def surface(p):
        loc, normal, _i, _d = bvh.ray_cast(Vector((p.x, p.y, 100.0)), Vector((0.0, 0.0, -1.0)))
        if loc is None:
            return Vector((p.x, p.y, 0.0)), UP.copy(), False
        return loc, (normal if normal.z > 0.0 else -normal), True

    def buried(p, margin=0.005):
        loc, _n, hit = surface(p)
        return hit and p.z < loc.z - margin

    drop = []
    n_coins = n_ingots = 0
    for item in layout:
        what = item[0]
        if what == "ingot":
            _w, x, y, z, yaw, pitch, roll = item
            _ingot(bm, kind, Matrix.Translation((x, y, z))
                   @ Matrix.Rotation(math.radians(yaw), 4, "Z")
                   @ Matrix.Rotation(math.radians(pitch), 4, "Y")
                   @ Matrix.Rotation(math.radians(roll), 4, "X"))
            n_ingots += 1
            continue
        ang, rho = item[1], item[2]
        radial = _polar(ang, 1.0)
        spin = math.radians(ang) + math.pi / COIN_SIDES + math.radians(rng.uniform(-6.0, 6.0))
        loc, n, _hit = surface(_polar(ang, rho))
        if what == "scale":
            lift = item[3] if len(item) > 3 else 0.0
            axis = (n * 0.85 + UP * 0.15).normalized()
            bottom = _coin(bm, kind, loc + axis * (COIN_T * 0.5 + lift), axis, spin)
            if keep_bottoms:
                bottom[kind] = K_COIN
            else:
                drop.append(bottom)
            n_coins += 1
        elif what == "stand":
            yaw = math.radians(item[3])
            sink = item[4] if len(item) > 4 else 0.62
            axis = Vector((math.cos(yaw), math.sin(yaw), rng.uniform(-0.08, 0.08)))
            _coin(bm, kind, loc + UP * (COIN_D * 0.5 * sink), axis, rng.uniform(0.0, 0.4))
            n_coins += 1
        elif what == "flat":
            drop.append(_coin(bm, kind, _polar(ang, rho) + UP * (COIN_T * 0.5), UP, spin))
            n_coins += 1
        elif what == "lean":
            tilt = math.radians(item[3])
            axis = UP * math.cos(tilt) + radial * math.sin(tilt)
            z = COIN_T * 0.5 * math.cos(tilt) + math.sin(tilt) * COIN_D * 0.46
            bottom = _coin(bm, kind, _polar(ang, rho) + UP * z, axis, spin)
            if keep_bottoms:
                bottom[kind] = K_COIN
            else:
                drop.append(bottom)
            n_coins += 1
        elif what == "column":
            for k in range(item[3]):
                off = Vector((rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 0.0))
                drop.append(_coin(bm, kind, _polar(ang, rho) + off + UP * (COIN_T * (k + 0.5)),
                                  UP, spin + rng.uniform(-0.25, 0.25)))
                n_coins += 1
        else:
            raise ValueError("Element de composition inconnu : %r" % (what,))

    # faces invisibles : dessous des pieces couchees, tout ce qui est noye dans le monticule
    doomed = set(drop)
    for f in bm.faces:
        if f[kind] != K_MOUND and buried(f.calc_center_median()) \
                and all(buried(v.co) for v in f.verts):
            doomed.add(f)
    bmesh.ops.delete(bm, geom=list(doomed), context="FACES")
    # rien sous le sol
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                           plane_co=(0.0, 0.0, 0.0), plane_no=(0.0, 0.0, 1.0), clear_inner=True)

    # base centree (simple translation, aucune mise a l'echelle)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    shift = Vector(((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, 0.0))
    bmesh.ops.translate(bm, verts=bm.verts, vec=-shift)
    dims = (max(xs) - min(xs), max(ys) - min(ys), max(zs))
    for d, target, name in zip(dims, size, "XYZ"):
        if abs(d - target) > tolerance * target:
            print("ATTENTION %s : %s = %.3f hors tolerance (vise %.2f)" % (asset, name, d, target))
    print("%s : %d pieces, %d lingots, encombrement %.3f x %.3f x %.3f"
          % (asset, n_coins, n_ingots, *dims))

    lw.add_object(asset, "Pile", bm, coll, GOLD)
    lw.update_manifest(asset, [
        {"object": "Pile", "color": GOLD, "material": "Metal", "canCollide": False,
         "role": "fixed",
         "notes": notes or "Tas d'or (monticule + pieces + lingots fusionnes). Origine = base "
                           "centree, a poser sur GoldPoint. Avant = -Y Blender (-Z Roblox)."}])
    path = lw.export_asset(asset, CATEGORY)
    lw.report(asset)
    lw.save_blend()
    return path


# ------------------------------------------------------------- tas d'or
def build_fx_goldpile_s():
    """FX_GoldPile_S : 2 x 2 x 0,6, pour la cavite de VLT_Lvl1 (3,1 de large)."""
    return _gold_pile("FX_GoldPile_S", (2.0, 2.0, 0.6), (0.62, 0.28, 2), [
        ("ingot", 0.0, 0.10, 0.40, 14.0, 0.0, 0.0),            # couche au sommet
        ("column", -45.0, 0.80, 2), ("column", 135.0, 0.80, 2),
        ("flat", -135.0, 0.80), ("flat", 45.0, 0.80),
        ("lean", -92.0, 0.62, 32.0), ("lean", 178.0, 0.62, 32.0), ("lean", 88.0, 0.62, 32.0),
        ("lean", 2.0, 0.62, 32.0),
    ], seed=3, keep_bottoms=True)


def build_fx_goldpile_m():
    """FX_GoldPile_M : 3 x 3 x 1,2, pour la cavite de VLT_Lvl2."""
    return _gold_pile("FX_GoldPile_M", (3.0, 3.0, 1.2), (1.0, 0.78, 2), [
        ("ingot", 0.0, 0.05, 0.86, 8.0, 0.0, 0.0),            # couche au sommet
        ("ingot", 0.08, -0.56, 0.72, -86.0, 44.0, 0.0),       # appuye dessus, vers l'avant
        ("ingot", -0.62, 0.18, 0.68, 165.0, -55.0, 10.0),     # plante en biais
        ("scale", -35.0, 0.62), ("scale", 18.0, 0.66), ("scale", -142.0, 0.62),
        ("stand", 42.0, 0.50, -70.0), ("stand", 112.0, 0.50, -108.0),
        ("column", -55.0, 1.08, 4),
        ("flat", -92.0, 1.10), ("flat", -150.0, 1.10), ("flat", 20.0, 1.10),
        ("flat", 92.0, 1.10), ("flat", 180.0, 1.10),
    ], seed=7)


def build_fx_goldpile_l():
    """FX_GoldPile_L : vise 3,9 x 3,9 x 2,0 (sol plat de la cavite de VLT_Lvl3 : 4,23 de large)."""
    return _gold_pile("FX_GoldPile_L", (3.9, 3.9, 2.0), (1.3, 1.32, 3), [
        ("ingot", 0.0, -0.30, 1.38, 4.0, 0.0, 0.0),           # pyramide de 3 au sommet
        ("ingot", 0.0, 0.30, 1.38, -4.0, 0.0, 0.0),
        ("ingot", 0.0, 0.0, 1.74, 6.0, 0.0, 0.0),
        ("ingot", -0.50, -0.82, 0.80, -112.0, 46.0, 0.0),     # appuye sur la pente avant
        ("ingot", 0.88, 0.12, 0.92, 12.0, -55.0, 10.0),       # plante en biais a droite
        ("ingot", 1.20, -0.58, 0.18, 62.0, 0.0, 0.0),         # couche au pied
        ("scale", -75.0, 0.95), ("scale", -35.0, 0.95), ("scale", 50.0, 0.95),
        ("scale", 95.0, 0.95), ("scale", 140.0, 0.95), ("scale", -172.0, 0.95),
        ("stand", 40.0, 0.60, -65.0), ("stand", 125.0, 0.60, -112.0),
        ("stand", -160.0, 0.62, -150.0),
        ("column", -64.0, 1.50, 4), ("column", 152.0, 1.50, 3),
        ("flat", -95.0, 1.52), ("flat", -150.0, 1.52), ("flat", 5.0, 1.52),
        ("flat", 95.0, 1.52), ("flat", -172.0, 1.52),
    ], seed=11, keep_bottoms=True)


# ------------------------------------------------------------------ piece
def build_fx_coin():
    """FX_Coin : piece isolee 0,6 de diametre x 0,1, 12 cotes, debout (axe = Y Blender), listel
    en pente et trou de serrure en relief sur les deux faces. Origine = centre."""
    asset = "FX_Coin"
    coll = lw.reset_collection(asset)
    sides, r_out, r_in, half, field = 12, 0.30, 0.235, 0.05, 0.022
    bm = bmesh.new()

    def ring(r, h):
        return [bm.verts.new((math.cos(2.0 * math.pi * i / sides) * r, h,
                              math.sin(2.0 * math.pi * i / sides) * r)) for i in range(sides)]

    rims = {}
    for sgn in (-1.0, 1.0):
        outer, inner = ring(r_out, sgn * half), ring(r_in, sgn * field)
        rims[sgn] = outer
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((outer[i], outer[j], inner[j], inner[i]))     # listel en pente
        bm.faces.new(inner)                                             # champ
        # trou de serrure stylise (tete a pans + pied evase), en relief jusqu'au niveau du listel
        outline = [(-0.062, -0.135), (0.062, -0.135), (0.030, -0.005), (0.082, 0.055),
                   (0.046, 0.125), (-0.046, 0.125), (-0.082, 0.055), (-0.030, -0.005)]
        # flancs en pente (base large, dessus etroit) : seuls eux accrochent la lumiere en une
        # seule couleur
        top = [bm.verts.new((u * 0.62, sgn * half, v * 0.80)) for u, v in outline]
        low = [bm.verts.new((u * 1.40, sgn * (field - 0.01), v * 1.30)) for u, v in outline]
        bm.faces.new(top)
        bm.faces.new(list(reversed(low)))       # fond cache : coque fermee, normales fiables
        for i in range(len(outline)):
            j = (i + 1) % len(outline)
            bm.faces.new((low[i], low[j], top[j], top[i]))
    for i in range(sides):                                              # tranche
        j = (i + 1) % sides
        bm.faces.new((rims[-1.0][i], rims[-1.0][j], rims[1.0][j], rims[1.0][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    lw.add_object(asset, "Coin", bm, coll, GOLD)
    lw.update_manifest(asset, [
        {"object": "Coin", "color": GOLD, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Piece lancee vers le voleur. Origine = centre de la piece. Piece debout : axe "
                  "de la piece = Y Blender = Z Roblox (faces vers l'avant -Z et l'arriere +Z), "
                  "diametre dans le plan X/Y Roblox. Trou de serrure en relief sur les deux "
                  "faces, pied vers le bas (-Y Roblox)."}])
    path = lw.export_asset(asset, CATEGORY)
    lw.report(asset)
    lw.save_blend()
    return path


# -------------------------------------------------------------- gyrophare
BEACON_SEGS = 10
BEACON_BASE_H = 0.4
BEACON_SKIRT = 0.4            # partie droite du dome sous la demi-sphere (cahier : dome 1 x 0,9)
BEACON_AXIS_Z = 0.75          # hauteur de l'origine du Reflector sur l'axe


def _lathe(bm, profile, segs, cap_top=False, phase=0.0):
    """Surface de revolution autour de Z a partir d'un profil [(r, z), ...] (r = 0 : sommet)."""
    loops = []
    for r, z in profile:
        if r <= 1e-6:
            loops.append([bm.verts.new((0.0, 0.0, z))])
        else:
            loops.append([bm.verts.new((math.cos(phase + 2.0 * math.pi * i / segs) * r,
                                        math.sin(phase + 2.0 * math.pi * i / segs) * r, z))
                          for i in range(segs)])
    for lo, hi in zip(loops, loops[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(hi) == 1:
                bm.faces.new((lo[i], lo[j], hi[0]))
            elif len(lo) == 1:
                bm.faces.new((lo[0], hi[j], hi[i]))
            else:
                bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    if cap_top and len(loops[-1]) > 1:
        bm.faces.new(loops[-1])
    return loops


def build_fx_alarmbeacon():
    """FX_AlarmBeacon : Base (socle), Dome (verre rouge), Reflector (miroir + ampoule, tournant)."""
    asset = "FX_AlarmBeacon"
    coll = lw.reset_collection(asset)
    bh, sk = BEACON_BASE_H, BEACON_SKIRT

    bm = bmesh.new()
    _lathe(bm, [(0.60, 0.0), (0.60, bh - 0.10), (0.50, bh)], 12, cap_top=True)
    lw.add_object(asset, "Base", bm, coll, "#3B3F45")

    bm = bmesh.new()
    prof = [(0.5, bh), (0.5, bh + sk)] if sk > 0.0 else [(0.5, bh)]
    for a in (30.0, 60.0):
        prof.append((0.5 * math.cos(math.radians(a)), bh + sk + 0.5 * math.sin(math.radians(a))))
    prof.append((0.0, bh + sk + 0.5))
    _lathe(bm, prof, BEACON_SEGS)
    lw.add_object(asset, "Dome", bm, coll, ALARM)

    # Reflector : demi-cylindre miroir (ouvert vers -Y) + ampoule + pied, centre sur l'axe
    bm = bmesh.new()
    z0, z1, ro, ri, n = 0.52, 0.98, 0.30, 0.25, 6
    cols = []
    for i in range(n + 1):
        a = math.pi * i / n                      # 0..180 deg : cote +Y
        c, s = math.cos(a), math.sin(a)
        cols.append([bm.verts.new((c * r, s * r, z)) for r, z in
                     ((ro, z0), (ro, z1), (ri, z1), (ri, z0))])
    for a, b in zip(cols, cols[1:]):
        for k in range(4):
            bm.faces.new((a[k], b[k], b[(k + 1) % 4], a[(k + 1) % 4]))
    bm.faces.new(cols[0])
    bm.faces.new(cols[-1])
    cz, br = BEACON_AXIS_Z, 0.12
    _lathe(bm, [(0.0, cz - br), (br * 0.82, cz - br * 0.57), (br * 0.82, cz + br * 0.57),
                (0.0, cz + br)], 6)
    _lathe(bm, [(0.06, bh + 0.01), (0.06, cz - br * 0.8)], 6)
    refl = lw.add_object(asset, "Reflector", bm, coll, ALARM, origin=(0.0, 0.0, cz))
    swept = max(math.hypot(v.co.x, v.co.y) for v in refl.data.vertices)
    print("Reflector : rayon balaye %.3f (dome : rayon interieur 0,5 jusqu'a z = %.2f)"
          % (swept, bh + sk))

    lw.update_manifest(asset, [
        {"object": "Base", "color": "#3B3F45", "material": "Metal", "canCollide": False,
         "role": "fixed",
         "notes": "Socle 1,2 de diametre x 0,4, chanfreine. Origine = base centree, a poser sur "
                  "BeaconPoint. Le code actuel nomme le gyrophare `Beacon` : garder ce nom pour "
                  "le modele clone."},
        {"object": "Dome", "color": ALARM, "material": "Glass", "canCollide": False,
         "role": "fixed",
         "notes": "Dome de verre rouge 1 de diametre x 0,9 (jupe droite 0,4 + demi-sphere), "
                  "pose sur le socle (z 0,4 a 1,3). Transparency 0,3. Origine = base centree du "
                  "gyrophare (0, 0, 0)."},
        {"object": "Reflector", "color": ALARM, "material": "Neon", "canCollide": False,
         "role": "moving",
         "notes": "Miroir demi-cylindrique + ampoule + pied, dans le dome. Tourne en boucle "
                  "autour de l'axe vertical (Y Roblox). Origine sur l'axe central : (0, 0, 0,75) "
                  "Blender = (0, 0,75, 0) Roblox. Rayon balaye 0,30 < rayon du dome 0,5. Miroir "
                  "ouvert vers l'avant (-Z Roblox) au repos. Porte la SpotLight et la PointLight "
                  "ajoutees dans Studio."},
    ])
    path = lw.export_asset(asset, CATEGORY)
    lw.report(asset)
    lw.save_blend()
    return path


# ---------------------------------------------------------------- bouclier
SHIELD_R = 5.0
SHIELD_SUBDIV = 3


def _shield_dome_bm():
    """Demi-icosphere de rayon 5 coupee a l'equateur, bord ramene sur le cercle z = 0."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=SHIELD_SUBDIV, radius=SHIELD_R)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4,
                           plane_co=(0.0, 0.0, 0.0), plane_no=(0.0, 0.0, 1.0), clear_inner=True)
    rim = [v for v in bm.verts if abs(v.co.z) < 1e-3]
    for v in rim:
        k = SHIELD_R / math.hypot(v.co.x, v.co.y)
        v.co = Vector((v.co.x * k, v.co.y * k, 0.0))
    angles = sorted(math.atan2(v.co.y, v.co.x) for v in rim)
    return bm, angles


def build_fx_shield_dome():
    """FX_Shield_Dome : demi-sphere facettee 10 de diametre x 5, bord ouvert plan a z = 0."""
    asset = "FX_Shield_Dome"
    coll = lw.reset_collection(asset)
    bm, angles = _shield_dome_bm()
    print("%s : %d sommets sur le bord" % (asset, len(angles)))
    lw.add_object(asset, "Dome", bm, coll, SHIELD)
    lw.update_manifest(asset, [
        {"object": "Dome", "color": SHIELD, "material": "ForceField", "canCollide": False,
         "role": "fixed",
         "notes": "Champ de force : demi-icosphere facettee 10 x 10 x 5, sans fond, normales "
                  "vers l'exterieur. Origine = base centree. CastShadow false. Redimensionne par "
                  "le jeu selon le coffre (10 / 14 / 20). Le code actuel nomme cette piece "
                  "`Shield` une fois clonee."}])
    path = lw.export_asset(asset, CATEGORY)
    lw.report(asset)
    lw.save_blend()
    return path


def build_fx_shield_ring():
    """FX_Shield_Ring : anneau plat au sol, memes sommets exterieurs que le bord du dome."""
    asset = "FX_Shield_Ring"
    coll = lw.reset_collection(asset)
    tmp, angles = _shield_dome_bm()
    tmp.free()
    width, thick = 0.45, 0.10
    bm = bmesh.new()
    cols = []
    for a in angles:
        c, s = math.cos(a), math.sin(a)
        cols.append([bm.verts.new((c * r, s * r, z)) for r, z in
                     ((SHIELD_R, 0.0), (SHIELD_R, thick), (SHIELD_R - width, thick),
                      (SHIELD_R - width, 0.0))])
    for i, a in enumerate(cols):
        b = cols[(i + 1) % len(cols)]
        for k in range(3):                       # flanc exterieur, dessus, flanc interieur
            bm.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    lw.add_object(asset, "Ring", bm, coll, SHIELD)
    lw.update_manifest(asset, [
        {"object": "Ring", "color": SHIELD, "material": "Neon", "canCollide": False,
         "role": "fixed",
         "notes": "Anneau au sol sous le dome : diametre exterieur 10, bande 0,45, epaisseur "
                  "0,1, %d cotes alignes sur le bord de FX_Shield_Dome. Sans dessous. Origine = "
                  "base centree. A redimensionner avec le dome." % len(angles)}])
    path = lw.export_asset(asset, CATEGORY)
    lw.report(asset)
    lw.save_blend()
    return path
