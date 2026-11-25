"""Locksmith Wars - categorie ING (lingot)."""
import bmesh
from mathutils import Vector

import lw_common as lw

CATEGORY = "ING"


def build_ING_Bar():
    """Lingot trapezoidal 2 (X) x 1 (Y) x 0,6 (Z), dessus a 80 %, biseau 0,05."""
    asset = "ING_Bar"
    coll = lw.reset_collection(asset)
    bm = lw.box_bm((2.0, 1.0, 0.6), (0.0, 0.0, 0.3))
    for v in bm.verts:
        if v.co.z > 0.3:
            v.co = Vector((v.co.x * 0.8, v.co.y * 0.8, v.co.z))
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.05, offset_type="OFFSET", segments=1,
                    profile=0.5, affect="EDGES")
    # le biseau rogne les aretes du bas : on retablit l'encombrement exact 2 x 1 x 0,6
    mx = max(abs(v.co.x) for v in bm.verts)
    my = max(abs(v.co.y) for v in bm.verts)
    for v in bm.verts:
        v.co = Vector((v.co.x / mx, v.co.y * 0.5 / my, v.co.z))
    lw.add_object(asset, "Bar", bm, coll, lw.TINT)
    lw.update_manifest(asset, [
        {"object": "Bar", "color": lw.TINT, "material": "Metal", "canCollide": False,
         "role": "tint",
         "notes": "Lingot recolore selon le metal ; etat chauffe = interpolation de couleur "
                  "vers #FF7A1A. Longueur selon X. Origine = base centree."}])
    path = lw.export_asset(asset, CATEGORY)
    lw.report(asset)
    lw.save_blend()
    return path
