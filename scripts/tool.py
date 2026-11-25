"""Locksmith Wars - categorie TOOL (outils tenus)."""
import math

import bmesh
from mathutils import Vector

import lw_common as lw

CATEGORY = "TOOL"
WOOD = "#8A5A33"
STEEL = "#9AA0A8"


# ------------------------------------------------------------ primitives
def lathe_y_bm(profile, sides=8, phase=22.5, bm=None):
    """Solide de revolution facette autour de l'axe Y. profile = [(rayon, y), ...]."""
    if bm is None:
        bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(t), y, r * math.sin(t)))
              for t in (math.radians(phase) + 2.0 * math.pi * i / sides for i in range(sides))]
             for r, y in profile]
    for lo, hi in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    return bm


def spike_bm(bm, sections, tip):
    """Pointe a section rectangulaire : sections = [(z, y, demi-x, demi-y), ...] puis apex."""
    rings = [[bm.verts.new((sx * dx, y + sy * dy, z))
              for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
             for z, y, dx, dy in sections]
    for lo, hi in zip(rings, rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    apex = bm.verts.new(tip)
    for i in range(4):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % 4], apex))
    bm.faces.new(list(reversed(rings[0])))
    return bm


def finish(asset, entries):
    lw.update_manifest(asset, entries)
    path = lw.export_asset(asset, CATEGORY)
    lw.report(asset)
    lw.save_blend()
    return path


# ---------------------------------------------------------- TOOL_Pickaxe
PICK_HANDLE = [(0.13, -1.80), (0.18, -1.74), (0.20, 0.42), (0.26, 0.48), (0.26, 0.62),
               (0.20, 0.68), (0.20, 1.44), (0.27, 1.52), (0.27, 1.72), (0.20, 1.80)]
PICK_EYE_Y = -1.36                 # centre de la douille sur le manche
PICK_EYE = (0.62, 0.78, 0.84)      # douille : x, y, z
PICK_SPAN = 1.5                    # demi-envergure (pointes a z = +/-1,5)
PICK_SWEEP = 0.46                  # recul des pointes vers +Y (cote manche), ~20 degres
# (z, demi-epaisseur x, demi-profondeur y) des sections d'une pointe
PICK_SECTIONS = [(0.20, 0.22, 0.27), (0.62, 0.22, 0.25), (0.98, 0.18, 0.18), (1.26, 0.12, 0.11)]


def _pick_y(z):
    return PICK_EYE_Y + PICK_SWEEP * (abs(z) / PICK_SPAN) ** 2


def build_TOOL_Pickaxe():
    """Pioche : Handle (manche le long de Y, origine au centre) + Head (fer a 2 pointes en -Y)."""
    asset = "TOOL_Pickaxe"
    coll = lw.reset_collection(asset)

    handle = lathe_y_bm(PICK_HANDLE)

    head = lw.box_bm(PICK_EYE, (0.0, PICK_EYE_Y, 0.0))
    bmesh.ops.bevel(head, geom=head.edges[:], offset=0.11, offset_type="OFFSET", segments=1,
                    profile=0.5, affect="EDGES")
    for sign in (1.0, -1.0):
        sections = [(sign * z, _pick_y(z), dx, dy) for z, dx, dy in PICK_SECTIONS]
        spike_bm(head, sections, (0.0, _pick_y(PICK_SPAN) + 0.04, sign * PICK_SPAN))
    bmesh.ops.recalc_face_normals(head, faces=head.faces)

    lw.add_object(asset, "Handle", handle, coll, WOOD)
    lw.add_object(asset, "Head", head, coll, STEEL)
    return finish(asset, [
        {"object": "Handle", "color": WOOD, "material": "Wood", "canCollide": False,
         "role": "fixed",
         "notes": "Manche, longueur 3,6 le long de Z Roblox (Y Blender), origine au centre du "
                  "manche. Tete a l'avant (-Z Roblox). Prise prevue a 1,2 stud en arriere du "
                  "centre (Tool.Grip = CFrame.new(0, 0, 1.2))."},
        {"object": "Head", "color": STEEL, "material": "Metal", "canCollide": False,
         "role": "fixed",
         "notes": "Fer a deux pointes (haut/bas, envergure 3), a souder sur Handle. Meme "
                  "origine que Handle (centre du manche)."},
    ])


# ----------------------------------------------------------- TOOL_Hammer
def loft_z_bm(bm, sections, y):
    """Bloc a sections rectangulaires empilees le long de Z : [(z, demi-x, demi-y), ...]."""
    rings = [[bm.verts.new((sx * dx, y + sy * dy, z))
              for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
             for z, dx, dy in sections]
    for lo, hi in zip(rings, rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    return bm


# meme langage que la pioche : bague de butee puis zone de prise lisse (y ~ +0,8) puis pommeau
HAMMER_HANDLE = [(0.12, -1.10), (0.165, -1.05), (0.18, 0.14), (0.24, 0.19), (0.24, 0.31),
                 (0.18, 0.36), (0.18, 0.92), (0.25, 0.97), (0.25, 1.05), (0.19, 1.10)]
# le bout chanfreine du manche depasse de 0,10 devant la tete (y = -1,10 contre -1,00) :
# ecart franc, plus de faces quasi coplanaires (scintillement corrige)
HAMMER_EYE_Y = -0.61
# (z, demi-x, demi-y) : face de frappe biseautee, table elargie, gorge, corps ; symetrique
HAMMER_HALF = [(0.70, 0.29, 0.29), (0.60, 0.39, 0.39), (0.40, 0.39, 0.39), (0.30, 0.31, 0.31)]


def build_TOOL_Hammer():
    """Marteau de forgeron : Handle (manche le long de Y) + Head (bloc trapu a 2 faces de frappe)."""
    asset = "TOOL_Hammer"
    coll = lw.reset_collection(asset)
    handle = lathe_y_bm(HAMMER_HANDLE)
    sections = [(-z, dx, dy) for z, dx, dy in HAMMER_HALF] + list(reversed(HAMMER_HALF))
    head = loft_z_bm(bmesh.new(), sections, HAMMER_EYE_Y)
    bmesh.ops.recalc_face_normals(head, faces=head.faces)
    lw.add_object(asset, "Handle", handle, coll, WOOD)
    lw.add_object(asset, "Head", head, coll, STEEL)
    return finish(asset, [
        {"object": "Handle", "color": WOOD, "material": "Wood", "canCollide": False,
         "role": "fixed",
         "notes": "Manche, longueur 2,2 le long de Z Roblox (Y Blender), origine au centre du "
                  "manche. Tete a l'avant (-Z Roblox). Prise prevue a 0,8 stud en arriere du "
                  "centre (C1 = CFrame.new(0, 0, 0.8))."},
        {"object": "Head", "color": STEEL, "material": "Metal", "canCollide": False,
         "role": "fixed",
         "notes": "Tete de forgeron a deux faces de frappe (haut/bas), a souder sur Handle. "
                  "Meme origine que Handle (centre du manche)."},
    ])
