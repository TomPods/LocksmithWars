"""Locksmith Wars - helpers communs Blender -> Roblox.

Conventions :
- 1 unite Blender = 1 stud, Z haut, face avant des assets vers -Y.
- Une Collection par asset. Les noms d'objets Blender sont globalement uniques,
  donc dans le .blend les pieces s'appellent "<ASSET>.<Piece>" ; le vrai nom de
  la piece ("Body", "Tint", "Rock"...) est stocke dans la propriete "lw_part"
  et applique le temps de l'export FBX.
"""
import json
import os

import bmesh
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\blanc\Locksmith_Wars"
EXPORTS = os.path.join(PROJECT, "exports")
RENDERS = os.path.join(PROJECT, "renders")
BLEND = os.path.join(PROJECT, "locksmith_assets.blend")
MANIFEST = os.path.join(EXPORTS, "manifest.json")

TINT = "#D0D0D0"          # pieces recolorees par le jeu
MARKER_COLOR = "#FF00FF"  # reperes (invisibles dans Studio)
MARKER_SIZE = 0.2

ROBLOX_MATERIALS = {
    "SmoothPlastic", "Metal", "DiamondPlate", "Wood", "WoodPlanks", "Slate",
    "Cobblestone", "Brick", "Concrete", "Glass", "Neon", "ForceField", "Foil",
}


# --------------------------------------------------------------- couleurs
def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(hex_color):
    h = hex_color.lstrip("#")
    return tuple(_srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (1.0,)


def material(hex_color):
    """Materiau uni (apercu Blender uniquement ; Roblox lit le manifest)."""
    name = "LW_" + hex_color.lstrip("#").upper()
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    rgba = hex_rgba(hex_color)
    mat.diffuse_color = rgba
    tree = mat.node_tree
    if tree is not None:
        bsdf = next((n for n in tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is not None:
            for sock in bsdf.inputs:
                if sock.identifier == "Base Color":
                    sock.default_value = rgba
                elif sock.identifier == "Roughness":
                    sock.default_value = 0.6
    return mat


# ------------------------------------------------------------ collections
def _purge(coll):
    for child in list(coll.children):
        _purge(child)
        bpy.data.collections.remove(child)
    for ob in list(coll.objects):
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if data is not None and data.users == 0 and isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)


def reset_collection(name, parent=None):
    """Vide puis (re)cree la Collection : rend chaque build_* idempotent."""
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    else:
        _purge(coll)
    host = parent if parent is not None else bpy.context.scene.collection
    if coll.name not in host.children:
        host.children.link(coll)
    return coll


# ----------------------------------------------------------------- objets
def add_object(asset, part, bm, coll, color, origin=(0.0, 0.0, 0.0), parent=None, flip=False):
    """Cree l'objet <asset>.<part> depuis un bmesh exprime en coordonnees monde.

    L'origine (pivot) est placee en `origin` ; rotation et echelle restent a
    l'identite, donc il n'y a rien a "appliquer" avant export.
    parent : groupe cree par add_group (a l'identite), l'objet en devient l'enfant.
    flip : inverse les normales apres recalcul (parois interieures d'une cavite).
    """
    origin = Vector(origin)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if flip:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bmesh.ops.translate(bm, verts=bm.verts, vec=-origin)
    full = part if part == asset else asset + "." + part
    mesh = bpy.data.meshes.new(full)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material(color))
    ob = bpy.data.objects.new(full, mesh)
    ob.location = origin
    ob["lw_part"] = part
    ob["lw_asset"] = asset
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent          # parent a l'identite : location locale = monde
    return ob


def add_group(asset, part, coll):
    """Groupe <asset>.<part> : Empty a l'identite, exporte comme noeud parent (Model Roblox).

    Les pieces creees avec add_object(..., parent=groupe) en sont les enfants dans le FBX.
    """
    full = asset + "." + part
    ob = bpy.data.objects.new(full, None)
    ob.empty_display_size = 0.5
    ob["lw_part"] = part
    ob["lw_asset"] = asset
    ob["lw_group"] = True
    coll.objects.link(ob)
    return ob


def meshes(objs):
    return [ob for ob in objs if ob.type == "MESH"]


def box_bm(size, center=(0.0, 0.0, 0.0), bm=None):
    """Ajoute un pave (size = x, y, z) centre en `center`."""
    if bm is None:
        bm = bmesh.new()
    res = bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    for v in res["verts"]:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz)) + Vector(center)
    return bm


def add_marker(asset, part, coll, position):
    """Repere : cube de 0,2 stud centre exactement sur `position`."""
    bm = box_bm((MARKER_SIZE,) * 3, position)
    ob = add_object(asset, part, bm, coll, MARKER_COLOR, origin=position)
    ob["lw_marker"] = True
    return ob


# ------------------------------------------------------------- controles
def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def world_bounds(ob):
    pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def report(asset):
    """Imprime triangles, dimensions, bornes et pivot de chaque piece."""
    bpy.context.view_layer.update()
    coll = bpy.data.collections[asset]
    total = 0
    for ob in sorted(meshes(coll.all_objects), key=lambda o: o.name):
        lo, hi = world_bounds(ob)
        d = hi - lo
        t = tri_count(ob)
        total += t
        print("%-28s tris=%-5d dim=(%.2f, %.2f, %.2f) min=(%.2f, %.2f, %.2f) "
              "max=(%.2f, %.2f, %.2f) pivot=(%.2f, %.2f, %.2f)"
              % (ob.get("lw_part", ob.name), t, d.x, d.y, d.z, lo.x, lo.y, lo.z,
                 hi.x, hi.y, hi.z, *ob.matrix_world.translation))
    print("%s : %d triangles au total" % (asset, total))
    return total


# ----------------------------------------------------------------- export
def export_asset(asset, category):
    """Exporte la Collection `asset` vers exports/<category>/<asset>.fbx."""
    coll = bpy.data.collections[asset]
    objs = list(coll.all_objects)
    path = os.path.join(EXPORTS, category, asset + ".fbx")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Noms de pieces exacts le temps de l'export (voir docstring du module).
    own = {ob: ob.name for ob in objs}
    displaced = {}
    for ob in objs:
        target = ob.get("lw_part", ob.name)
        other = bpy.data.objects.get(target)
        if other is not None and other is not ob:
            displaced[other] = other.name
            other.name = "__lw_swap__" + other.name
        ob.name = target

    coll.hide_viewport = False   # une Collection masquee n'est pas selectionnable
    view_layer = bpy.context.view_layer
    view_layer.update()
    for ob in list(view_layer.objects):
        if ob is not None:
            ob.select_set(False)
    for ob in objs:
        ob.select_set(True)
    view_layer.objects.active = objs[0]
    try:
        bpy.ops.export_scene.fbx(
            filepath=path,
            use_selection=True,
            apply_scale_options="FBX_SCALE_ALL",
            axis_forward="-Z",
            axis_up="Y",
            object_types=({"MESH", "EMPTY"} if any(ob.type == "EMPTY" for ob in objs)
                          else {"MESH"}),
            use_mesh_modifiers=True,
            bake_anim=False,
            add_leaf_bones=False,
            path_mode="STRIP",
        )
    finally:
        for ob, name in own.items():
            ob.name = name
        for ob, name in displaced.items():
            ob.name = name
        for ob in objs:
            ob.select_set(False)
    return path


# --------------------------------------------------------------- manifest
def update_manifest(asset, entries):
    """Remplace les entrees de `asset` dans exports/manifest.json.

    entries : liste de dicts {object, color, material, canCollide, role, notes}.
    """
    os.makedirs(EXPORTS, exist_ok=True)
    data = []
    if os.path.exists(MANIFEST):
        with open(MANIFEST, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    data = [e for e in data if e.get("asset") != asset]
    for e in entries:
        if e["material"] not in ROBLOX_MATERIALS:
            raise ValueError("Materiau Roblox inconnu : %s" % e["material"])
        if e["role"] not in ("fixed", "tint", "moving", "marker"):
            raise ValueError("Role inconnu : %s" % e["role"])
        data.append({
            "asset": asset,
            "object": e["object"],
            "color": e["color"],
            "material": e["material"],
            "canCollide": bool(e["canCollide"]),
            "role": e["role"],
            "notes": e.get("notes", ""),
        })
    data.sort(key=lambda e: (e["asset"], e["object"]))
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return len(data)


def save_blend():
    if bpy.data.filepath and os.path.normcase(bpy.data.filepath) == os.path.normcase(BLEND):
        bpy.ops.wm.save_mainfile()
    else:
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    return bpy.data.filepath
