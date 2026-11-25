"""Locksmith Wars - categorie ORE (gisements) + ING (lingot)."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import lw_common as lw

CATEGORY = "ORE"
ROCK_COLOR = "#6E6A66"


# ------------------------------------------------------------ primitives
def merge_bm(dst, src):
    """Ajoute la geometrie de `src` dans `dst` puis libere `src`."""
    tmp = bpy.data.meshes.new("__lw_tmp__")
    src.to_mesh(tmp)
    src.free()
    dst.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
    return dst


def rock_bm(scale, center, seed, subdiv=2, jitter=0.13, squash_top=None):
    """Rocher facette : icosphere deformee (graine fixe), base plate a z = 0."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    rng = random.Random(seed)
    cx, cy, cz = center
    for v in bm.verts:
        k = 1.0 + rng.uniform(-jitter, jitter)
        z = v.co.z * scale[2] * k + cz
        if squash_top is not None and z > squash_top:
            z = squash_top + (z - squash_top) * 0.35
        v.co = Vector((v.co.x * scale[0] * k + cx, v.co.y * scale[1] * k + cy, z))
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 0, 1),
                           clear_inner=True)
    bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def direction(az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    return Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))


def surface_hit(bvh, center, dirv):
    """Point et normale de la surface vus depuis l'exterieur dans la direction dirv."""
    loc, normal, _idx, _dist = bvh.ray_cast(Vector(center) + dirv * 20.0, -dirv)
    if loc is None:
        raise RuntimeError("rayon dans le vide : %s" % (tuple(dirv),))
    return loc, normal


def vein_bm(bm, loc, normal, length, width, angle_deg, seed,
            sink=0.35, lip=0.06, height=0.2, strata=(0.5, 0.3, 0.8)):
    """Veine de metal : plaque hexagonale allongee, chanfreinee, incrustee."""
    n = normal.normalized()
    r = Vector(strata)
    t = r - r.dot(n) * n
    if t.length < 1e-3:
        t = n.orthogonal()
    t = (Matrix.Rotation(math.radians(angle_deg), 3, n) @ t.normalized()).normalized()
    b = n.cross(t)
    rng = random.Random(seed)
    L, W = length, width
    outline = [(L / 2, 0), (L / 4, W / 2), (-L / 4, W / 2),
               (-L / 2, 0), (-L / 4, -W / 2), (L / 4, -W / 2)]
    outline = [(u + rng.uniform(-0.07, 0.07), v + rng.uniform(-0.05, 0.05)) for u, v in outline]
    rings = []
    for h, s in ((-sink, 1.0), (lip, 1.0), (height, 0.66)):
        rings.append([bm.verts.new(loc + t * (u * s) + b * (v * s) + n * h) for u, v in outline])
    k = len(outline)
    for lo, hi in zip(rings, rings[1:]):
        for i in range(k):
            j = (i + 1) % k
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    return bm


def ore_manifest(asset, material, extra=()):
    entries = [
        {"object": "Rock", "color": ROCK_COLOR, "material": "Slate", "canCollide": True,
         "role": "fixed", "notes": "Roche fixe. CollisionFidelity Hull."},
        {"object": "Crystals", "color": lw.TINT, "material": material, "canCollide": False,
         "role": "tint", "notes": "Etat intact. Recolore selon le metal."},
        {"object": "Crystals_Broken", "color": lw.TINT, "material": material, "canCollide": False,
         "role": "tint", "notes": "Etat fissure (50 % PV), remplace Crystals. Meme origine."},
    ]
    entries.extend(extra)
    lw.update_manifest(asset, entries)


# ---------------------------------------------------------------- ORE_F1
# (azimut, elevation, longueur, largeur, angle, garde dans la version cassee)
F1_VEINS = [
    (-90, 34, 1.55, 0.70, 18, False),
    (-48, 14, 1.25, 0.60, -25, True),
    (-138, 16, 1.30, 0.62, 30, False),
    (2, 40, 1.45, 0.66, -12, False),
    (178, 36, 1.40, 0.64, 22, True),
    (92, 30, 1.50, 0.68, -18, False),
    (-105, 68, 1.35, 0.62, 40, True),
    (55, 62, 1.25, 0.58, -35, False),
]


def build_ORE_F1():
    """F1 Commun (Fer, Cuivre) : roche + 8 veines plates incrustees. ~4,4 x 4,3 x 3."""
    asset = "ORE_F1"
    coll = lw.reset_collection(asset)

    rock = rock_bm((2.0, 1.95, 2.25), (0.0, 0.0, 0.95), seed=11, squash_top=2.75)
    merge_bm(rock, rock_bm((0.75, 0.7, 0.8), (1.45, -1.25, 0.3), seed=5, subdiv=1, jitter=0.1))
    merge_bm(rock, rock_bm((0.6, 0.65, 0.6), (-1.55, 1.0, 0.2), seed=8, subdiv=1, jitter=0.1))
    bvh = BVHTree.FromBMesh(rock)

    full, broken = bmesh.new(), bmesh.new()
    for i, (az, el, length, width, angle, keep) in enumerate(F1_VEINS):
        loc, normal = surface_hit(bvh, (0.0, 0.0, 1.0), direction(az, el))
        vein_bm(full, loc, normal, length, width, angle, seed=100 + i)
        if keep:
            vein_bm(broken, loc, normal, length * 0.8, width * 0.85, angle, seed=100 + i,
                    height=0.12)

    lw.add_object(asset, "Rock", rock, coll, ROCK_COLOR)
    lw.add_object(asset, "Crystals", full, coll, lw.TINT)
    lw.add_object(asset, "Crystals_Broken", broken, coll, lw.TINT)
    ore_manifest(asset, "Metal")
    return lw.export_asset(asset, CATEGORY)


# ------------------------------------------------- primitives cristaux
def top_hit(bvh, x, y):
    """Point de la surface de la roche a la verticale de (x, y)."""
    loc, _n, _i, _d = bvh.ray_cast(Vector((x, y, 30.0)), Vector((0.0, 0.0, -1.0)))
    if loc is None:
        raise RuntimeError("rien sous (%.2f, %.2f)" % (x, y))
    return loc


def prism_bm(loc, tilt, az, radius, vis, sink=0.7, sides=6, twist=0.0, tip=None,
             taper=0.8, cut=None):
    """Prisme facette a pointe nette, plante dans la roche.

    loc : point d'ancrage sur la surface ; tilt : inclinaison par rapport a la
    verticale (degres) vers l'azimut az ; vis : longueur visible hors roche ;
    sink : longueur enfoncee. cut = (hauteur visible, inclinaison, azimut de la
    coupe) : prisme casse, face de coupe plate.
    """
    a = direction(az, 90.0 - tilt)
    u = (Matrix.Rotation(math.radians(twist), 3, a) @ a.orthogonal().normalized()).normalized()
    v = a.cross(u)
    base = Vector(loc) - a * sink
    length = vis + sink
    tip = radius * 1.4 if tip is None else tip
    bm = bmesh.new()

    def ring(h, r):
        return [bm.verts.new(base + a * h + (u * math.cos(t) + v * math.sin(t)) * r)
                for t in (2.0 * math.pi * i / sides for i in range(sides))]

    lo, hi = ring(0.0, radius * taper), ring(length - tip, radius)
    apex = bm.verts.new(base + a * length)
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bm.faces.new((hi[i], hi[j], apex))
    bm.faces.new(list(reversed(lo)))
    if cut is not None:
        h, ctilt, caz = cut
        ct, ca = math.radians(ctilt), math.radians(caz)
        n = a * math.cos(ct) + (u * math.cos(ca) + v * math.sin(ca)) * math.sin(ct)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Vector(loc) + a * h, plane_no=n,
                               clear_outer=True)
        bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def bipyramid_bm(center, radius, up, down, sides=8, tilt=0.0, az=0.0, twist=0.0):
    """Double pyramide (gemme) : equateur de rayon `radius`, pointes a +up / -down."""
    a = direction(az, 90.0 - tilt)
    u = (Matrix.Rotation(math.radians(twist), 3, a) @ a.orthogonal().normalized()).normalized()
    v = a.cross(u)
    c = Vector(center)
    bm = bmesh.new()
    eq = [bm.verts.new(c + (u * math.cos(t) + v * math.sin(t)) * radius)
          for t in (2.0 * math.pi * i / sides for i in range(sides))]
    top, bot = bm.verts.new(c + a * up), bm.verts.new(c - a * down)
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((eq[i], eq[j], top))
        bm.faces.new((eq[j], eq[i], bot))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def lathe_bm(profile, sides=8, phase=22.5):
    """Solide de revolution facette. profile = [(rayon, z), ...] de bas en haut."""
    bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(t), r * math.sin(t), z))
              for t in (math.radians(phase) + 2.0 * math.pi * i / sides for i in range(sides))]
             for r, z in profile]
    for lo, hi in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def crystals_from(bvh, table, seed, keep=None, cuts=None):
    """Assemble les prismes de `table` : (x, y, tilt, az, rayon, visible, enfonce).

    keep : indices conserves (None = tous) ; cuts : {indice: (h, tilt, az)}.
    """
    out = bmesh.new()
    rng = random.Random(seed)
    for i, (x, y, tilt, az, radius, vis, sink) in enumerate(table):
        twist = rng.uniform(0.0, 60.0)
        if keep is not None and i not in keep:
            continue
        cut = cuts.get(i) if cuts else None
        merge_bm(out, prism_bm(top_hit(bvh, x, y), tilt, az, radius, vis, sink=sink,
                               twist=twist, cut=cut))
    return out


def finish(asset, category=CATEGORY):
    path = lw.export_asset(asset, category)
    lw.report(asset)
    lw.save_blend()
    return path


# ---------------------------------------------------------------- ORE_F2
# (x, y, inclinaison, azimut, rayon, longueur visible, longueur enfoncee)
F2_PRISMS = [
    (-0.35, -0.45, 15, 115, 0.74, 2.25, 1.0),
    (1.00, -0.55, 28, -15, 0.60, 1.80, 1.0),
    (-1.20, 0.15, 26, 185, 0.54, 1.50, 0.9),
]
F2_CUTS = {0: (1.05, 14, 40), 1: (0.85, 12, 200), 2: (0.70, 16, 120)}


def build_ORE_F2():
    """F2 Peu commun (Argent, Or) : roche ronde + 3 prismes hexagonaux inclines."""
    asset = "ORE_F2"
    coll = lw.reset_collection(asset)
    rock = rock_bm((2.0, 2.0, 2.3), (0.0, 0.0, 0.95), seed=23, jitter=0.085)
    merge_bm(rock, rock_bm((0.7, 0.7, 0.75), (-1.5, -1.2, 0.3), seed=6, subdiv=1, jitter=0.1))
    merge_bm(rock, rock_bm((0.6, 0.6, 0.6), (1.5, 1.15, 0.2), seed=9, subdiv=1, jitter=0.1))
    bvh = BVHTree.FromBMesh(rock)
    full = crystals_from(bvh, F2_PRISMS, seed=20)
    broken = crystals_from(bvh, F2_PRISMS, seed=20, cuts=F2_CUTS)
    lw.add_object(asset, "Rock", rock, coll, ROCK_COLOR)
    lw.add_object(asset, "Crystals", full, coll, lw.TINT)
    lw.add_object(asset, "Crystals_Broken", broken, coll, lw.TINT)
    ore_manifest(asset, "Metal")
    return finish(asset)


# ---------------------------------------------------------------- ORE_F3
F3_PRISMS = [
    (0.00, 0.10, 4, 80, 0.80, 4.40, 1.1),
    (0.95, -0.40, 22, -20, 0.52, 2.60, 0.9),
    (-0.90, -0.50, 26, 200, 0.47, 2.20, 0.9),
    (0.30, 1.00, 24, 75, 0.43, 1.90, 0.8),
    (-0.80, 0.80, 32, 135, 0.38, 1.45, 0.7),
    (0.20, -1.15, 34, -85, 0.34, 1.10, 0.7),
    (1.35, 0.55, 40, 20, 0.30, 0.90, 0.6),
]
F3_CUTS = {0: (1.25, 16, 30)}
F3_KEEP = (0, 4, 5, 6)


def build_ORE_F3():
    """F3 Rare (Cobalt, Titane) : socle bas + grappe de 7 prismes, un grand central."""
    asset = "ORE_F3"
    coll = lw.reset_collection(asset)
    rock = rock_bm((2.05, 2.05, 1.7), (0.0, 0.0, 0.45), seed=31, jitter=0.11, squash_top=1.6)
    merge_bm(rock, rock_bm((0.7, 0.65, 0.6), (1.55, -1.1, 0.2), seed=4, subdiv=1, jitter=0.1))
    merge_bm(rock, rock_bm((0.6, 0.6, 0.5), (-1.6, 0.9, 0.15), seed=7, subdiv=1, jitter=0.1))
    bvh = BVHTree.FromBMesh(rock)
    full = crystals_from(bvh, F3_PRISMS, seed=30)
    broken = crystals_from(bvh, F3_PRISMS, seed=30, keep=F3_KEEP, cuts=F3_CUTS)
    lw.add_object(asset, "Rock", rock, coll, ROCK_COLOR)
    lw.add_object(asset, "Crystals", full, coll, lw.TINT)
    lw.add_object(asset, "Crystals_Broken", broken, coll, lw.TINT)
    ore_manifest(asset, "Glass")
    return finish(asset)


# ---------------------------------------------------------------- ORE_F4
F4_PEDESTAL = [(1.30, 0.0), (1.30, 0.33), (1.18, 0.45), (0.95, 0.45), (0.95, 1.00),
               (1.15, 1.12), (1.15, 1.38), (1.03, 1.50)]
F4_TOP = 1.5            # dessus du piedestal
F4_CORE_CENTER = (0.0, 0.0, F4_TOP + 1.0 + 2.0)   # flotte 1 stud au-dessus, demi-hauteur 2
F4_RING_RADIUS = 2.0
F4_PRISMS = [
    (0.00, -0.72, 24, -90, 0.37, 1.50, 0.5),
    (0.62, 0.36, 24, 30, 0.37, 1.50, 0.5),
    (-0.62, 0.36, 24, 150, 0.37, 1.50, 0.5),
]
F4_CUTS = {0: (0.60, 14, 60), 1: (0.60, 12, 180), 2: (0.60, 15, 300)}
# (x, y), (rayon, demi-hauteur), graine
F4_ROCKS = [((1.15, -0.95), (0.55, 0.75), 3), ((-1.30, -0.40), (0.50, 0.60), 5),
            ((-0.75, 1.20), (0.60, 0.85), 12), ((1.20, 0.85), (0.45, 0.55), 14)]


def build_ORE_F4():
    """F4 Epique/Legendaire : piedestal octogonal + noyau flottant + 4 eclats en orbite."""
    asset = "ORE_F4"
    coll = lw.reset_collection(asset)
    rock = lathe_bm(F4_PEDESTAL, sides=8)
    for (x, y), (sx, sz), seed in F4_ROCKS:
        merge_bm(rock, rock_bm((sx, sx, sz), (x, y, 0.2), seed=seed, subdiv=1, jitter=0.12))
    bvh = BVHTree.FromBMesh(rock)
    full = crystals_from(bvh, F4_PRISMS, seed=40)
    broken = crystals_from(bvh, F4_PRISMS, seed=40, cuts=F4_CUTS)
    core = bipyramid_bm(F4_CORE_CENTER, 0.75, 2.0, 2.0, sides=8)
    shards = bmesh.new()
    cz = F4_CORE_CENTER[2]
    for i in range(4):
        t = math.radians(45.0 + 90.0 * i)
        c = (F4_RING_RADIUS * math.cos(t), F4_RING_RADIUS * math.sin(t), cz)
        merge_bm(shards, bipyramid_bm(c, 0.2, 0.4, 0.4, sides=6, tilt=14,
                                      az=math.degrees(t) + 90.0, twist=30.0 * i))
    lw.add_object(asset, "Rock", rock, coll, ROCK_COLOR)
    lw.add_object(asset, "Crystals", full, coll, lw.TINT)
    lw.add_object(asset, "Crystals_Broken", broken, coll, lw.TINT)
    lw.add_object(asset, "Core", core, coll, lw.TINT, origin=F4_CORE_CENTER)
    lw.add_object(asset, "Shards", shards, coll, lw.TINT, origin=F4_CORE_CENTER)
    pos = ("origine Blender (0, 0, %.1f) = Roblox (0, %.1f, 0) par rapport a la base de Rock"
           % (cz, cz))
    ore_manifest(asset, "Neon", [
        {"object": "Core", "color": lw.TINT, "material": "Neon", "canCollide": False,
         "role": "tint",
         "notes": "Noyau flottant, piece separee ; flotte ±0,3 stud, 2 s. Pivot = centre "
                  "geometrique, " + pos + "."},
        {"object": "Shards", "color": lw.TINT, "material": "Neon", "canCollide": False,
         "role": "tint",
         "notes": "4 eclats en anneau Ø 4, piece separee ; tourne 4 s/tour autour de l'axe "
                  "vertical. Pivot = centre de l'anneau sur l'axe du noyau, " + pos + "."},
    ])
    return finish(asset)


# ------------------------------------------------------------ ORE_Rubble
# (x, y, rayon horizontal, demi-hauteur, graine)
RUBBLE_ROCKS = [
    (-0.30, 0.10, 0.80, 0.72, 51), (1.15, -0.70, 0.60, 0.62, 52), (-1.30, -0.85, 0.55, 0.50, 53),
    (0.90, 1.05, 0.65, 0.55, 54), (-1.20, 1.10, 0.50, 0.45, 55), (0.10, -1.45, 0.42, 0.38, 56),
    (1.55, 0.25, 0.38, 0.35, 57),
]


def build_ORE_Rubble():
    """Debris (gisement epuise) : 7 petites roches eparpillees dans ~4 x 4 x 0,8."""
    asset = "ORE_Rubble"
    coll = lw.reset_collection(asset)
    bm = bmesh.new()
    for x, y, r, h, seed in RUBBLE_ROCKS:
        merge_bm(bm, rock_bm((r, r * 0.92, h), (x, y, h * 0.12), seed=seed, subdiv=1, jitter=0.14))
    lw.add_object(asset, "Rubble", bm, coll, ROCK_COLOR)
    lw.update_manifest(asset, [
        {"object": "Rubble", "color": ROCK_COLOR, "material": "Slate", "canCollide": False,
         "role": "fixed",
         "notes": "Etat epuise (0 PV), remplace tout le gisement. Partage par les 4 familles. "
                  "Origine = base centree."}])
    return finish(asset)


# ------------------------------------------------------------- ORE_Chunk
def build_ORE_Chunk():
    """Eclat de minerai : petite icosphere deformee Ø ~0,8, origine au centre."""
    asset = "ORE_Chunk"
    coll = lw.reset_collection(asset)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.5)
    rng = random.Random(61)
    for v in bm.verts:
        v.co = Vector((v.co.x, v.co.y * 0.9, v.co.z * 0.85)) * (1.0 + rng.uniform(-0.2, 0.12))
    lo = Vector([min(v.co[k] for v in bm.verts) for k in range(3)])
    hi = Vector([max(v.co[k] for v in bm.verts) for k in range(3)])
    bmesh.ops.translate(bm, verts=bm.verts, vec=-(lo + hi) / 2.0)   # origine = centre
    lw.add_object(asset, "Chunk", bm, coll, lw.TINT)
    lw.update_manifest(asset, [
        {"object": "Chunk", "color": lw.TINT, "material": "Metal", "canCollide": False,
         "role": "tint",
         "notes": "Eclat recolore selon le metal (materiau de la famille : F1-F2 Metal, "
                  "F3 Glass, F4 Neon). Origine = centre."}])
    return finish(asset)
