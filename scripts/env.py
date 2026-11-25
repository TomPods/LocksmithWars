"""Locksmith Wars - lot 6, environnement (MIN_*, ENV_*).

La mine reprend la matiere de la roche d'ORE_F1 (Slate #6E6A66, icosphere
deformee a facettes franches). Pour ne pas etre confondus avec un gisement
sans cristaux (dome arrondi), les rochers decoratifs sont des blocs TAILLES :
memes facettes triangulaires, mais recoupees par de grands plans francs aux
aretes biseautees. A = bloc dresse incline ; B et C seront d'autres silhouettes
(pas des agrandissements).
"""
import math
import random

import bmesh
from mathutils import Matrix, Vector

import lw_common as lw
import ore

ROCK_COLOR = ore.ROCK_COLOR      # #6E6A66, roche d'ORE_F1
BEVEL = 0.14                     # biseau des aretes taillees (stud)


def category(asset):
    """La categorie d'export est le prefixe du nom : MIN_Rock_Deco_A -> MIN."""
    return asset.split("_", 1)[0]


def _cut(bm, co, no):
    """Coupe franche : supprime ce qui depasse du plan (co, no) et rebouche.

    Renvoie les faces de coupe creees.
    """
    before = set(bm.faces)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=Vector(no).normalized(),
                           clear_outer=True)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    return [f for f in bm.faces if f not in before and len(f.verts) > 3]


def cut_block_bm(scale, cuts, seed, jitter=0.12, subdiv=1, bevel=BEVEL):
    """Bloc taille, centre sur l'origine (a incliner et poser ensuite).

    Icosphere deformee (graine fixe, comme la roche d'ORE_F1) recoupee par les
    plans `cuts` = [((x, y, z), (nx, ny, nz)), ...] ; les aretes entre deux
    faces de coupe recoivent un biseau d'un segment.
    """
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    rng = random.Random(seed)
    for v in bm.verts:
        k = 1.0 + rng.uniform(-jitter, jitter)
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) * k
    cut_faces = set()
    for co, no in cuts:
        cut_faces = {f for f in cut_faces if f.is_valid}
        cut_faces.update(_cut(bm, co, no))
    cut_faces = {f for f in cut_faces if f.is_valid}
    if bevel:
        edges = [e for e in bm.edges
                 if len(e.link_faces) == 2 and all(f in cut_faces for f in e.link_faces)]
        if edges:
            bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=1, affect="EDGES",
                            clamp_overlap=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def place_bm(bm, tilt_deg, az_deg, turn_deg, location):
    """Incline le bloc de tilt_deg vers l'azimut az_deg, le tourne, le pose en `location`."""
    az = math.radians(az_deg)
    axis = Vector((-math.sin(az), math.cos(az), 0.0))       # horizontal, perpendiculaire a az
    mat = (Matrix.Translation(Vector(location))
           @ Matrix.Rotation(math.radians(tilt_deg), 4, axis)
           @ Matrix.Rotation(math.radians(turn_deg), 4, "Z"))
    bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
    return bm


def ground_bm(bm):
    """Base plate a z = 0 : rien ne descend sous le sol."""
    _cut(bm, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def center_xy(bm):
    """Recentre l'emprise au sol sur l'origine (pivot = base centree)."""
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    off = Vector((-(min(xs) + max(xs)) / 2.0, -(min(ys) + max(ys)) / 2.0, 0.0))
    bmesh.ops.translate(bm, verts=bm.verts, vec=off)
    return bm


def rock_manifest(asset, notes):
    lw.update_manifest(asset, [
        {"object": "Rock", "color": ROCK_COLOR, "material": "Slate", "canCollide": True,
         "role": "fixed", "notes": notes}])


def finish(asset):
    path = lw.export_asset(asset, category(asset))
    lw.report(asset)
    lw.save_blend()
    return path


# ------------------------------------------------------- MIN_Rock_Deco_A
# Bloc dresse : plans de coupe dans le repere du bloc (avant inclinaison).
ROCK_A_SCALE = (1.55, 1.3, 2.3)
ROCK_A_CUTS = [
    ((0.0, 0.0, 1.50), (0.60, -0.15, 1.0)),     # dessus en biais
    ((0.0, -0.74, 0.0), (0.08, -1.0, 0.14)),    # grande face avant
    ((0.98, 0.0, 0.0), (1.0, 0.15, -0.12)),     # flanc droit
    ((-1.02, 0.0, 0.6), (-1.0, 0.10, 0.40)),    # epaule gauche (le bas reste brut)
]


def build_min_rock_deco_a():
    """MIN_Rock_Deco_A : rocher decoratif Ø ~3, bloc taille dresse et incline + petite roche au pied."""
    asset = "MIN_Rock_Deco_A"
    coll = lw.reset_collection(asset)
    bm = cut_block_bm(ROCK_A_SCALE, ROCK_A_CUTS, seed=71)
    place_bm(bm, tilt_deg=21.0, az_deg=180.0, turn_deg=-14.0, location=(0.25, 0.0, 0.72))
    ground_bm(bm)
    # petite roche au pied : exactement la recette des roches satellites d'ORE_F1
    chip = ore.rock_bm((0.62, 0.56, 0.6), (1.2, -0.92, 0.18), seed=5, subdiv=1, jitter=0.1)
    ore.merge_bm(bm, chip)
    center_xy(bm)
    lw.add_object(asset, "Rock", bm, coll, ROCK_COLOR)
    rock_manifest(asset, "Rocher decoratif Ø 3 (bloc taille incline + petite roche). CollisionFidelity "
                         "Hull. Origine = base centree.")
    return finish(asset)


# ===================================================================== suite du lot 6
import bpy          # noqa: E402
import frg          # noqa: E402  (block_bm, lathe_z_bm, prism_y_bm, boolean_cut, tri_ngons)

WOOD = "#8B5A2B"
WOOD_DARK = "#5C3A1E"
STEEL = "#5A5F66"
STEEL_DARK = "#3B3F45"
BRASS = "#C9A14A"
GOLD = "#F2C12E"            # recompenses uniquement
CONCRETE = "#737A84"
SCREEN = "#1E1E1E"
MASK = "#2A2A2A"
LANTERN = "#FFD966"         # seule teinte nouvelle du lot (jaune lanterne, l'or reste reserve)
SPAWN = "#4FC3FF"           # bleu du bouclier


def finish_entries(asset, entries):
    lw.update_manifest(asset, entries)
    return finish(asset)


def entry(obj, color, material, collide, notes, role="fixed"):
    return {"object": obj, "color": color, "material": material, "canCollide": collide,
            "role": role, "notes": notes}


def lathe_at(bm, profile, center=(0.0, 0.0, 0.0), sides=8, phase=22.5, scale_y=1.0):
    """Solide de revolution facette (frg.lathe_z_bm) pose en `center`, ecrase en Y si besoin."""
    tmp = frg.lathe_z_bm(profile, sides=sides, phase=phase)
    c = Vector(center)
    made = {v: bm.verts.new(Vector((v.co.x, v.co.y * scale_y, v.co.z)) + c) for v in tmp.verts}
    for f in tmp.faces:
        bm.faces.new([made[v] for v in f.verts])
    tmp.free()
    return bm


def block(bm, x0, x1, y0, y1, z0, z1, bevel=0.0):
    """Pave donne par ses bornes."""
    return frg.block_bm(bm, (x1 - x0, y1 - y0, z1 - z0),
                        ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0), bevel=bevel)


def rock_part(scale, cuts, seed, tilt, az, turn, loc, subdiv=2, jitter=0.1):
    bm = cut_block_bm(scale, cuts, seed=seed, jitter=jitter, subdiv=subdiv)
    place_bm(bm, tilt_deg=tilt, az_deg=az, turn_deg=turn, location=loc)
    return ground_bm(bm)


# ------------------------------------------------------- MIN_Rock_Deco_B
# (echelle, coupes, graine, inclinaison, azimut, rotation, position, subdivisions)
ROCK_B_PARTS = [
    ((1.55, 0.95, 2.9), [((0.0, 0.0, 2.0), (0.55, 0.0, 1.0)),
                         ((0.0, -0.62, 0.0), (0.0, -1.0, 0.10))], 81, 13.0, 0.0, 20.0,
     (-0.75, 0.35, 1.25), 2),
    ((1.25, 0.85, 2.1), [((0.0, 0.0, 1.35), (-0.45, 0.2, 1.0)),
                         ((0.0, 0.55, 0.0), (0.10, 1.0, 0.12))], 83, 25.0, 180.0, -25.0,
     (1.05, -0.35, 0.8), 2),
    ((0.95, 0.65, 1.25), [((0.0, 0.0, 0.8), (0.3, -0.3, 1.0))], 85, 32.0, 100.0, 60.0,
     (-0.35, -1.55, 0.35), 1),
]


def build_min_rock_deco_b():
    """MIN_Rock_Deco_B : Ø ~5, trois dalles taillees appuyees, hauteurs inegales + petite roche."""
    asset = "MIN_Rock_Deco_B"
    coll = lw.reset_collection(asset)
    bm = bmesh.new()
    for scale, cuts, seed, tilt, az, turn, loc, subdiv in ROCK_B_PARTS:
        ore.merge_bm(bm, rock_part(scale, cuts, seed, tilt, az, turn, loc, subdiv))
    ore.merge_bm(bm, ore.rock_bm((0.7, 0.62, 0.65), (1.75, 1.35, 0.2), seed=8, subdiv=1, jitter=0.1))
    center_xy(bm)
    lw.add_object(asset, "Rock", bm, coll, ROCK_COLOR)
    rock_manifest(asset, "Rocher decoratif Ø 5 (trois dalles taillees appuyees + petite roche). "
                         "CollisionFidelity Hull. Origine = base centree.")
    return finish(asset)


# ------------------------------------------------------- MIN_Rock_Deco_C
ROCK_C_PARTS = [
    # gradin bas, large
    ((3.75, 3.2, 1.7), [((0.0, 0.0, 0.85), (0.04, -0.03, 1.0))], 91, 0.0, 0.0, 0.0,
     (0.0, 0.0, 0.2), 2),
    # second gradin
    ((2.5, 2.15, 1.6), [((0.0, 0.0, 0.85), (-0.06, 0.04, 1.0)),
                        ((0.0, -1.55, 0.0), (0.10, -1.0, 0.25))], 93, 0.0, 0.0, 15.0,
     (0.75, 0.55, 1.05), 2),
    # bloc dominant excentre
    ((1.45, 1.25, 2.5), [((0.0, 0.0, 1.55), (0.55, -0.15, 1.0)),
                         ((0.0, -0.78, 0.0), (0.08, -1.0, 0.14)),
                         ((0.95, 0.0, 0.0), (1.0, 0.15, -0.12))], 95, 13.0, 180.0, -20.0,
     (1.55, 1.05, 1.55), 2),
    # marche basse devant
    ((1.5, 1.2, 0.9), [((0.0, 0.0, 0.42), (0.0, -0.08, 1.0))], 97, 0.0, 0.0, 30.0,
     (-2.3, -2.0, 0.15), 1),
]


def build_min_rock_deco_c():
    """MIN_Rock_Deco_C : Ø ~8, affleurement bas en gradins + bloc dominant excentre."""
    asset = "MIN_Rock_Deco_C"
    coll = lw.reset_collection(asset)
    bm = bmesh.new()
    for scale, cuts, seed, tilt, az, turn, loc, subdiv in ROCK_C_PARTS:
        ore.merge_bm(bm, rock_part(scale, cuts, seed, tilt, az, turn, loc, subdiv))
    ore.merge_bm(bm, ore.rock_bm((0.8, 0.7, 0.7), (3.3, -1.9, 0.2), seed=5, subdiv=1, jitter=0.1))
    ore.merge_bm(bm, ore.rock_bm((0.6, 0.6, 0.5), (-2.9, 2.2, 0.15), seed=9, subdiv=1, jitter=0.1))
    center_xy(bm)
    lw.add_object(asset, "Rock", bm, coll, ROCK_COLOR)
    rock_manifest(asset, "Rocher decoratif Ø 8 (affleurement en gradins + bloc dominant). "
                         "CollisionFidelity Hull (ou PreciseConvexDecomposition si l'on veut "
                         "monter sur les gradins). Origine = base centree.")
    return finish(asset)


# ------------------------------------------------------ MIN_Lantern_Post
def build_min_lantern_post():
    """Lanterne de mine 1 x 1 x 6 : Post (fer sombre) + Light (bloc evase Neon)."""
    asset = "MIN_Lantern_Post"
    coll = lw.reset_collection(asset)
    post = bmesh.new()
    frg.loft_chamfer_z_bm(post, [(0.0, 0.5, 0.5), (0.4, 0.5, 0.5), (0.6, 0.3, 0.3),
                                 (0.6, 0.22, 0.22), (4.05, 0.22, 0.22), (4.2, 0.46, 0.46),
                                 (4.4, 0.46, 0.46)], chamfer=0.1)
    # toit de la lanterne
    frg.loft_chamfer_z_bm(post, [(5.4, 0.5, 0.5), (5.55, 0.5, 0.5), (5.85, 0.2, 0.2),
                                 (6.0, 0.12, 0.12)], chamfer=0.1)
    # 4 montants d'angle
    for sx in (-1, 1):
        for sy in (-1, 1):
            block(post, sx * 0.4 - 0.06, sx * 0.4 + 0.06, sy * 0.4 - 0.06, sy * 0.4 + 0.06,
                  4.35, 5.45)
    light = frg.loft_chamfer_z_bm(bmesh.new(), [(4.4, 0.26, 0.26), (5.4, 0.38, 0.38)],
                                  chamfer=0.08)
    lw.add_object(asset, "Post", post, coll, STEEL_DARK)
    lw.add_object(asset, "Light", light, coll, LANTERN)
    return finish_entries(asset, [
        entry("Post", STEEL_DARK, "Metal", True,
              "Socle, fut, cage et toit de la lanterne. Origine = base centree."),
        entry("Light", LANTERN, "Neon", False,
              "Bloc lumineux evase, centre a (0, 4.9, 0) Roblox : y ajouter le PointLight. "
              "Meme origine que Post (base centree)."),
    ])


# --------------------------------------------------------- ENV_Plot_Base
def build_env_plot_base():
    """Sol de parcelle 32 x 32 x 1 : Base (dalle 30 x 30) + Border (bordure de 1 stud chanfreinee)."""
    asset = "ENV_Plot_Base"
    coll = lw.reset_collection(asset)
    base = lw.box_bm((30.0, 30.0, 1.0), (0.0, 0.0, 0.5))
    border = bmesh.new()
    profile = [(15.0, 0.0), (16.0, 0.0), (16.0, 0.7), (15.7, 1.0), (15.0, 1.0)]
    corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    rings = [[border.verts.new((sx * d, sy * d, z)) for d, z in profile] for sx, sy in corners]
    n = len(profile)
    for a in range(4):
        lo, hi = rings[a], rings[(a + 1) % 4]
        for i in range(n):
            j = (i + 1) % n
            border.faces.new((lo[i], lo[j], hi[j], hi[i]))
    lw.add_object(asset, "Base", base, coll, CONCRETE)
    lw.add_object(asset, "Border", border, coll, STEEL_DARK)
    return finish_entries(asset, [
        entry("Base", CONCRETE, "Concrete", True,
              "Dalle 30 x 30 x 1, dessus plan a Y = 1. CollisionFidelity Box. Origine = base centree."),
        entry("Border", STEEL_DARK, "Concrete", True,
              "Bordure de 1 stud (32 exterieur, 30 interieur), dessus a Y = 1 au meme niveau que "
              "Base, chanfrein exterieur 0,3. CollisionFidelity Box ou Hull (le dessus est plan). "
              "Origine = base centree."),
    ])


# ----------------------------------------------------- ENV_Plot_VaultPad
def build_env_plot_vaultpad():
    """Dalle du coffre 14 x 14 x 0,4 : Pad (acier sombre) + Rivets (4 gros rivets laiton aux coins)."""
    asset = "ENV_Plot_VaultPad"
    coll = lw.reset_collection(asset)
    pad = block(bmesh.new(), -7.0, 7.0, -7.0, 7.0, 0.0, 0.4, bevel=0.12)
    rivets = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe_at(rivets, [(0.6, 0.3), (0.6, 0.45), (0.45, 0.55)], (sx * 6.0, sy * 6.0, 0.0))
    lw.add_object(asset, "Pad", pad, coll, STEEL_DARK)
    lw.add_object(asset, "Rivets", rivets, coll, BRASS)
    return finish_entries(asset, [
        entry("Pad", STEEL_DARK, "DiamondPlate", True,
              "Dalle 14 x 14, dessus plan a Y = 0,4 (le coffre se pose dessus). Origine = base centree."),
        entry("Rivets", BRASS, "Metal", False,
              "4 rivets octogonaux Ø 1,2 centres a (±6, ±6), depassent la dalle de 0,15. "
              "Meme origine que Pad."),
    ])


# -------------------------------------------------------- ENV_Plot_Sign
def build_env_plot_sign():
    """Panneau de parcelle 5 x 0,6 x 7 : Frame (2 poteaux + 2 traverses) + Board (face avant plate)."""
    asset = "ENV_Plot_Sign"
    coll = lw.reset_collection(asset)
    frame = bmesh.new()
    for sx in (-1, 1):
        block(frame, sx * 2.2 - 0.3, sx * 2.2 + 0.3, -0.3, 0.3, 0.0, 7.0, bevel=0.1)
    block(frame, -2.0, 2.0, -0.22, 0.22, 3.8, 4.1, bevel=0.06)
    block(frame, -2.0, 2.0, -0.22, 0.22, 6.6, 6.9, bevel=0.06)
    board = lw.box_bm((3.8, 0.3, 2.5), (0.0, -0.05, 5.35))
    lw.add_object(asset, "Frame", frame, coll, WOOD_DARK)
    lw.add_object(asset, "Board", board, coll, WOOD)
    return finish_entries(asset, [
        entry("Frame", WOOD_DARK, "Wood", True,
              "2 poteaux 0,6 x 0,6 x 7 + 2 traverses. Origine = base centree."),
        entry("Board", WOOD, "WoodPlanks", False,
              "Pave 3,8 x 2,5 x 0,3 sans biseau. Face avant plate et verticale (cote -Z Roblox) "
              "a Z = -0,2, centre a Y = 5,35. Meme origine que Frame (base centree)."),
    ])


# ------------------------------------------------------- ENV_Plot_Fence
def build_env_plot_fence():
    """Module de cloture 8 x 0,4 x 2 : 2 poteaux a x = ±2, 2 lisses continues de -4 a +4."""
    asset = "ENV_Plot_Fence"
    coll = lw.reset_collection(asset)
    bm = bmesh.new()
    for sx in (-1, 1):
        tmp = frg.loft_chamfer_z_bm(bmesh.new(), [(0.0, 0.2, 0.2), (1.82, 0.2, 0.2),
                                                  (2.0, 0.08, 0.08)], chamfer=0.06)
        bmesh.ops.translate(tmp, verts=tmp.verts, vec=(sx * 2.0, 0.0, 0.0))
        ore.merge_bm(bm, tmp)
    for z in (0.65, 1.4):
        lw.box_bm((8.0, 0.2, 0.36), (0.0, 0.0, z), bm)
    lw.add_object(asset, "Fence", bm, coll, WOOD)
    return finish_entries(asset, [
        entry("Fence", WOOD, "WoodPlanks", True,
              "Module 8 de long. Poteaux a X = ±2, lisses a section constante coupees net a "
              "X = ±4 : bout a bout, les lisses se prolongent et les poteaux restent espaces de 4. "
              "Symetrique gauche/droite et avant/arriere. CollisionFidelity Box. Origine = base centree."),
    ])


# --------------------------------------------------------- ENV_SpawnPad
def build_env_spawnpad():
    """Plateforme d'apparition Ø 10 x 0,5 : Base (12 cotes) + Ring (anneau Neon)."""
    asset = "ENV_SpawnPad"
    coll = lw.reset_collection(asset)
    k = 1.0 / math.cos(math.pi / 12.0)      # rayon au sommet pour 10 entre plats
    base = lathe_at(bmesh.new(), [(5.0 * k, 0.0), (5.0 * k, 0.24), (4.72 * k, 0.46)],
                    sides=12, phase=15.0)
    ring = bmesh.new()
    ro, ri, z0, z1 = 4.1 * k, 3.3 * k, 0.36, 0.5
    prof = [(ri, z0), (ro, z0), (ro, z1), (ri, z1)]
    rings = [[ring.verts.new((r * math.cos(t), r * math.sin(t), z)) for r, z in prof]
             for t in (math.radians(15.0) + 2.0 * math.pi * i / 12 for i in range(12))]
    for a in range(12):
        lo, hi = rings[a], rings[(a + 1) % 12]
        for i in range(4):
            j = (i + 1) % 4
            ring.faces.new((lo[i], lo[j], hi[j], hi[i]))
    lw.add_object(asset, "Base", base, coll, STEEL)
    lw.add_object(asset, "Ring", ring, coll, SPAWN)
    return finish_entries(asset, [
        entry("Base", STEEL, "Metal", True,
              "Disque 12 cotes, 10 entre plats, dessus plan a Y = 0,46. Origine = base centree."),
        entry("Ring", SPAWN, "Neon", False,
              "Anneau 12 cotes (rayons 3,3 a 4,1), depasse le dessus de Base de 0,04 (dessus a "
              "Y = 0,5). Meme origine que Base."),
    ])


# -------------------------------------------------------- ENV_Zone_Sign
def build_env_zone_sign():
    """Arche de zone 8 x 0,6 x 9 : Frame (2 poteaux + 2 traverses) + Board (bandeau, face plate)."""
    asset = "ENV_Zone_Sign"
    coll = lw.reset_collection(asset)
    frame = bmesh.new()
    for sx in (-1, 1):
        block(frame, sx * 3.6 - 0.4, sx * 3.6 + 0.4, -0.3, 0.3, 0.0, 9.0, bevel=0.12)
    block(frame, -3.35, 3.35, -0.3, 0.3, 8.6, 9.0, bevel=0.08)
    block(frame, -3.35, 3.35, -0.3, 0.3, 6.6, 6.9, bevel=0.08)
    board = lw.box_bm((6.4, 0.4, 1.7), (0.0, 0.0, 7.75))
    lw.add_object(asset, "Frame", frame, coll, WOOD_DARK)
    lw.add_object(asset, "Board", board, coll, WOOD)
    return finish_entries(asset, [
        entry("Frame", WOOD_DARK, "Wood", True,
              "2 poteaux 0,8 x 0,6 x 9 + 2 traverses. Passage libre 6,4 de large x 6,6 de haut. "
              "CollisionFidelity PreciseConvexDecomposition (sinon le passage est bouche). "
              "Origine = base centree."),
        entry("Board", WOOD, "WoodPlanks", False,
              "Pave 6,4 x 1,7 x 0,4 sans biseau. Face avant plate et verticale (-Z Roblox) a "
              "Z = -0,2, centre a Y = 7,75. Meme origine que Frame."),
    ])


# ------------------------------------------------------ ENV_Leaderboard
def build_env_leaderboard():
    """Classement 12 x 1 x 10 : Frame (2 montants + 2 traverses, acier) + Screen (ecran plat sombre)."""
    asset = "ENV_Leaderboard"
    coll = lw.reset_collection(asset)
    frame = bmesh.new()
    for sx in (-1, 1):
        block(frame, sx * 5.5 - 0.5, sx * 5.5 + 0.5, -0.5, 0.5, 0.0, 10.0, bevel=0.14)
    block(frame, -5.2, 5.2, -0.5, 0.5, 9.2, 10.0, bevel=0.12)
    block(frame, -5.2, 5.2, -0.5, 0.5, 2.5, 3.3, bevel=0.12)
    screen = lw.box_bm((10.0, 0.3, 5.9), (0.0, -0.15, 6.25))
    lw.add_object(asset, "Frame", frame, coll, STEEL)
    lw.add_object(asset, "Screen", screen, coll, SCREEN)
    return finish_entries(asset, [
        entry("Frame", STEEL, "Metal", True,
              "2 montants 1 x 1 x 10 + traverses haute et basse. Dessus plan a Y = 10 (pose des "
              "ornements ENV_LB_Topper_*). Origine = base centree. CollisionFidelity "
              "PreciseConvexDecomposition (sinon le vide sous l'écran est bouché)."),
        entry("Screen", SCREEN, "SmoothPlastic", False,
              "Ecran 10 x 5,9 x 0,3 sans biseau. Face avant plate et verticale (-Z Roblox) a "
              "Z = -0,3 (en retrait de 0,2 du cadre), centre a Y = 6,25. Meme origine que Frame."),
    ])


# -------------------------------------------------- ENV_LB_Topper_Crown
def build_env_lb_topper_crown():
    """Couronne 3 x 1 x 2 (ovale, pour tenir sur le cadre de 1 de profondeur) : 8 pointes."""
    asset = "ENV_LB_Topper_Crown"
    coll = lw.reset_collection(asset)
    bm = bmesh.new()
    n, sy = 16, 1.0 / 3.0

    def ring(r, z_even, z_odd=None):
        z_odd = z_even if z_odd is None else z_odd
        return [bm.verts.new((r * math.cos(t), r * sy * math.sin(t), z_even if i % 2 == 0 else z_odd))
                for i, t in enumerate(2.0 * math.pi * i / n for i in range(n))]

    # bandeau epais, paroi, pointes (sommets pairs hauts), interieur creux
    rings = [ring(1.5, 0.0), ring(1.5, 0.4), ring(1.38, 0.5), ring(1.38, 2.0, 1.05),
             ring(1.0, 1.85, 0.95), ring(1.0, 0.75)]
    for lo, hi in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) == 4])
    lw.add_object(asset, "Crown", bm, coll, GOLD)
    return finish_entries(asset, [
        entry("Crown", GOLD, "Metal", False,
              "Couronne ovale 3 x 2 x 1 (L x H x P), 8 pointes. A poser au sommet du classement "
              "des plus riches (Y = 10 du cadre). Origine = base centree."),
    ])


# --------------------------------------------------- ENV_LB_Topper_Mask
MASK_HALF = [(0.0, 0.45), (0.3, 0.12), (0.75, 0.0), (1.15, 0.12), (1.4, 0.55), (1.5, 1.5),
             (1.0, 1.28), (0.45, 1.3), (0.0, 1.15)]
MASK_EYE = [(0.28, 0.70), (0.5, 0.95), (0.88, 1.02), (1.1, 0.88), (0.95, 0.6), (0.55, 0.5)]


# Triangulation explicite de la demi-face droite (x >= 0) : couronne entre le contour (o, indice
# dans MASK_HALF) et l'oeil (e, indice dans MASK_EYE). Sens trigonometrique vu de face. L'ancienne
# version laissait Blender trianguler un n-gone concave puis percait les yeux par booleen : des
# triangles sortaient du contour (nez, arcade) et certains etaient retournes.
MASK_TRIS = [(("o", 1), ("o", 2), ("e", 5)), (("o", 2), ("e", 4), ("e", 5)),
             (("o", 2), ("o", 3), ("e", 4)), (("o", 3), ("o", 4), ("e", 4)),
             (("o", 4), ("e", 3), ("e", 4)), (("o", 4), ("o", 5), ("e", 3)),
             (("o", 5), ("e", 2), ("e", 3)), (("o", 5), ("o", 6), ("e", 2)),
             (("o", 6), ("e", 1), ("e", 2)), (("o", 6), ("o", 7), ("e", 1)),
             (("o", 7), ("e", 0), ("e", 1)), (("o", 7), ("o", 8), ("e", 0)),
             (("o", 8), ("o", 0), ("e", 0)), (("o", 0), ("o", 1), ("e", 0)),
             (("o", 1), ("e", 5), ("e", 0))]


def _area2(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))


def build_env_lb_topper_mask():
    """Loup de voleur 3 x 0,5 x 1,5 : plaque decoupee, bords chanfreines, 2 yeux traversants.
    Les deux grandes faces sont triangulees a la main (MASK_TRIS), sans booleen."""
    asset = "ENV_LB_Topper_Mask"
    coll = lw.reset_collection(asset)
    outline = MASK_HALF + [(-x, z) for x, z in reversed(MASK_HALF[1:-1])]
    k = len(outline)
    n_half = len(MASK_HALF)
    cz = 0.75
    eye_r = MASK_EYE
    eye_l = [(-x, z) for x, z in MASK_EYE]          # meme indice = sommet miroir

    def ring_xz(s):
        # homothetie de centre (0, cz), point interieur vu du bon cote de toutes les aretes :
        # chaque arete rentre, les pans du chanfrein sont plans et jamais en surplomb (l'ancienne
        # version ne reduisait pas z au pied : pans gauches et retournes pres des pointes basses)
        return [(x * s, cz + (z - cz) * s) for x, z in outline]

    # controle 2D de la triangulation sur le contour de la face (chanfreine a 90 %)
    face_xz = ring_xz(0.9)
    total = 0.0
    for tri in MASK_TRIS:
        pts = [face_xz[i] if kind == "o" else eye_r[i] for kind, i in tri]
        a2 = _area2(pts)
        assert a2 > 1e-6, "triangle retourne ou degenere : %r" % (tri,)
        total += a2
    half = [face_xz[i] for i in range(n_half)]
    assert abs(total - (_area2(half) - _area2(list(reversed(eye_r))))) < 1e-9,         "la triangulation ne couvre pas exactement la demi-face"

    bm = bmesh.new()
    ys = (-0.25, -0.12, 0.12, 0.25)                 # avant -> arriere
    rings = [[bm.verts.new((x, y, z)) for x, z in ring_xz(s)]
             for y, s in zip(ys, (0.9, 1.0, 1.0, 0.9))]
    for lo, hi in zip(rings, rings[1:]):            # tranche chanfreinee
        for i in range(k):
            j = (i + 1) % k
            bm.faces.new((lo[i], hi[i], hi[j], lo[j]))
    eyes = {}                                       # (cote, y) -> sommets du trou
    for side, eye in (("r", eye_r), ("l", eye_l)):
        for y in (ys[0], ys[-1]):
            eyes[side, y] = [bm.verts.new((x, y, z)) for x, z in eye]
        f, r = eyes[side, ys[0]], eyes[side, ys[-1]]
        for i in range(len(eye)):                   # tunnel de l'oeil
            j = (i + 1) % len(eye)
            bm.faces.new((f[i], f[j], r[j], r[i]))
    for y, ring, front in ((ys[0], rings[0], True), (ys[-1], rings[-1], False)):
        for tri in MASK_TRIS:
            right = [ring[i] if kind == "o" else eyes["r", y][i] for kind, i in tri]
            left = [ring[(k - i) % k] if kind == "o" else eyes["l", y][i] for kind, i in tri]
            left.reverse()                          # le miroir inverse le sens
            for vs in (right, left):
                bm.faces.new(vs if front else list(reversed(vs)))
    lw.add_object(asset, "Mask", bm, coll, MASK)
    return finish_entries(asset, [
        entry("Mask", MASK, "SmoothPlastic", False,
              "Loup de voleur 3 x 1,5 x 0,5 (L x H x P), debout face a -Z Roblox, yeux traversants. "
              "A poser au sommet du classement des meilleurs voleurs. Origine = base centree."),
    ])


LOT6_BUILDERS = ("build_min_rock_deco_a", "build_min_rock_deco_b", "build_min_rock_deco_c",
                 "build_min_lantern_post", "build_env_plot_base", "build_env_plot_vaultpad",
                 "build_env_plot_sign", "build_env_plot_fence", "build_env_spawnpad",
                 "build_env_zone_sign", "build_env_leaderboard", "build_env_lb_topper_crown",
                 "build_env_lb_topper_mask")
