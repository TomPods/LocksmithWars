"""Locksmith Wars - previsualisation (jamais exportee).

Cree dans la Collection _PREVIEW des copies colorees des assets, alignees cote
a cote avec un mannequin de 5 studs, et masque les Collections d'assets (qui
restent toutes a l'origine pour l'export).
"""
import math
import os

import bpy
from mathutils import Matrix

import lw_common as lw

PREVIEW = "_PREVIEW"

# nom -> (couleur, materiau Roblox)
METALS = {
    "Iron": ("#8A8F98", "Metal"), "Copper": ("#C46A3A", "Metal"),
    "Silver": ("#D9DDE3", "Metal"), "Gold": ("#F2C12E", "Metal"),
    "Cobalt": ("#2E5BD6", "Glass"), "Titanium": ("#7FD1C9", "Glass"),
    "Obsidium": ("#6B2FB3", "Neon"), "Aetherite": ("#FF4FD8", "Neon"),
}


def _set(bsdf, identifier, value):
    for sock in bsdf.inputs:
        if sock.identifier == identifier:
            sock.default_value = value
            return


def pv_material(hex_color, kind):
    """Approximation Blender d'un materiau Roblox (Metal, Glass, Neon...)."""
    name = "PV_%s_%s" % (kind, hex_color.lstrip("#").upper())
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    rgba = lw.hex_rgba(hex_color)
    mat.diffuse_color = rgba
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return mat
    _set(bsdf, "Base Color", rgba)
    _set(bsdf, "Roughness", 0.6)
    if kind == "Metal":
        _set(bsdf, "Metallic", 0.85)
        _set(bsdf, "Roughness", 0.38)
    elif kind == "Glass":
        _set(bsdf, "Metallic", 0.25)
        _set(bsdf, "Roughness", 0.12)
        _set(bsdf, "Emission Color", rgba)
        _set(bsdf, "Emission Strength", 0.35)
    elif kind == "Neon":
        _set(bsdf, "Emission Color", rgba)
        _set(bsdf, "Emission Strength", 1.6)
    return mat


def clear():
    return lw.reset_collection(PREVIEW)


def hide_assets(hidden=True):
    """Masque (ou reaffiche) toutes les Collections d'assets."""
    for coll in bpy.context.scene.collection.children:
        if coll.name != PREVIEW:
            coll.hide_viewport = hidden
            coll.hide_render = hidden


def place(asset, parts, offset, tint=None, tag=""):
    """Copie les pieces `parts` de `asset` en `offset`.

    tint : nom de metal applique aux pieces recolorables (lw_part Crystals*,
    Tint, Core, Shards...) ; les autres gardent leur couleur.
    """
    coll = bpy.data.collections[PREVIEW]
    src = bpy.data.collections[asset]
    made = []
    for ob in src.all_objects:
        part = ob.get("lw_part", ob.name)
        if part not in parts or ob.get("lw_marker"):
            continue
        cp = ob.copy()
        cp.data = ob.data.copy()
        cp.name = "PV_%s_%s%s" % (asset, part, tag)
        cp.location = ob.location + lw.Vector(offset)
        base = cp.data.materials[0]
        if tint is not None and base is not None and base.name == "LW_" + lw.TINT.lstrip("#"):
            color, kind = METALS[tint]
            cp.data.materials[0] = pv_material(color, kind)
        coll.objects.link(cp)
        made.append(cp)
    return made


def mannequin(offset=(0.0, 0.0, 0.0), color="#B9BEC6"):
    """Avatar generique en blocs, 5 studs de haut, face vers -Y."""
    coll = bpy.data.collections[PREVIEW]
    bm = None
    for size, center in (
        ((0.9, 0.9, 2.0), (-0.5, 0.0, 1.0)), ((0.9, 0.9, 2.0), (0.5, 0.0, 1.0)),   # jambes
        ((2.0, 1.0, 2.0), (0.0, 0.0, 3.0)),                                         # torse
        ((0.9, 0.9, 2.0), (-1.5, 0.0, 3.0)), ((0.9, 0.9, 2.0), (1.5, 0.0, 3.0)),   # bras
        ((1.1, 1.1, 1.0), (0.0, 0.0, 4.5)),                                         # tete
    ):
        bm = lw.box_bm(size, center, bm)
    ob = lw.add_object(PREVIEW, "Mannequin", bm, coll, color, origin=(0.0, 0.0, 0.0))
    ob.name = "PV_Mannequin"
    ob.location = lw.Vector(offset)
    return ob


# ------------------------------------------------------------- planches
def label(text, position, size=1.1, color="#1E2227"):
    """Etiquette debout (face a -Y), jamais exportee."""
    coll = bpy.data.collections[PREVIEW]
    cu = bpy.data.curves.new("PV_Label", type="FONT")
    cu.body = text
    cu.size = size
    cu.extrude = 0.02
    ob = bpy.data.objects.new("PV_Label", cu)
    ob.location = position
    ob.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    cu.materials.append(lw.material(color))
    coll.objects.link(ob)
    return ob


def stage(center, width, height, elevation=35.0, ground="#9A9DA2", res_x=2000):
    """Sol neutre, soleil, camera orthographique plongeante cadree sur la planche."""
    coll = bpy.data.collections[PREVIEW]
    scene = bpy.context.scene
    bm = lw.box_bm((400.0, 400.0, 0.2), (center[0], center[1], -0.1))
    g = lw.add_object(PREVIEW, "Ground", bm, coll, ground)
    g.name = "PV_Ground"
    sun_data = bpy.data.lights.new("PV_Sun", "SUN")
    sun_data.energy = 3.2
    sun_data.angle = math.radians(6.0)
    sun = bpy.data.objects.new("PV_Sun", sun_data)
    sun.rotation_euler = (math.radians(48.0), 0.0, math.radians(-32.0))
    coll.objects.link(sun)
    cam_data = bpy.data.cameras.new("PV_Camera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(width, height)
    cam_data.clip_end = 500.0
    cam = bpy.data.objects.new("PV_Camera", cam_data)
    el = math.radians(elevation)
    cam.rotation_euler = (math.radians(90.0) - el, 0.0, 0.0)
    c = lw.Vector(center)
    cam.location = c + lw.Vector((0.0, -math.cos(el), math.sin(el))) * 150.0
    coll.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x = res_x
    scene.render.resolution_y = int(res_x * height / width)
    scene.render.resolution_percentage = 100
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    bg = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)         if world.node_tree else None
    if bg is not None:
        bg.inputs[0].default_value = (0.75, 0.77, 0.80, 1.0)
        bg.inputs[1].default_value = 0.9
    return cam


def render_to(filename):
    scene = bpy.context.scene
    path = os.path.join(lw.RENDERS, filename)
    os.makedirs(lw.RENDERS, exist_ok=True)
    vs = scene.view_settings
    old = (vs.view_transform, vs.look, scene.render.filepath)
    try:
        vs.view_transform = "Standard"
    except TypeError:
        pass
    hide_assets(True)
    bpy.data.collections[PREVIEW].hide_render = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = path
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        vs.view_transform, vs.look, scene.render.filepath = old
    return path


def cleanup():
    """Supprime toutes les copies de previsualisation et reaffiche les assets."""
    scene = bpy.context.scene
    coll = bpy.data.collections.get(PREVIEW)
    if coll is not None:
        for ob in list(coll.objects):
            data = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if data is not None and data.users == 0:
                kind = {"MESH": bpy.data.meshes, "FONT": bpy.data.curves, "LIGHT": bpy.data.lights,
                        "CAMERA": bpy.data.cameras}.get(data.id_type if hasattr(data, "id_type") else "")
                if kind is not None:
                    kind.remove(data)
    for mat in list(bpy.data.materials):
        if mat.name.startswith("PV_") and mat.users == 0:
            bpy.data.materials.remove(mat)
    cam = bpy.data.objects.get("Camera")
    if scene.camera is None and cam is not None:
        scene.camera = cam
    hide_assets(False)


LOT1_ROWS = [("ORE_F1", "Iron", "Copper", "F1  Fer / Cuivre"),
             ("ORE_F2", "Silver", "Gold", "F2  Argent / Or"),
             ("ORE_F3", "Cobalt", "Titanium", "F3  Cobalt / Titane"),
             ("ORE_F4", "Obsidium", "Aetherite", "F4  Obsidium / Aetherite")]


def board_lot1(filename="lot1_ORE_ING.png", keep=False):
    """Planche du lot 1 : 4 familles x 2 metaux x (intact, fissure) + debris, eclats, lingots."""
    clear()
    cols = (-9.75, -3.25, 3.25, 9.75)
    pitch = 12.0
    for r, (asset, m1, m2, text) in enumerate(LOT1_ROWS):
        y = r * pitch
        extra = ("Core", "Shards") if asset == "ORE_F4" else ()
        for k, (metal, parts) in enumerate((
                (m1, ("Rock", "Crystals")), (m1, ("Rock", "Crystals_Broken")),
                (m2, ("Rock", "Crystals")), (m2, ("Rock", "Crystals_Broken")))):
            place(asset, parts + extra, (cols[k], y, 0.0), tint=metal, tag="_%d%d" % (r, k))
        mannequin((-15.5, y, 0.0)).name = "PV_Mannequin_%d" % r
        label(text, (-30.0, y, 1.6))
        label("intact / fissure", (-30.0, y, 0.3), size=0.8)
    y = -10.0
    label("Debris, eclats, lingots", (-30.0, y, 1.0))
    mannequin((-15.5, y, 0.0)).name = "PV_Mannequin_x"
    place("ORE_Rubble", ("Rubble",), (-9.75, y, 0.0), tag="_x")
    for i, metal in enumerate(("Iron", "Gold", "Cobalt", "Aetherite")):
        place("ORE_Chunk", ("Chunk",), (-5.2 + 1.5 * i, y, 0.42), tint=metal, tag="_x%d" % i)
    for i, metal in enumerate(("Copper", "Gold", "Titanium")):
        place("ING_Bar", ("Bar",), (3.25 + 3.2 * i, y, 0.0), tint=metal, tag="_x%d" % i)
    stage(center=(-8.5, 13.0, 2.5), width=48.0, height=36.0)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


def _turn(objs, euler_deg):
    for ob in objs:
        ob.rotation_euler = tuple(math.radians(a) for a in euler_deg)
    return objs


def board_tool(asset="TOOL_Pickaxe", filename="lot2_TOOL_Pickaxe.png", keep=False):
    """Planche d'un outil : profil, trois-quarts, dessus + mise a l'echelle (mannequin, ORE_F2 or)."""
    clear()
    parts = ("Handle", "Head")
    lift = 2.4
    _turn(place(asset, parts, (-10.0, 0.0, lift), tag="_profil"), (0.0, 0.0, 90.0))
    _turn(place(asset, parts, (-3.5, 0.0, lift), tag="_3q"), (0.0, -18.0, 40.0))
    _turn(place(asset, parts, (3.0, 0.0, lift), tag="_dessus"), (55.0, 0.0, 90.0))
    label("profil", (-11.2, -3.2, 0.1), size=0.7)
    label("trois-quarts", (-5.2, -3.2, 0.1), size=0.7)
    label("dessus", (1.9, -3.2, 0.1), size=0.7)
    label("echelle", (11.5, -3.2, 0.1), size=0.7)
    mannequin((9.5, 0.0, 0.0))
    # outil debout, pommeau au sol, tete en haut, fer de profil
    _turn(place(asset, parts, (12.6, 0.0, 1.8), tag="_debout"), (-90.0, 0.0, 90.0))
    place("ORE_F2", ("Rock", "Crystals"), (17.0, 0.0, 0.0), tint="Gold", tag="_ech")
    stage(center=(4.0, 0.0, 2.3), width=34.0, height=13.0)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


def board_tools(filename="lot2_TOOL.png", keep=False):
    """Planche du lot 2 : pioche et marteau en profil et trois-quarts + echelle (mannequin)."""
    clear()
    parts = ("Handle", "Head")
    lift = 2.2
    _turn(place("TOOL_Pickaxe", parts, (-9.0, 0.0, lift), tag="_profil"), (0.0, 0.0, 90.0))
    _turn(place("TOOL_Hammer", parts, (-5.3, 0.0, lift), tag="_profil"), (0.0, 0.0, 90.0))
    _turn(place("TOOL_Pickaxe", parts, (-1.4, 0.0, lift), tag="_3q"), (0.0, -18.0, 40.0))
    _turn(place("TOOL_Hammer", parts, (2.0, 0.0, lift), tag="_3q"), (0.0, -18.0, 40.0))
    label("profil", (-8.2, -2.6, 0.1), size=0.6)
    label("trois-quarts", (-1.4, -2.6, 0.1), size=0.6)
    label("echelle", (8.0, -2.6, 0.1), size=0.6)
    mannequin((6.4, 0.0, 0.0))
    # outils debout, pommeau au sol, tete en haut, de profil
    _turn(place("TOOL_Pickaxe", parts, (9.6, 0.0, 1.8), tag="_debout"), (-90.0, 0.0, 90.0))
    _turn(place("TOOL_Hammer", parts, (12.0, 0.0, 1.1), tag="_debout"), (-90.0, 0.0, 90.0))
    stage(center=(1.2, 0.0, 2.3), width=26.0, height=9.0)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


def board_frg_anvil(filename="lot3_FRG_Anvil.png", keep=False):
    """Planche de FRG_Anvil : face, trois-quarts avant avec lingot, echelle (mannequin, ORE_F1)."""
    clear()
    parts = ("Body", "Stump", "Band")
    place("FRG_Anvil", parts, (-7.0, 0.0, 0.0), tag="_face")
    _turn(place("FRG_Anvil", parts, (-1.0, 0.0, 0.0), tag="_3q"), (0.0, 0.0, 35.0))
    _turn(place("ING_Bar", ("Bar",), (-1.0, 0.0, 3.0), tint="Copper", tag="_3q"), (0.0, 0.0, 35.0))
    mannequin((5.0, 0.0, 0.0))
    _turn(place("FRG_Anvil", parts, (9.9, -0.5, 0.0), tag="_ech"), (0.0, 0.0, -30.0))
    place("ORE_F1", ("Rock", "Crystals"), (14.0, 0.0, 0.0), tint="Iron", tag="_ech")
    label("face", (-7.8, -3.4, 0.1), size=0.7)
    label("trois-quarts + lingot", (-4.2, -3.4, 0.1), size=0.7)
    label("echelle", (8.0, -3.4, 0.1), size=0.7)
    stage(center=(3.5, 0.0, 2.3), width=28.0, height=11.0)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


def board_lot3(filename="lot3_FRG.png", keep=False):
    """Planche du lot 3 : enclume, fourneau, etabli de trois-quarts avant + mannequin + marteau."""
    clear()
    turn = (0.0, 0.0, 30.0)
    _turn(place("FRG_Anvil", ("Body", "Stump", "Band"), (-14.5, -1.0, 0.0), tag="_l3"), turn)
    mannequin((-9.0, -1.0, 0.0))
    furnace = _turn(place("FRG_Furnace", ("Base", "Body", "Hood", "Glow", "Embers"),
                          (-0.5, 1.0, 0.0), tag="_l3"), turn)
    for ob in furnace:
        if ob.name.startswith("PV_FRG_Furnace_Glow"):
            ob.data.materials[0] = pv_material("#FF7A1A", "Neon")
        elif ob.name.startswith("PV_FRG_Furnace_Embers"):
            ob.data.materials[0] = pv_material("#FFB347", "Neon")
    _turn(place("FRG_Workbench", ("Top", "Legs", "Vise", "Props", "Props_Steel"),
                (11.5, -1.0, 0.0), tag="_l3"), turn)
    # medaillon : marteau retouche, grossi 3x (apercu uniquement)
    for ob in _turn(place("TOOL_Hammer", ("Handle", "Head"), (21.5, -1.0, 4.2), tag="_l3"),
                    (0.0, -18.0, 40.0)):
        ob.scale = (3.0, 3.0, 3.0)
    label("FRG_Anvil", (-16.6, -6.5, 0.1), size=0.8)
    label("FRG_Furnace", (-3.2, -6.5, 0.1), size=0.8)
    label("FRG_Workbench", (8.2, -6.5, 0.1), size=0.8)
    label("TOOL_Hammer x3", (18.3, -6.5, 0.1), size=0.8)
    stage(center=(3.5, 0.0, 4.6), width=46.0, height=19.0)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


# ------------------------------------------------------------- coffres (VLT)
VLT_FIXED = ("Body", "Bands", "Corners", "Interior")
VLT_MOVING = ("Door", "DoorFrame", "DoorStuds", "Handle")


def place_vault(asset, offset, turn_deg=0.0, door_deg=0.0, tag="", gold=None,
                gold_size=(2.0, 2.0, 0.6)):
    """Copie un coffre en `offset`, tourne de turn_deg, porte ouverte de door_deg autour du bord +X
    de la boite englobante de DoorAssembly (comme le jeu). gold = (x, y, z) du repere GoldPoint :
    pose un tas d'or temoin de taille gold_size (apercu uniquement).
    """
    coll = bpy.data.collections[PREVIEW]
    src = bpy.data.collections[asset]
    world = (Matrix.Translation(lw.Vector(offset))
             @ Matrix.Rotation(math.radians(turn_deg), 4, "Z"))
    moving = [ob for ob in lw.meshes(src.all_objects) if ob.parent is not None]
    los, his = zip(*(lw.world_bounds(ob) for ob in moving))
    pivot = lw.Vector((max(p.x for p in his),
                       (min(p.y for p in los) + max(p.y for p in his)) / 2.0, 0.0))
    swing = (Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(door_deg), 4, "Z")
             @ Matrix.Translation(-pivot))
    made = []
    for ob in lw.meshes(src.all_objects):
        if ob.get("lw_marker"):
            continue
        cp = ob.copy()
        cp.data = ob.data.copy()
        cp.name = "PV_%s_%s%s" % (asset, ob["lw_part"], tag)
        cp.parent = None
        base = world @ swing if ob.parent is not None else world
        cp.matrix_world = base @ Matrix.Translation(ob.matrix_world.translation)
        coll.objects.link(cp)
        made.append(cp)
    if gold is not None:
        bm = lw.box_bm(gold_size, (gold[0], gold[1], gold[2] + gold_size[2] / 2.0))
        g = lw.add_object(PREVIEW, "Gold" + tag, bm, coll, "#F2C12E")
        g.name = "PV_Gold" + tag
        g.matrix_world = world
        made.append(g)
    return made


def board_vlt(asset="VLT_Lvl1", filename="lot4a_VLT_Lvl1.png", gold=(0.0, -0.5, 0.95),
              pitch=9.0, width=40.0, height=15.0, keep=False):
    """Planche d'un coffre : face, trois-quarts ferme, ouvert (cavite + tas d'or temoin), mannequin."""
    clear()
    mannequin((-1.5 * pitch - 6.0, 0.0, 0.0))
    place_vault(asset, (-1.5 * pitch, 0.0, 0.0), tag="_face")
    place_vault(asset, (-0.5 * pitch, 0.0, 0.0), turn_deg=32.0, tag="_3q")
    place_vault(asset, (0.5 * pitch, 0.0, 0.0), turn_deg=32.0, door_deg=100.0, tag="_open")
    place_vault(asset, (1.5 * pitch + 1.0, 0.0, 0.0), turn_deg=-22.0, door_deg=100.0, tag="_gold",
                gold=gold)
    y = -8.5
    label("face", (-1.5 * pitch - 1.0, y, 0.1), size=0.7)
    label("trois-quarts", (-0.5 * pitch - 2.5, y, 0.1), size=0.7)
    label("porte ouverte 100", (0.5 * pitch - 3.5, y, 0.1), size=0.7)
    label("ouvert + or 2 x 2 x 0,6", (1.5 * pitch - 4.0, y, 0.1), size=0.7)
    stage(center=(-1.5, -2.0, 2.6), width=width, height=height)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


# (asset, x sur la planche, repere GoldPoint, taille du tas d'or temoin)
VLT_ROW = [("VLT_Lvl1", -11.0, (0.0, -0.5, 0.95), (2.0, 2.0, 0.6)),
           ("VLT_Lvl2", -1.0, (0.0, -0.3, 1.75), (3.0, 3.0, 1.2)),
           ("VLT_Lvl3", 14.0, (0.0, -0.5, 3.0), (4.0, 4.0, 2.0))]


def board_vlt_all(filename="lot4a_VLT.png", open_filename="lot4a_VLT_ouverts.png", keep=False):
    """Deux planches : les 3 coffres fermes de trois-quarts, puis ouverts a 100 deg avec or temoin."""
    paths = []
    for name, turn, door_deg, spread in ((filename, 30.0, 0.0, 1.0),
                                         (open_filename, -24.0, 100.0, 1.25)):
        clear()
        mannequin((VLT_ROW[0][1] * spread - 6.5, -1.0, 0.0))
        for asset, x, gold, size in VLT_ROW:
            place_vault(asset, (x * spread, 0.0, 0.0), turn_deg=turn, door_deg=door_deg,
                        tag="_all", gold=gold if door_deg else None, gold_size=size)
            label(asset, (x * spread - 2.5, -11.5 if door_deg else -8.5, 0.1), size=0.9)
        width = 50.0 * spread
        stage(center=(1.0 * spread, -3.0 if door_deg else -1.0, 5.5), width=width,
              height=width * 0.5)
        paths.append(render_to(name))
        if not keep:
            cleanup()
    return paths


# ------------------------------------------------------------- effets (FX)
def _fx_pile(asset, offset, tag, part="Pile"):
    """Copie d'un tas d'or (ou d'une piece) avec l'apercu du materiau Roblox Metal."""
    made = place(asset, (part,), offset, tag=tag)
    mat = bpy.data.materials.get("PV_Gold") or bpy.data.materials.new("PV_Gold")
    rgba = lw.hex_rgba("#F2C12E")
    mat.diffuse_color = rgba
    if mat.node_tree is None:
        mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is not None:        # metal adouci : facettes lisibles sans reflets satures
        _set(bsdf, "Base Color", rgba)
        _set(bsdf, "Metallic", 0.45)
        _set(bsdf, "Roughness", 0.75)
    for ob in made:
        ob.data.materials[0] = mat
    return made


def pv_alpha(hex_color, alpha, emission=0.0):
    """Materiau d'apercu semi-transparent (Glass, ForceField)."""
    name = "PV_Alpha%d_%s" % (int(alpha * 100), hex_color.lstrip("#").upper())
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    rgba = lw.hex_rgba(hex_color)
    mat.diffuse_color = rgba[:3] + (alpha,)
    if mat.node_tree is None:
        mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is not None:
        _set(bsdf, "Base Color", rgba)
        _set(bsdf, "Alpha", alpha)
        _set(bsdf, "Roughness", 0.25)
        _set(bsdf, "Emission Color", rgba)
        _set(bsdf, "Emission Strength", emission)
    for attr, value in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(mat, attr, value)
        except (AttributeError, TypeError):
            pass
    return mat


def _zoom(objs, offset, zoom):
    """Grossit un asset multi-pieces autour de son origine posee en `offset` (medaillon)."""
    o = lw.Vector(offset)
    for ob in objs:
        ob.location = o + (ob.location - o) * zoom
        ob.scale = (zoom,) * 3
    return objs


def _fx_beacon(offset, tag, zoom=1.0, turn=0.0):
    objs = place("FX_AlarmBeacon", ("Base", "Dome", "Reflector"), offset, tag=tag)
    for ob in objs:
        if "_Dome" in ob.name:
            ob.data.materials[0] = pv_alpha("#FF2A2A", 0.4, 0.15)
            ob.visible_shadow = False
        elif "_Reflector" in ob.name:
            ob.data.materials[0] = pv_material("#FF2A2A", "Neon")
    _zoom(objs, offset, zoom)
    return _turn(objs, (0.0, 0.0, turn))


def board_fx(filename="lot5_FX.png", keep=False):
    """Planche du lot 5 : tas d'or S / M / L (echelle 1 et x2,5), piece, gyrophare, bouclier."""
    clear()
    back = 11.0
    mannequin((-25.0, 0.0, 0.0))
    for name, x, bx in (("S", -20.5, -21.0), ("M", -16.5, -13.5), ("L", -11.5, -4.0)):
        _turn(_fx_pile("FX_GoldPile_" + name, (x, 0.0, 0.0), "_row"), (0.0, 0.0, 20.0))
        label(name, (x - 0.3, -3.2, 0.1), size=0.8)
        for ob in _turn(_fx_pile("FX_GoldPile_" + name, (bx, back, 0.0), "_big"),
                        (0.0, 0.0, 20.0)):
            ob.scale = (2.5,) * 3
    label("FX_GoldPile  S / M / L  x2,5", (-19.5, back - 6.5, 0.1), size=0.8)
    label("echelle 1", (-26.5, -5.0, 0.1), size=0.8)
    # piece : echelle 1 puis medaillon x8
    _fx_pile("FX_Coin", (-7.6, 0.0, 0.5), "_1", part="Coin")
    label("FX_Coin", (-9.0, -3.2, 0.1), size=0.8)
    for ob in _turn(_fx_pile("FX_Coin", (4.0, back, 3.0), "_x8", part="Coin"), (0.0, 0.0, 28.0)):
        ob.scale = (8.0,) * 3
    label("FX_Coin  x8", (1.8, back - 4.0, 0.1), size=0.8)
    # gyrophare : medaillon x4 (l'echelle 1 est sur le coffre)
    _fx_beacon((10.5, back, 0.0), "_x4", zoom=4.0, turn=25.0)
    label("FX_AlarmBeacon  x4", (7.0, back - 4.0, 0.1), size=0.8)
    # bouclier sur VLT_Lvl1 + gyrophare a l'echelle sur BeaconPoint
    cx = 19.0
    place_vault("VLT_Lvl1", (cx, 0.0, 0.0), tag="_sh")
    _fx_beacon((cx, 0.0, 5.1), "_1")
    for ob in place("FX_Shield_Dome", ("Dome",), (cx, 0.0, 0.0), tag="_sh"):
        ob.data.materials[0] = pv_alpha("#4FC3FF", 0.28, 0.25)
        ob.visible_shadow = False
    for ob in place("FX_Shield_Ring", ("Ring",), (cx, 0.0, 0.0), tag="_sh"):
        ob.data.materials[0] = pv_material("#4FC3FF", "Neon")
    label("FX_Shield_Dome + FX_Shield_Ring", (cx - 8.5, -7.6, 0.1), size=0.8)
    label("VLT_Lvl1 + FX_AlarmBeacon echelle 1", (cx - 8.5, -9.2, 0.1), size=0.8)
    stage(center=(-1.5, 3.5, 2.5), width=56.0, height=30.0)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


FX_GOLD = {"VLT_Lvl1": "FX_GoldPile_S", "VLT_Lvl2": "FX_GoldPile_M", "VLT_Lvl3": "FX_GoldPile_L"}


def board_fx_gold_in_vaults(filename="lot5_FX_or_dans_coffres.png", turn=8.0, keep=False):
    """Les trois coffres ouverts avec S / M / L poses sur GoldPoint (copies d'apercu)."""
    clear()
    spread = 1.25
    mannequin((VLT_ROW[0][1] * spread - 6.5, -1.0, 0.0))
    for asset, x, gold, _size in VLT_ROW:
        place_vault(asset, (x * spread, 0.0, 0.0), turn_deg=turn, door_deg=110.0, tag="_g")
        world = (Matrix.Translation((x * spread, 0.0, 0.0))
                 @ Matrix.Rotation(math.radians(turn), 4, "Z"))
        for ob in _fx_pile(FX_GOLD[asset], (0.0, 0.0, 0.0), "_g"):
            ob.matrix_world = world @ Matrix.Translation(gold)
        label("%s + %s" % (asset, FX_GOLD[asset]), (x * spread - 5.0, -11.5, 0.1), size=0.8)
    width = 50.0 * spread
    stage(center=(1.0 * spread, -3.0, 5.5), width=width, height=width * 0.5)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


def board_fx_goldpile(asset="FX_GoldPile_M", vault="VLT_Lvl2", gold=(0.0, -0.3, 1.75),
                      filename="lot5_FX_GoldPile_M.png", zoom=3.0, keep=False):
    """Planche d'un tas d'or : gros plan trois-quarts avant, plongee, puis pose sur GoldPoint dans
    le coffre porte ouverte (copies d'apercu : le coffre lui-meme n'est pas modifie)."""
    clear()

    def pile(offset, tag):
        return _fx_pile(asset, offset, tag)

    for ob in _turn(pile((-14.0, 0.0, 0.0), "_3q"), (0.0, 0.0, 30.0)):
        ob.scale = (zoom,) * 3
    for ob in _turn(pile((-2.5, 0.0, 5.0), "_top"), (52.0, 0.0, 0.0)):
        ob.scale = (zoom,) * 3
    mannequin((7.5, -1.0, 0.0))
    turn = 8.0
    place_vault(vault, (16.0, 0.0, 0.0), turn_deg=turn, door_deg=110.0, tag="_fx")
    world = (Matrix.Translation((16.0, 0.0, 0.0)) @ Matrix.Rotation(math.radians(turn), 4, "Z"))
    for ob in pile((0.0, 0.0, 0.0), "_in"):
        ob.matrix_world = world @ Matrix.Translation(gold)
    label("%s x%d  trois-quarts avant" % (asset, zoom), (-19.5, -8.0, 0.1), size=0.8)
    label("x%d  plongee" % zoom, (-5.0, -8.0, 0.1), size=0.8)
    label("dans %s (GoldPoint), porte ouverte" % vault, (8.5, -11.0, 0.1), size=0.8)
    stage(center=(2.5, -2.5, 4.5), width=48.0, height=21.0)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


# ------------------------------------------------------- environnement (MIN)
def pv_black():
    """Materiau noir mat : controle de la silhouette."""
    mat = bpy.data.materials.get("PV_Black") or bpy.data.materials.new("PV_Black")
    mat.diffuse_color = (0.0, 0.0, 0.0, 1.0)
    if mat.node_tree is None:
        mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is not None:
        _set(bsdf, "Base Color", (0.0, 0.0, 0.0, 1.0))
        _set(bsdf, "Roughness", 1.0)
        for ident in ("Specular IOR Level", "Specular"):
            _set(bsdf, ident, 0.0)
    return mat


def board_min_rock(asset="MIN_Rock_Deco_A", filename="lot6_MIN_Rock_Deco_A.png",
                   angles=(0.0, 90.0, 180.0, 270.0), pitch=4.5, keep=False):
    """Planche d'un rocher decoratif : mannequin, ORE_F1 (reference de style), le rocher sous
    plusieurs angles (rotation autour de Z), puis sa silhouette noire a cote de celle de la roche
    d'ORE_F1 sans cristaux."""
    clear()
    mannequin((-11.5, 0.0, 0.0))
    place("ORE_F1", ("Rock", "Crystals"), (-6.5, 0.0, 0.0), tint="Iron", tag="_ref")
    label("ORE_F1 (reference)", (-9.3, -3.6, 0.1), size=0.6)
    x = -1.0
    for a in angles:
        _turn(place(asset, ("Rock",), (x, 0.0, 0.0), tag="_%d" % a), (0.0, 0.0, a))
        label("%d" % a, (x - 0.4, -3.6, 0.1), size=0.6)
        x += pitch
    label(asset, (-1.0 + pitch * 0.2, -4.6, 0.1), size=0.6)
    x += 0.5
    black = pv_black()
    for ob in place(asset, ("Rock",), (x, 0.0, 0.0), tag="_sil"):
        ob.data.materials[0] = black
    for ob in place("ORE_F1", ("Rock",), (x + 4.6, 0.0, 0.0), tag="_sil"):
        ob.data.materials[0] = black
    label("silhouettes : rocher / roche ORE_F1", (x - 1.5, -3.6, 0.1), size=0.6)
    right = x + 4.6 + 3.0
    width = right + 14.5
    stage(center=((right - 14.5) / 2.0, -0.6, 2.0), width=width, height=width * 0.3)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


# ------------------------------------------------------------- lot 6 complet
def _neon(objs, part, hex_color):
    for ob in objs:
        if ob.name.startswith("PV_") and ("_%s_" % part) in ob.name + "_":
            ob.data.materials[0] = pv_material(hex_color, "Neon")
    return objs


def _lantern(offset, tag):
    objs = place("MIN_Lantern_Post", ("Post", "Light"), offset, tag=tag)
    for ob in objs:
        if "_Light" in ob.name:
            ob.data.materials[0] = pv_material("#FFD966", "Neon")
    return objs


def board_lot6_min(filename="lot6_MIN.png", keep=False):
    """Planche MIN : rochers A / B / C (plusieurs angles + silhouettes), lanterne, ORE_F1, mannequin."""
    clear()
    mannequin((-17.5, 0.0, 0.0))
    place("ORE_F1", ("Rock", "Crystals"), (-12.0, 0.0, 0.0), tint="Iron", tag="_ref")
    label("ORE_F1 (reference)", (-15.5, -5.2, 0.1), size=0.7)
    xs = {"A": -6.0, "B": 0.5, "C": 9.5}
    for k, x in xs.items():
        asset = "MIN_Rock_Deco_" + k
        place(asset, ("Rock",), (x, 0.0, 0.0), tag="_0")
        label(asset, (x - 3.0, -5.2 if k == "C" else -4.2, 0.1), size=0.7)
    _lantern((17.0, 0.0, 0.0), "_0")
    label("MIN_Lantern_Post", (14.0, -4.2, 0.1), size=0.7)
    # rang arriere : autres angles
    y = 11.0
    x = -15.0
    for k, angles, pitch in (("A", (120.0, 240.0), 4.0), ("B", (120.0, 240.0), 6.5),
                             ("C", (180.0,), 9.5)):
        for a in angles:
            _turn(place("MIN_Rock_Deco_" + k, ("Rock",), (x, y, 0.0), tag="_%d" % a),
                  (0.0, 0.0, a))
            x += pitch
    label("autres angles (120 / 240 ; C : 180)", (-17.0, y + 4.5, 0.1), size=0.7)
    # silhouettes
    y = 21.0
    black = pv_black()
    for asset, part, x in (("ORE_F1", "Rock", -12.0), ("MIN_Rock_Deco_A", "Rock", -6.0),
                           ("MIN_Rock_Deco_B", "Rock", 0.5), ("MIN_Rock_Deco_C", "Rock", 9.5),
                           ("MIN_Lantern_Post", "Post", 17.0)):
        for ob in place(asset, (part,), (x, y, 0.0), tag="_sil"):
            ob.data.materials[0] = black
    for ob in place("MIN_Lantern_Post", ("Light",), (17.0, y, 0.0), tag="_sil"):
        ob.data.materials[0] = black
    label("silhouettes", (-17.0, y - 4.5, 0.1), size=0.7)
    stage(center=(0.5, 9.0, 2.0), width=42.0, height=30.0, res_x=2200)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


def _plot_scene(origin):
    """Parcelle montee (apercu) : sol, dalle, coffre Lvl1, cloture sur 3 cotes, panneau."""
    ox, oy = origin
    place("ENV_Plot_Base", ("Base", "Border"), (ox, oy, 0.0), tag="_plot")
    place("ENV_Plot_VaultPad", ("Pad", "Rivets"), (ox, oy + 4.0, 1.0), tag="_plot")
    place_vault("VLT_Lvl1", (ox, oy + 4.0, 1.4), tag="_plot")
    for i in range(4):
        x = ox - 12.0 + 8.0 * i
        place("ENV_Plot_Fence", ("Fence",), (x, oy + 15.5, 1.0), tag="_b%d" % i)
        for s in (-1, 1):
            _turn(place("ENV_Plot_Fence", ("Fence",), (ox + s * 15.5, oy - 12.0 + 8.0 * i, 1.0),
                        tag="_s%d%d" % (i, s)), (0.0, 0.0, 90.0))
    place("ENV_Plot_Sign", ("Frame", "Board"), (ox - 10.0, oy - 13.0, 1.0), tag="_plot")
    mannequin((ox + 7.0, oy - 8.0, 1.0)).name = "PV_Mannequin_plot"


def board_lot6_env(filename="lot6_ENV.png", keep=False):
    """Planche ENV : chaque asset isole au premier rang + une parcelle montee au second rang."""
    clear()
    y = 0.0
    mannequin((-34.0, y, 0.0))
    place("ENV_Plot_Fence", ("Fence",), (-30.0 + 4.0, y, 0.0), tag="_a")
    place("ENV_Plot_Fence", ("Fence",), (-30.0 + 12.0, y, 0.0), tag="_b")
    label("ENV_Plot_Fence x2", (-29.5, y - 3.5, 0.1), size=0.8)
    place("ENV_Plot_Sign", ("Frame", "Board"), (-8.0, y, 0.0), tag="_0")
    label("ENV_Plot_Sign", (-11.5, y - 3.5, 0.1), size=0.8)
    _neon(place("ENV_SpawnPad", ("Base", "Ring"), (2.5, y, 0.0), tag="_0"), "Ring", "#4FC3FF")
    mannequin((2.5, y, 0.46)).name = "PV_Mannequin_spawn"
    label("ENV_SpawnPad", (-1.0, y - 7.5, 0.1), size=0.8)
    place("ENV_Zone_Sign", ("Frame", "Board"), (15.0, y, 0.0), tag="_0")
    mannequin((15.0, y, 0.0)).name = "PV_Mannequin_zone"
    label("ENV_Zone_Sign", (11.5, y - 3.5, 0.1), size=0.8)
    for i, (x, topper, part) in enumerate(((29.0, "ENV_LB_Topper_Crown", "Crown"),
                                           (44.0, "ENV_LB_Topper_Mask", "Mask"))):
        place("ENV_Leaderboard", ("Frame", "Screen"), (x, y, 0.0), tag="_%d" % i)
        tp = place(topper, (part,), (x, y, 10.0), tag="_%d" % i)
        if part == "Crown":
            for ob in tp:
                ob.data.materials[0] = pv_material("#F2C12E", "Metal")
        label("ENV_Leaderboard + " + topper[7:], (x - 6.5, y - 3.5, 0.1), size=0.8)
    # second rang : parcelle montee, dalle seule, ornements grossis
    _plot_scene((-14.0, 30.0))
    label("ENV_Plot_Base + VaultPad + VLT_Lvl1 + Fence + Sign", (-30.0, 11.5, 0.1), size=0.8)
    place("ENV_Plot_VaultPad", ("Pad", "Rivets"), (16.0, 24.0, 0.0), tag="_solo")
    mannequin((16.0, 24.0, 0.4)).name = "PV_Mannequin_pad"
    label("ENV_Plot_VaultPad", (11.0, 15.0, 0.1), size=0.8)
    for ob in _turn(place("ENV_LB_Topper_Crown", ("Crown",), (32.0, 24.0, 0.0), tag="_x3"),
                    (0.0, 0.0, 25.0)):
        ob.scale = (3.0,) * 3
        ob.data.materials[0] = pv_material("#F2C12E", "Metal")
    for ob in _turn(place("ENV_LB_Topper_Mask", ("Mask",), (44.0, 24.0, 0.0), tag="_x3"),
                    (0.0, 0.0, 25.0)):
        ob.scale = (3.0,) * 3
    label("Topper_Crown x3", (28.0, 19.0, 0.1), size=0.8)
    label("Topper_Mask x3", (40.0, 19.0, 0.1), size=0.8)
    _lantern((38.0, 36.0, 0.0), "_env")
    stage(center=(8.0, 17.0, 3.0), width=92.0, height=52.0, res_x=2600)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


# ------------------------------------------------------------- serrures (LCK)
def board_lck(asset="LCK_T1", parts=("Tint", "Shackle", "Keyhole"),
              filename="lot4b_LCK_T1.png", zoom=3.0, keep=False):
    """Planche d'une serrure : face / trois-quarts / profil (grossie x zoom) en fer, or et
    Aetherite (Neon), puis a l'echelle 1 sur le LockSocket de VLT_Lvl1 avec le mannequin."""
    clear()
    views = (("face", 0.0), ("trois-quarts", 40.0), ("profil", 90.0))
    tints = ("Iron", "Gold", "Aetherite")
    for r, metal in enumerate(tints):
        y = 9.0 * r
        for c, (_name, ang) in enumerate(views):
            off = (-16.0 + 7.0 * c, y, 3.2)
            objs = place(asset, parts, off, tint=metal, tag="_%d%d" % (r, c))
            _zoom(objs, off, zoom)
            _turn(objs, (0.0, 0.0, ang))
        label(metal, (-23.5, y, 2.6), size=0.9)
    for c, (name, _ang) in enumerate(views):
        label(name, (-17.5 + 7.0 * c, -3.5, 0.1), size=0.8)
    label("x%d" % zoom, (-23.5, -3.5, 0.1), size=0.8)
    # echelle 1 : sur la porte de VLT_Lvl1 (copie d'apercu), LockSocket (0, -2.9, 3.5)
    for i, (metal, x, turn) in enumerate((("Iron", 8.0, 0.0), ("Gold", 16.5, 28.0),
                                          ("Aetherite", 25.0, -28.0))):
        world = (Matrix.Translation((x, 0.0, 0.0)) @ Matrix.Rotation(math.radians(turn), 4, "Z"))
        place_vault("VLT_Lvl1", (x, 0.0, 0.0), turn_deg=turn, tag="_l%d" % i)
        for ob in place(asset, parts, (0.0, 0.0, 0.0), tint=metal, tag="_v%d" % i):
            ob.matrix_world = world @ Matrix.Translation((0.0, -2.9, 3.5))
    mannequin((2.5, -1.5, 0.0))
    label("echelle 1 sur LockSocket de VLT_Lvl1", (5.0, -7.0, 0.1), size=0.8)
    stage(center=(2.5, 7.0, 3.0), width=58.0, height=31.0, res_x=2400)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


def place_lock(asset, world, tint=None, tag=""):
    """Copie toutes les pieces d'une serrure avec la matrice `world` appliquee a l'asset entier
    (les pieces mobiles gardent leur propre origine : Dial, Lever...)."""
    coll = bpy.data.collections[PREVIEW]
    made = []
    for ob in lw.meshes(bpy.data.collections[asset].all_objects):
        cp = ob.copy()
        cp.data = ob.data.copy()
        cp.name = "PV_%s_%s%s" % (asset, ob["lw_part"], tag)
        base = cp.data.materials[0]
        if tint is not None and base is not None and base.name == "LW_" + lw.TINT.lstrip("#"):
            cp.data.materials[0] = pv_material(*METALS[tint])
        cp.matrix_world = world @ Matrix.Translation(ob.matrix_world.translation)
        coll.objects.link(cp)
        made.append(cp)
    return made


def lock_on_vault(lock, vault, offset, turn_deg=0.0, tint=None, tag=""):
    """Coffre d'apercu en `offset` + serrure posee sur son repere LockSocket."""
    world = Matrix.Translation(lw.Vector(offset)) @ Matrix.Rotation(math.radians(turn_deg), 4, "Z")
    made = place_vault(vault, offset, turn_deg=turn_deg, tag=tag)
    socket = bpy.data.objects[vault + ".LockSocket"].matrix_world.translation
    return made + place_lock(lock, world @ Matrix.Translation(socket), tint=tint, tag=tag)


LCK_VAULT = (("LCK_T1", "VLT_Lvl1"), ("LCK_T2", "VLT_Lvl2"), ("LCK_T3", "VLT_Lvl3"))


def board_lck_all(filename="lot4b_LCK.png", zoom=3.0, keep=False):
    """Planche du lot 4b : T1 / T2 / T3 (face et trois-quarts, grossies x zoom) en fer, or et
    Aetherite, puis a l'echelle 1 chacune sur le LockSocket de son coffre, avec le mannequin."""
    clear()
    tints = ("Iron", "Gold", "Aetherite")
    pitch_x, pitch_y, x0, lift = 8.5, 13.0, -52.0, 4.0
    for r, metal in enumerate(tints):
        y = pitch_y * r
        for c, (asset, _vault) in enumerate(LCK_VAULT):
            for v, ang in enumerate((0.0, 40.0)):
                world = (Matrix.Translation((x0 + pitch_x * (2 * c + v), y, lift))
                         @ Matrix.Rotation(math.radians(ang), 4, "Z") @ Matrix.Scale(zoom, 4))
                place_lock(asset, world, tint=metal, tag="_%d%d%d" % (r, c, v))
        label(metal, (x0 - 11.5, y, 3.0), size=1.1)
    for c, (asset, _vault) in enumerate(LCK_VAULT):
        label(asset, (x0 + pitch_x * 2 * c - 2.0, -5.5, 0.1), size=1.0)
        label("face / trois-quarts", (x0 + pitch_x * 2 * c - 2.0, -7.2, 0.1), size=0.7)
    label("x%.1f" % zoom, (x0 - 11.5, -5.5, 0.1), size=1.0)
    # echelle 1 : chaque serrure sur son coffre
    mannequin((2.0, -2.0, 0.0))
    for i, ((lock, vault), x, metal) in enumerate(zip(LCK_VAULT, (8.5, 18.0, 31.5), tints)):
        lock_on_vault(lock, vault, (x, 0.0, 0.0), turn_deg=18.0, tint=metal, tag="_v%d" % i)
        label("%s sur %s" % (lock[4:], vault), (x - 4.0, -9.5 - 1.2 * (i == 2), 0.1), size=0.8)
    # second rang : les trois serrures (or) sur le meme coffre, pour comparer les tailles
    for i, (lock, _vault) in enumerate(LCK_VAULT):
        lock_on_vault(lock, "VLT_Lvl1", (8.5 + 7.0 * i, 27.0, 0.0), tint="Gold", tag="_c%d" % i)
    label("T1 / T2 / T3 sur VLT_Lvl1 (meme echelle)", (5.0, 22.5, 0.1), size=0.8)
    label("echelle 1", (0.5, -7.5, 0.1), size=0.8)
    stage(center=(-12.5, 10.5, 4.0), width=106.0, height=44.0, res_x=3200)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path


# ------------------------------------------------------------- planche globale
def _extent(asset):
    """(largeur X, profondeur Y, hauteur Z, y avant) de l'asset, reperes exclus."""
    obs = [ob for ob in lw.meshes(bpy.data.collections[asset].all_objects)
           if not ob.get("lw_marker")]
    los, his = zip(*(lw.world_bounds(ob) for ob in obs))
    lo = lw.Vector((min(p.x for p in los), min(p.y for p in los), min(p.z for p in los)))
    hi = lw.Vector((max(p.x for p in his), max(p.y for p in his), max(p.z for p in his)))
    return hi.x - lo.x, hi.y - lo.y, hi.z, lo.y


def _parts(asset):
    return tuple(ob["lw_part"] for ob in lw.meshes(bpy.data.collections[asset].all_objects)
                 if not ob.get("lw_marker"))


def _g_row(y, family, items, x0=0.0, gap=1.6, text=0.8):
    """Range `items` de gauche a droite sur la ligne y. item = (etiquette, largeur, y avant, fn)
    ou fn(x, y, tag) pose l'asset centre en x. Renvoie le x de fin."""
    label(family, (x0 - 27.0, y, 0.1), size=1.5)
    mannequin((x0 - 4.5, y, 0.0)).name = "PV_Mannequin_g%d" % int(y)
    x = x0
    for i, (text_i, width, front, fn) in enumerate(items):
        slot = max(width, 0.52 * text * len(text_i))
        cx = x + slot / 2.0
        fn(cx, y, "_g%d_%d" % (int(y), i))
        label(text_i, (cx - 0.26 * text * len(text_i), y + front - 1.3, 0.1), size=text)
        x += slot + gap
    return x


def board_global(filename="session3_global.png", keep=False):
    """Tous les assets a la meme echelle (1 stud = 1 unite), ranges par famille, avec un
    mannequin de 5 studs au debut de chaque ligne."""
    clear()

    def simple(asset, tint=None, lift=0.0, after=None, name=None):
        w, _d, _h, front = _extent(asset)

        def fn(x, y, tag):
            objs = place(asset, _parts(asset), (x, y, lift), tint=tint, tag=tag)
            if after is not None:
                after(objs)
        return (name or asset, w, front, fn)

    def neon(part, color):
        return lambda objs: _neon(objs, part, color)

    # ---- gisements + lingot
    row = []
    for asset, m1, m2 in (("ORE_F1", "Iron", "Copper"), ("ORE_F2", "Silver", "Gold"),
                          ("ORE_F3", "Cobalt", "Titanium"), ("ORE_F4", "Obsidium", "Aetherite")):
        w, _d, _h, front = _extent(asset)
        for metal in (m1, m2):
            def fn(x, y, tag, asset=asset, metal=metal):
                parts = tuple(p for p in _parts(asset) if p != "Crystals_Broken")
                place(asset, parts, (x, y, 0.0), tint=metal, tag=tag)
            row.append(("%s %s" % (asset, metal), w, front, fn))
    row.append(simple("ORE_Rubble"))
    row.append(simple("ORE_Chunk", tint="Cobalt", lift=0.42))
    row.append(simple("ING_Bar", tint="Copper"))
    ends = [_g_row(0.0, "Gisements, lingot", row)]

    # ---- outils + forge
    def tool(asset, lift):
        def fn(x, y, tag):
            _turn(place(asset, ("Handle", "Head"), (x, y, lift), tag=tag), (-90.0, 0.0, 90.0))
        return (asset, 2.4, -0.6, fn)

    def furnace(objs):
        _neon(objs, "Glow", "#FF7A1A")
        _neon(objs, "Embers", "#FFB347")

    def anvil(x, y, tag):
        place("FRG_Anvil", _parts("FRG_Anvil"), (x, y, 0.0), tag=tag)
        place("ING_Bar", ("Bar",), (x, y, 3.0), tint="Gold", tag=tag + "i")
    aw, _d, _h, afront = _extent("FRG_Anvil")
    ends.append(_g_row(34.0, "Outils, forge", [
        tool("TOOL_Pickaxe", 1.8), tool("TOOL_Hammer", 1.1),
        ("FRG_Anvil + ING_Bar", aw, afront, anvil),
        simple("FRG_Furnace", after=furnace), simple("FRG_Workbench")]))

    # ---- serrures + coffres
    def lock(asset, metal):
        def fn(x, y, tag):
            place_lock(asset, Matrix.Translation((x, y + 0.3, 1.6)), tint=metal, tag=tag)
        return ("%s %s" % (asset, metal), 2.6, -0.4, fn)

    def vault(asset, lck, metal):
        w, _d, _h, front = _extent(asset)

        def fn(x, y, tag):
            lock_on_vault(lck, asset, (x, y, 0.0), tint=metal, tag=tag)
        return ("%s + %s" % (asset, lck), w, front, fn)
    ends.append(_g_row(58.0, "Serrures, coffres", [
        lock("LCK_T1", "Iron"), lock("LCK_T2", "Gold"), lock("LCK_T3", "Aetherite"),
        vault("VLT_Lvl1", "LCK_T1", "Iron"), vault("VLT_Lvl2", "LCK_T2", "Gold"),
        vault("VLT_Lvl3", "LCK_T3", "Aetherite")]))

    # ---- effets
    def pile(asset, part="Pile", lift=0.0):
        w, _d, _h, front = _extent(asset)

        def fn(x, y, tag):
            _fx_pile(asset, (x, y, lift), tag, part=part)
        return (asset, w, front, fn)

    def beacon(x, y, tag):
        _fx_beacon((x, y, 0.0), tag)

    def shield(x, y, tag):
        place_vault("VLT_Lvl1", (x, y, 0.0), tag=tag)
        _fx_beacon((x, y, 5.1), tag + "b")
        for ob in place("FX_Shield_Dome", ("Dome",), (x, y, 0.0), tag=tag):
            ob.data.materials[0] = pv_alpha("#4FC3FF", 0.28, 0.25)
            ob.visible_shadow = False
        for ob in place("FX_Shield_Ring", ("Ring",), (x, y, 0.0), tag=tag):
            ob.data.materials[0] = pv_material("#4FC3FF", "Neon")
    sw, _d, _h, sfront = _extent("FX_Shield_Dome")
    ends.append(_g_row(18.0, "Effets", [
        pile("FX_GoldPile_S"), pile("FX_GoldPile_M"), pile("FX_GoldPile_L"),
        pile("FX_Coin", part="Coin", lift=0.5),
        ("FX_AlarmBeacon", 1.2, -0.6, beacon),
        ("FX_Shield_Dome + Ring, VLT_Lvl1 + AlarmBeacon", sw, sfront, shield)]))

    # ---- mine + environnement
    def lantern(x, y, tag):
        _lantern((x, y, 0.0), tag)

    def board(asset, topper, part):
        w, _d, _h, front = _extent(asset)

        def fn(x, y, tag):
            place(asset, _parts(asset), (x, y, 0.0), tag=tag)
            for ob in place(topper, (part,), (x, y, 10.0), tag=tag):
                if part == "Crown":
                    ob.data.materials[0] = pv_material("#F2C12E", "Metal")
        return ("Leaderboard + " + topper[4:], w, front, fn)
    lwid, _d, _h, lfront = _extent("MIN_Lantern_Post")
    ends.append(_g_row(84.0, "Mine, environnement", [
        simple("MIN_Rock_Deco_A"), simple("MIN_Rock_Deco_B"), simple("MIN_Rock_Deco_C"),
        ("MIN_Lantern_Post", lwid, lfront, lantern),
        simple("ENV_Plot_Sign"), simple("ENV_Plot_Fence"),
        simple("ENV_SpawnPad", after=neon("Ring", "#4FC3FF")), simple("ENV_Zone_Sign"),
        board("ENV_Leaderboard", "ENV_LB_Topper_Crown", "Crown"),
        board("ENV_Leaderboard", "ENV_LB_Topper_Mask", "Mask")]))

    # ---- parcelle montee + dalle seule
    y = 122.0
    label("Parcelle", (-27.0, y - 14.0, 0.1), size=1.5)
    _plot_scene((16.0, y))
    label("ENV_Plot_Base + Plot_VaultPad + VLT_Lvl1 + Plot_Fence + Plot_Sign", (0.0, y - 17.8, 0.1),
          size=0.8)
    place("ENV_Plot_VaultPad", ("Pad", "Rivets"), (46.0, y - 6.0, 0.0), tag="_gsolo")
    mannequin((46.0, y - 6.0, 0.4)).name = "PV_Mannequin_gpad"
    label("ENV_Plot_VaultPad", (41.0, y - 14.8, 0.1), size=0.8)

    right = max(ends + [54.0])
    width = right + 32.0
    stage(center=((right - 29.0) / 2.0, 68.0, 0.0), width=width, height=96.0, res_x=4400)
    path = render_to(filename)
    if not keep:
        cleanup()
    return path
