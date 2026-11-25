"""Locksmith Wars - categorie LCK (serrures clipsees sur LockSocket).

Contrat : origine de TOUTES les pieces = centre de la face arriere de la serrure (plan y = 0),
la serrure s'etend vers -Y (avant). Rien ne depasse derriere y = 0. La piece recoloree selon le
metal s'appelle `Tint` (#D0D0D0) ; le jeu lui applique couleur et materiau (Metal, Glass, Neon) :
elle doit se lire par sa silhouette et ses reliefs, pas par l'ombrage.
Encombrement : zone libre 2,6 x 2,6 autour de LockSocket (±1,3 en X et Z), epaisseur <= 0,7.
"""
import math

import bmesh
from mathutils import Vector

import lw_common as lw
import frg

CATEGORY = "LCK"
STEEL = "#5A5F66"
STEEL_DARK = "#3B3F45"
BRASS = "#C9A14A"
GOLD = "#F2C12E"
DARK = "#1E1E1E"
ZONE = 1.3                                # demi-cote de la zone libre autour de LockSocket


def plate_bm(bm, half_x, z0, z1, depth, corner=0.18, lip=0.1):
    """Bloc a silhouette octogonale (coins coupes de `corner`) pose contre y = 0, avant a
    y = -depth, arete avant chanfreinee de `lip`. Dos plat."""
    c = corner
    outline = [(-half_x + c, z0), (half_x - c, z0), (half_x, z0 + c), (half_x, z1 - c),
               (half_x - c, z1), (-half_x + c, z1), (-half_x, z1 - c), (-half_x, z0 + c)]
    cx, cz = 0.0, (z0 + z1) / 2.0
    kx = (half_x - lip) / half_x
    kz = ((z1 - z0) / 2.0 - lip) / ((z1 - z0) / 2.0)
    rings = [[bm.verts.new((x, 0.0, z)) for x, z in outline],
             [bm.verts.new((x, -(depth - lip), z)) for x, z in outline],
             [bm.verts.new((cx + (x - cx) * kx, -depth, cz + (z - cz) * kz)) for x, z in outline]]
    n = len(outline)
    for lo, hi in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    return bm


def tube_bm(bm, path, radius, y, sides=6):
    """Tube facette le long d'un chemin (x, z) dans le plan y = `y`, bouts fermes."""
    pts = [Vector((x, y, z)) for x, z in path]
    yv = Vector((0.0, 1.0, 0.0))
    rings = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        nv = yv.cross(t).normalized()
        # coude : on elargit la section pour garder le diametre dans les segments
        k = 1.0
        if 0 < i < len(pts) - 1:
            half = (p - a).normalized().angle((b - p).normalized()) / 2.0
            k = 1.0 / max(math.cos(half), 0.5)
        rings.append([bm.verts.new(p + radius * (math.cos(s) * nv * k + math.sin(s) * yv))
                      for s in (2.0 * math.pi * (j + 0.5) / sides for j in range(sides))])
    for lo, hi in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    return bm


def shell_bm(bm, outline, y_back, y_front, lip=0.0, center=None, back=True):
    """Relief pose sur la plaque : contour (x, z) extrude de y_back a y_front (vers -Y), arete
    avant chanfreinee de `lip` (chaque sommet rentre de `lip` vers `center`). Volume ferme (les
    normales se recalculent sans ambiguite) ; le dos est retire ensuite par add_relief."""
    n = len(outline)
    if center is None:
        center = (sum(x for x, _z in outline) / n, sum(z for _x, z in outline) / n)
    c = Vector((center[0], 0.0, center[1]))
    rings = [[bm.verts.new((x, y_back, z)) for x, z in outline]]
    if lip > 0.0:
        rings.append([bm.verts.new((x, y_front + lip, z)) for x, z in outline])
        front = []
        for x, z in outline:
            d = Vector((x, 0.0, z)) - c
            q = c + d * max(0.0, 1.0 - lip / max(d.length, 1e-6))
            front.append(bm.verts.new((q.x, y_front, q.z)))
        rings.append(front)
    else:
        rings.append([bm.verts.new((x, y_front, z)) for x, z in outline])
    for lo, hi in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(rings[-1])
    if back:
        bm.faces.new(list(reversed(rings[0])))
    return bm


def ngon(cx, cz, radius, sides, phase_deg=0.0):
    """Contour (x, z) d'un polygone regulier centre en (cx, cz)."""
    return [(cx + radius * math.cos(math.radians(phase_deg) + 2.0 * math.pi * i / sides),
             cz + radius * math.sin(math.radians(phase_deg) + 2.0 * math.pi * i / sides))
            for i in range(sides)]


def add_relief(asset, part, bm, coll, color, origin=(0.0, 0.0, 0.0)):
    """add_object pour un relief pose contre la plaque : normales calculees sur le volume ferme,
    puis suppression des faces de dos (normale +Y), jamais visibles."""
    ob = lw.add_object(asset, part, bm, coll, color, origin=origin)
    work = bmesh.new()
    work.from_mesh(ob.data)
    work.normal_update()
    bmesh.ops.delete(work, geom=[f for f in work.faces if f.normal.y > 0.9], context="FACES")
    work.to_mesh(ob.data)
    work.free()
    return ob


def check_envelope(coll, depth_max=0.7):
    """Contrat LCK : rien derriere y = 0, facade dans la zone libre 2,6 x 2,6, epaisseur bornee,
    et aucune face des reliefs a dos ouvert ne regarde vers l'arriere (normales sorties)."""
    for ob in lw.meshes(coll.all_objects):
        lo, hi = lw.world_bounds(ob)
        assert hi.y <= 1e-6, "%s depasse derriere y = 0" % ob.name
        assert max(abs(lo.x), abs(hi.x), abs(lo.z), abs(hi.z)) <= ZONE, "%s sort de la zone" % ob.name
        assert lo.y >= -depth_max - 1e-6, "%s : epaisseur > %.2f" % (ob.name, depth_max)
        if ob["lw_part"] != "Tint":
            assert not any(q.normal.y > 0.5 for q in ob.data.polygons), \
                "%s : normales inversees" % ob.name


def finish(asset, entries, export=True):
    """export=False : met seulement le manifest a jour (notes), sans toucher au FBX."""
    lw.update_manifest(asset, entries)
    path = lw.export_asset(asset, CATEGORY) if export else None
    lw.report(asset)
    lw.save_blend()
    return path


# ----------------------------------------------------------------- LCK_T1
T1_BODY = (0.70, -0.60, 0.60, 0.60)       # demi-largeur, z bas, z haut, epaisseur
T1_BAND = (0.75, 0.24, 0.46, 0.66)        # sangle forgee en relief, deborde de 0,05 sur les cotes
T1_SHACKLE_R = 0.13                       # rayon du fer de l'anse
T1_SHACKLE_X = 0.38                       # demi-entraxe des branches
T1_SHACKLE_Z = (0.20, 0.75)               # pied des branches (dans le corps), centre de l'arc
T1_KEYHOLE = [(-0.12, -0.36), (0.12, -0.36), (0.055, -0.12), (0.16, -0.03), (0.16, 0.10),
              (0.07, 0.20), (-0.07, 0.20), (-0.16, 0.10), (-0.16, -0.03), (-0.055, -0.12)]
T1_KEYHOLE_DZ = -0.14


def build_lck_t1():
    """LCK_T1 : cadenas rustique. Tint (corps + sangle), Shackle (anse acier), Keyhole (entree de cle)."""
    asset = "LCK_T1"
    coll = lw.reset_collection(asset)

    tint = bmesh.new()
    hx, z0, z1, depth = T1_BODY
    plate_bm(tint, hx, z0, z1, depth, corner=0.2, lip=0.1)
    hx, z0, z1, depth = T1_BAND
    plate_bm(tint, hx, z0, z1, depth, corner=0.06, lip=0.05)

    shackle = bmesh.new()
    zf, zc = T1_SHACKLE_Z
    r = T1_SHACKLE_X
    path = [(-r, zf)] + [(-r * math.cos(math.pi * k / 6.0), zc + r * math.sin(math.pi * k / 6.0))
                         for k in range(7)] + [(r, zf)]
    tube_bm(shackle, path, T1_SHACKLE_R, y=-T1_BODY[3] / 2.0)

    keyhole = bmesh.new()
    frg.prism_y_bm(keyhole, [(x, z + T1_KEYHOLE_DZ) for x, z in T1_KEYHOLE], -0.64, -0.45)
    frg.tri_ngons(keyhole)

    lw.add_object(asset, "Tint", tint, coll, lw.TINT)
    lw.add_object(asset, "Shackle", shackle, coll, STEEL)
    lw.add_object(asset, "Keyhole", keyhole, coll, DARK)
    for ob in lw.meshes(coll.all_objects):
        lo, hi = lw.world_bounds(ob)
        assert hi.y <= 1e-6, "%s depasse derriere y = 0" % ob.name
        assert max(abs(lo.x), abs(hi.x), abs(lo.z), abs(hi.z)) <= 1.3, "%s sort de ±1,3" % ob.name
        assert lo.y >= -0.7 - 1e-6, "%s : epaisseur > 0,7" % ob.name
    return finish(asset, t1_entries())


def t1_entries():
    return [
        {"object": "Tint", "color": lw.TINT, "material": "Metal", "canCollide": False,
         "role": "tint",
         "notes": "Corps du cadenas 1,4 x 1,2 x 0,6 + sangle en relief (1,5 de large, avant a "
                  "0,66). Recolore selon le metal. Origine = centre de la face arriere du corps "
                  "(a poser sur LockSocket), avant vers -Z Roblox. Facade totale avec l'anse : "
                  "1,5 x 1,85 (de Y = -0,60 a +1,25 Roblox), dans la zone libre 2,6 x 2,6."},
        {"object": "Shackle", "color": STEEL, "material": "Metal", "canCollide": False,
         "role": "fixed",
         "notes": "Anse acier (fer diam. 0,26, largeur 0,99), sommet a Y = +1,25 Roblox au-dessus "
                  "de l'origine ; branches enfoncees de 0,4 dans le corps (peut se soulever de "
                  "0,3 a l'ouverture sans se detacher). Meme origine que Tint."},
        {"object": "Keyhole", "color": DARK, "material": "SmoothPlastic", "canCollide": False,
         "role": "fixed",
         "notes": "Entree de cle sombre, depasse la face avant du corps de 0,04. Meme origine que Tint."},
    ]


# ----------------------------------------------------------------- LCK_T2
T2_PLATE = (0.90, -1.10, 1.10, 0.30)      # demi-largeur, z bas, z haut, epaisseur
T2_SCREW = (0.62, 0.84, 0.13)             # |x|, |z|, rayon des vis (6 cotes)
T2_COLLAR_R = 0.56                        # rosace laiton autour du barillet
T2_TAB = (0.28, -0.80, -0.90)             # demi-largeur, z du pan coupe, z bas (profil "europeen")
T2_CYL_R = 0.40                           # barillet diam. 0,8, 12 cotes
T2_KEYWAY = [(-0.08, -0.26), (0.08, -0.26), (0.08, 0.20), (0.0, 0.30), (-0.08, 0.20)]


def build_lck_t2():
    """LCK_T2 : serrure a barillet. Tint (plaque), Trim (rosace + 4 vis laiton), Cylinder (barillet
    acier, tourne), Keyway (fente de cle sombre, tourne avec Cylinder)."""
    asset = "LCK_T2"
    coll = lw.reset_collection(asset)

    tint = bmesh.new()
    hx, z0, z1, depth = T2_PLATE
    plate_bm(tint, hx, z0, z1, depth, corner=0.22, lip=0.08)

    trim = bmesh.new()
    r = T2_COLLAR_R
    hw, zc, zb = T2_TAB
    a0 = math.degrees(math.acos(hw / r))          # raccord de la patte sur le cercle
    arc = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
           for a in [-a0 + (180.0 + 2.0 * a0) * k / 10.0 for k in range(11)]]
    outline = arc + [(-hw, zc), (-hw + 0.10, zb), (hw - 0.10, zb), (hw, zc)]
    shell_bm(trim, outline, -0.28, -0.38, lip=0.04, center=(0.0, 0.0))
    sx, sz, sr = T2_SCREW
    for kx in (-1.0, 1.0):
        for kz in (-1.0, 1.0):
            shell_bm(trim, ngon(kx * sx, kz * sz, sr, 6, 30.0), -0.28, -0.38)
    frg.tri_ngons(trim)

    cyl = bmesh.new()
    shell_bm(cyl, ngon(0.0, 0.0, T2_CYL_R, 12, 15.0), -0.36, -0.47, lip=0.04)
    frg.tri_ngons(cyl)

    keyway = bmesh.new()
    shell_bm(keyway, T2_KEYWAY, -0.45, -0.50, center=(0.0, 0.0))
    frg.tri_ngons(keyway)

    lw.add_object(asset, "Tint", tint, coll, lw.TINT)
    add_relief(asset, "Trim", trim, coll, BRASS)
    add_relief(asset, "Cylinder", cyl, coll, STEEL)
    add_relief(asset, "Keyway", keyway, coll, DARK)
    check_envelope(coll)
    return finish(asset, [
        {"object": "Tint", "color": lw.TINT, "material": "Metal", "canCollide": False,
         "role": "tint",
         "notes": "Plaque 1,8 x 2,2 x 0,3 a coins coupes. Recoloree selon le metal. Origine = "
                  "centre de la face arriere (a poser sur LockSocket), avant vers -Z Roblox."},
        {"object": "Trim", "color": BRASS, "material": "Metal", "canCollide": False,
         "role": "fixed",
         "notes": "Laiton : rosace de barillet (diam. 1,12 + patte vers le bas) et 4 vis 6 pans "
                  "aux coins, avant a 0,38. Dos ouvert (contre la plaque). Meme origine que Tint."},
        {"object": "Cylinder", "color": STEEL, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Barillet acier diam. 0,8 (12 cotes), avant a 0,47. Peut tourner de 90 deg a "
                  "l'ouverture autour de l'axe Z Roblox passant par son origine. Origine = "
                  "centre de la face arriere de la serrure (son axe passe par LockSocket)."},
        {"object": "Keyway", "color": DARK, "material": "SmoothPlastic", "canCollide": False,
         "role": "moving",
         "notes": "Fente de cle sombre 0,16 x 0,56, depasse le barillet de 0,03. Tourne AVEC "
                  "Cylinder (meme origine, meme axe)."},
    ])


# ----------------------------------------------------------------- LCK_T3
T3_PLATE = (1.20, -1.20, 1.20, 0.30)
T3_DIAL_C = (0.0, 0.24)                   # axe du cadran (x, z)
T3_DIAL_R = (0.62, 0.54)                  # rayon des crans / des encoches (12 crans, 24 sommets)
T3_BEZEL_R = 0.86
T3_BOLT = (0.86, 0.86, 0.14)              # |x|, |z|, rayon des boulons de coin
T3_LEVER_HUB = (-0.45, -0.88)             # axe du levier (x, z)
T3_LEVER_TIP = (0.58, -0.88)
T3_INDEX = [(-0.16, 1.16), (0.16, 1.16), (0.0, 0.88)]
T3_TICK = (0.83, 0.67, 0.055)             # rayon de la base, rayon de la pointe, demi-largeur


def build_lck_t3():
    """LCK_T3 : serrure a combinaison. Tint (plaque), Bezel (lunette + 4 boulons, acier sombre),
    Dial (cadran crante, tourne), Lever (levier, tourne), Index (repere or fixe)."""
    asset = "LCK_T3"
    coll = lw.reset_collection(asset)
    cx, cz = T3_DIAL_C

    tint = bmesh.new()
    hx, z0, z1, depth = T3_PLATE
    plate_bm(tint, hx, z0, z1, depth, corner=0.34, lip=0.10)

    bezel = bmesh.new()
    shell_bm(bezel, ngon(cx, cz, T3_BEZEL_R, 12, 15.0), -0.28, -0.38)
    bx, bz, br = T3_BOLT
    for kx in (-1.0, 1.0):
        for kz in (-1.0, 1.0):
            shell_bm(bezel, ngon(kx * bx, kz * bz, br, 6, 30.0), -0.28, -0.39)
    frg.tri_ngons(bezel)

    dial = bmesh.new()
    r_out, r_in = T3_DIAL_R
    rim = [(cx + (r_out if i % 2 == 0 else r_in) * math.cos(math.radians(90.0 + 15.0 * i)),
            cz + (r_out if i % 2 == 0 else r_in) * math.sin(math.radians(90.0 + 15.0 * i)))
           for i in range(24)]
    shell_bm(dial, rim, -0.36, -0.50, center=(cx, cz))
    shell_bm(dial, ngon(cx, cz, 0.24, 8, 22.5), -0.48, -0.62)                    # bouton central
    shell_bm(dial, [(cx - 0.05, cz + 0.24), (cx + 0.05, cz + 0.24), (cx + 0.05, cz + 0.56),
                    (cx - 0.05, cz + 0.56)], -0.48, -0.54)                        # repere en relief
    frg.tri_ngons(dial)

    lever = bmesh.new()
    (ax, az), (tx, tz) = T3_LEVER_HUB, T3_LEVER_TIP
    shell_bm(lever, ngon(ax, az, 0.20, 6, 0.0), -0.28, -0.48)
    shell_bm(lever, [(ax, az - 0.12), (tx - 0.08, tz - 0.08), (tx, tz), (tx - 0.08, tz + 0.08),
                     (ax, az + 0.12)], -0.33, -0.44)                              # bras effile
    frg.tri_ngons(lever)

    index = bmesh.new()
    shell_bm(index, T3_INDEX, -0.28, -0.46)
    rb, rt, hw = T3_TICK
    for k in range(1, 12):                        # 11 graduations ; la 12e est le repere du haut
        a = math.radians(90.0 + 30.0 * k)
        ux, uz = math.cos(a), math.sin(a)
        shell_bm(index, [(cx + rb * ux - hw * uz, cz + rb * uz + hw * ux),
                         (cx + rb * ux + hw * uz, cz + rb * uz - hw * ux),
                         (cx + rt * ux, cz + rt * uz)], -0.36, -0.42)

    lw.add_object(asset, "Tint", tint, coll, lw.TINT)
    add_relief(asset, "Bezel", bezel, coll, STEEL_DARK)
    add_relief(asset, "Dial", dial, coll, STEEL, origin=(cx, 0.0, cz))
    add_relief(asset, "Lever", lever, coll, STEEL, origin=(ax, 0.0, az))
    add_relief(asset, "Index", index, coll, GOLD)
    check_envelope(coll)
    return finish(asset, [
        {"object": "Tint", "color": lw.TINT, "material": "Metal", "canCollide": False,
         "role": "tint",
         "notes": "Plaque 2,4 x 2,4 x 0,3 a grands coins coupes. Recoloree selon le metal. "
                  "Origine = centre de la face arriere (a poser sur LockSocket), avant vers -Z "
                  "Roblox."},
        {"object": "Bezel", "color": STEEL_DARK, "material": "Metal", "canCollide": False,
         "role": "fixed",
         "notes": "Acier sombre : lunette diam. 1,72 sous le cadran + 4 boulons 6 pans aux "
                  "coins. Dos ouvert (contre la plaque). Meme origine que Tint."},
        {"object": "Dial", "color": STEEL, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Cadran diam. 1,24 a 12 crans, bouton central et repere en relief, "
                  "avant a 0,62. Tourne pendant le crochetage autour de l'axe Z Roblox passant "
                  "par son origine. Origine = son axe, dans le plan arriere : (0, +0,24, 0) "
                  "Roblox par rapport a Tint."},
        {"object": "Lever", "color": STEEL, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Levier acier (moyeu + bras effile de 1,03), avant a 0,48. Peut pivoter a "
                  "l'ouverture autour de l'axe Z Roblox passant par son origine. Origine = axe du "
                  "moyeu, dans le plan arriere : (+0,45, -0,88, 0) Roblox par rapport a Tint "
                  "(X Blender -0,45 = X Roblox +0,45)."},
        {"object": "Index", "color": GOLD, "material": "Metal", "canCollide": False,
         "role": "fixed",
         "notes": "Or, fixe : repere (triangle pointe en bas) au-dessus du cadran + 11 graduations "
                  "triangulaires sur la lunette, tous les 30 deg. Meme origine que Tint."},
    ])
