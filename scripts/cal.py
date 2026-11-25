"""Locksmith Wars - categorie CAL (calibrage echelle + orientation)."""
import bmesh

import lw_common as lw

CATEGORY = "CAL"


def build_CAL_Cube_1x1x1():
    """Cube de 1 x 1 x 1 stud, origine a la base centree."""
    asset = "CAL_Cube_1x1x1"
    coll = lw.reset_collection(asset)
    bm = lw.box_bm((1.0, 1.0, 1.0), (0.0, 0.0, 0.5))
    lw.add_object(asset, asset, bm, coll, "#D0D0D0")
    lw.update_manifest(asset, [{
        "object": asset, "color": "#D0D0D0", "material": "SmoothPlastic",
        "canCollide": True, "role": "fixed",
        "notes": "Calibrage : doit mesurer 1 x 1 x 1 stud dans Studio.",
    }])
    return lw.export_asset(asset, CATEGORY)


def build_CAL_Arrow():
    """Fleche de 3 studs couchee au sol, pointe vers l'avant (-Y Blender).

    Un ergot depasse du cote +X a la queue : il permet de voir si l'import
    retourne le modele en miroir. Emprise : 1,4 x 3 x 0,4.
    """
    asset = "CAL_Arrow"
    coll = lw.reset_collection(asset)
    outline = [
        (0.0, -1.5),                 # pointe (avant)
        (0.7, -0.4), (0.25, -0.4),   # epaule droite de la tete
        (0.25, 1.1), (0.6, 1.1), (0.6, 1.5),  # ergot cote +X
        (-0.25, 1.5), (-0.25, -0.4), (-0.7, -0.4),
    ]
    bm = bmesh.new()
    face = bm.faces.new([bm.verts.new((x, y, 0.0)) for x, y in outline])
    top = bmesh.ops.extrude_face_region(bm, geom=[face])
    bmesh.ops.translate(
        bm, vec=(0.0, 0.0, 0.4),
        verts=[g for g in top["geom"] if isinstance(g, bmesh.types.BMVert)])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    lw.add_object(asset, asset, bm, coll, "#FF2A2A")
    lw.update_manifest(asset, [{
        "object": asset, "color": "#FF2A2A", "material": "SmoothPlastic",
        "canCollide": False, "role": "fixed",
        "notes": "Calibrage : pointe = avant (-Y Blender), ergot = cote +X, epaisseur = haut.",
    }])
    return lw.export_asset(asset, CATEGORY)


def build_all():
    return [build_CAL_Cube_1x1x1(), build_CAL_Arrow()]
