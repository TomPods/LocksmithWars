"""Locksmith Wars - categorie FRG (forge : enclume, fourneau, etabli)."""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import lw_common as lw

CATEGORY = "FRG"
STEEL_DARK = "#2E2E33"
BRICK = "#6B3A2A"
STONE = "#5B5650"
HOOD_METAL = "#3B3F45"
GLOW = "#FF7A1A"
EMBER = "#FFB347"
WOOD_DARK = "#5C3A1E"
BRASS = "#C9A14A"
WOOD = "#8B5A2B"
IRON = "#5A5F66"


# ------------------------------------------------------------ primitives
def lathe_z_bm(profile, sides=8, phase=22.5, bm=None):
    """Solide de revolution facette autour de l'axe Z. profile = [(rayon, z), ...] de bas en haut."""
    if bm is None:
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
    return bm


def loft_chamfer_z_bm(bm, sections, chamfer=0.1, cy=0.0):
    """Bloc a sections rectangulaires aux coins chanfreines, empilees le long de Z.

    sections = [(z, demi-x, demi-y), ...] de bas en haut, centrees sur x = 0, y = cy.
    """
    rings = []
    for z, hx, hy in sections:
        c = min(chamfer, hx * 0.45, hy * 0.45)
        pts = ((-hx + c, -hy), (hx - c, -hy), (hx, -hy + c), (hx, hy - c),
               (hx - c, hy), (-hx + c, hy), (-hx, hy - c), (-hx, -hy + c))
        rings.append([bm.verts.new((x, y + cy, z)) for x, y in pts])
    for lo, hi in zip(rings, rings[1:]):
        for i in range(8):
            j = (i + 1) % 8
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    return bm


def horn_bm(bm, sections, tip, sides=8):
    """Corne conique le long de X : sections = [(x, z centre, rayon y, rayon z), ...] puis pointe."""
    rings = [[bm.verts.new((x, ry * math.cos(t), zc + rz * math.sin(t)))
              for t in (math.radians(22.5) + 2.0 * math.pi * i / sides for i in range(sides))]
             for x, zc, ry, rz in sections]
    for lo, hi in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    apex = bm.verts.new(tip)
    for i in range(sides):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % sides], apex))
    bm.faces.new(list(reversed(rings[0])))
    return bm


def finish(asset, entries):
    lw.update_manifest(asset, entries)
    path = lw.export_asset(asset, CATEGORY)
    lw.report(asset)
    lw.save_blend()
    return path


# -------------------------------------------------------------- FRG_Anvil
ANVIL_TABLE_Z = 3.0                # contrat : le code pose le lingot a cette hauteur
ANVIL_STUMP_H = 1.5
# billot : (rayon, z)
ANVIL_STUMP = [(1.10, 0.0), (1.22, 0.12), (1.15, 1.38), (1.04, ANVIL_STUMP_H)]
# cerclage : (rayon, z), depasse le billot de ~0,09
ANVIL_BAND = [(1.10, 0.90), (1.26, 0.97), (1.26, 1.21), (1.10, 1.28)]
# corps : (z, demi-x, demi-y) pied, taille, evasement, table
ANVIL_BODY = [(1.50, 0.86, 0.60), (1.72, 0.86, 0.60), (1.86, 0.72, 0.48),
              (2.02, 0.50, 0.40), (2.26, 0.50, 0.40), (2.56, 1.30, 0.72),
              (2.90, 1.30, 0.72), (ANVIL_TABLE_Z, 1.20, 0.62)]
# corne vers -X : (x, z centre, rayon y, rayon z), dessus 0,06 sous la table
ANVIL_HORN = [(-1.22, 2.62, 0.60, 0.34), (-1.66, 2.66, 0.50, 0.29),
              (-2.12, 2.74, 0.32, 0.19)]
ANVIL_HORN_TIP = (-2.60, 0.0, 2.86)


def build_frg_anvil():
    """Enclume sur billot : Body (acier), Stump (bois), Band (cerclage), repere IngotPoint."""
    asset = "FRG_Anvil"
    coll = lw.reset_collection(asset)

    stump = lathe_z_bm(ANVIL_STUMP)
    band = lathe_z_bm(ANVIL_BAND)
    body = loft_chamfer_z_bm(bmesh.new(), ANVIL_BODY, chamfer=0.1)
    horn_bm(body, ANVIL_HORN, ANVIL_HORN_TIP)

    lw.add_object(asset, "Body", body, coll, STEEL_DARK)
    lw.add_object(asset, "Stump", stump, coll, WOOD)
    lw.add_object(asset, "Band", band, coll, IRON)
    lw.add_marker(asset, "IngotPoint", coll, (0.0, 0.0, ANVIL_TABLE_Z))
    return finish(asset, [
        {"object": "Body", "color": STEEL_DARK, "material": "Metal", "canCollide": True,
         "role": "fixed",
         "notes": "Enclume. Dessus de table a Y Roblox = 3,0 exactement ; table plane "
                  "2,4 x 1,24 centree sur l'origine. Corne vers +X Roblox (-X Blender, gauche du "
                  "joueur place devant), talon carre a l'oppose. Origine au sol, centre du billot."},
        {"object": "Stump", "color": WOOD, "material": "WoodPlanks", "canCollide": True,
         "role": "fixed", "notes": "Billot octogonal, hauteur 1,5. Origine au sol, centre."},
        {"object": "Band", "color": IRON, "material": "Metal", "canCollide": False,
         "role": "fixed", "notes": "Cerclage de fer du billot. Origine au sol, centre."},
        {"object": "IngotPoint", "color": lw.MARKER_COLOR, "material": "SmoothPlastic",
         "canCollide": False, "role": "marker",
         "notes": "Centre de la table, (0, 3.0, 0) Roblox : base du lingot ING_Bar."},
    ])


# ------------------------------------------------- primitives (fourneau, etabli)
def block_bm(bm, size, center, bevel=0.0, rot_z=0.0):
    """Pave (x, y, z) centre en `center`, aretes chanfreinees de `bevel`, tourne de rot_z degres."""
    tmp = bmesh.new()
    res = bmesh.ops.create_cube(tmp, size=1.0)
    for v in res["verts"]:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel > 0.0:
        bmesh.ops.bevel(tmp, geom=tmp.edges[:], offset=bevel, offset_type="OFFSET", segments=1,
                        profile=0.5, affect="EDGES")
    mat = Matrix.Translation(Vector(center)) @ Matrix.Rotation(math.radians(rot_z), 4, "Z")
    made = {v: bm.verts.new(mat @ v.co) for v in tmp.verts}
    for f in tmp.faces:
        bm.faces.new([made[v] for v in f.verts])
    tmp.free()
    return bm


def cyl_bm(bm, radius, p0, p1, sides=8):
    """Cylindre facette ferme entre les points p0 et p1."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = (p1 - p0).normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(axis.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    u = axis.cross(ref).normalized()
    w = axis.cross(u)
    rings = [[bm.verts.new(p + radius * (math.cos(t) * u + math.sin(t) * w))
              for t in (math.radians(22.5) + 2.0 * math.pi * i / sides for i in range(sides))]
             for p in (p0, p1)]
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    bm.faces.new(rings[1])
    bm.faces.new(list(reversed(rings[0])))
    return bm


def arch_pts(rx, rz, zc, z0, n=7):
    """Profil d'arche (x, z) : jambage gauche, arc elliptique en n segments, jambage droit."""
    pts = [(-rx, z0)]
    pts += [(rx * math.cos(math.pi - math.pi * k / n), zc + rz * math.sin(math.pi * k / n))
            for k in range(n + 1)]
    pts.append((rx, z0))
    return pts


def prism_y_bm(bm, pts, y0, y1):
    """Prisme ferme : polygone (x, z) extrude de y0 a y1."""
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    return bm


def boolean_cut(bm, cutter):
    """Retourne un nouveau bmesh = bm - cutter (les deux sont liberes)."""
    scene = bpy.context.scene
    objs = []
    for name, src in (("__lw_cut_a", bm), ("__lw_cut_b", cutter)):
        bmesh.ops.recalc_face_normals(src, faces=src.faces)
        me = bpy.data.meshes.new(name)
        src.to_mesh(me)
        src.free()
        ob = bpy.data.objects.new(name, me)
        scene.collection.objects.link(ob)
        objs.append(ob)
    mod = objs[0].modifiers.new("cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = objs[1]
    try:
        mod.solver = "EXACT"
    except TypeError:
        pass
    bpy.context.view_layer.update()
    ev = objs[0].evaluated_get(bpy.context.evaluated_depsgraph_get())
    out = bmesh.new()
    out.from_mesh(ev.to_mesh())
    ev.to_mesh_clear()
    for ob in objs:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
    return out


def tri_ngons(bm):
    """Triangule les faces de plus de 4 cotes (decoupe deterministe avant export)."""
    faces = [f for f in bm.faces if len(f.verts) > 4]
    if faces:
        bmesh.ops.triangulate(bm, faces=faces)
    return bm


# ------------------------------------------------------------ FRG_Furnace
FURN_CY = 0.3                       # corps et hotte recules : le socle forme un seuil devant
FURN_BASE = [(0.0, 4.0, 3.8), (0.86, 4.0, 3.8), (1.0, 3.86, 3.66)]
# corps : fut legerement fruite puis corniche
FURN_BODY = [(0.9, 3.6, 3.2), (4.9, 3.45, 3.05), (5.0, 3.7, 3.3), (5.5, 3.7, 3.3),
             (5.6, 3.6, 3.2)]
FURN_MOUTH = (2.0, 1.3, 2.5)        # demi-largeur, fleche de l'arc, z des naissances
FURN_MOUTH_BACK = -1.5              # fond de la bouche (derriere Glow)
FURN_GLOW_Y = (-1.8, -1.6)       # bouche peu profonde : lueur visible meme en vue plongeante
FURN_HOOD = [(5.5, 3.3, 2.9), (5.95, 3.3, 2.9), (8.1, 1.15, 1.15), (9.5, 1.15, 1.15),
             (9.6, 1.4, 1.4), (9.9, 1.4, 1.4), (10.0, 1.3, 1.3)]
# braises : (centre, echelle, rotation z en degres)
FURN_EMBERS = [((-0.95, -2.3, 1.12), (0.55, 0.42, 0.40), 20.0),
               ((0.15, -2.15, 1.20), (0.70, 0.46, 0.52), -35.0),
               ((1.05, -2.4, 1.10), (0.46, 0.38, 0.34), 60.0)]


def build_frg_furnace():
    """Fourneau : Base (pierre), Body (brique, bouche en arche), Hood, Glow, Embers."""
    asset = "FRG_Furnace"
    coll = lw.reset_collection(asset)
    rx, rz, zc = FURN_MOUTH

    base = loft_chamfer_z_bm(bmesh.new(), FURN_BASE, chamfer=0.14)

    body = loft_chamfer_z_bm(bmesh.new(), FURN_BODY, chamfer=0.14, cy=FURN_CY)
    cutter = prism_y_bm(bmesh.new(), arch_pts(rx, rz, zc, 0.5), -6.0, FURN_MOUTH_BACK)
    body = boolean_cut(body, cutter)
    tri_ngons(body)
    # claveaux en relief autour de la bouche, clef d'arche plus saillante
    inner = arch_pts(rx - 0.08, rz - 0.08, zc, 0.9)
    outer = arch_pts(rx + 0.6, rz + 0.6, zc, 0.9)
    nseg = len(inner) - 1
    for i in range(nseg):
        key = i == nseg // 2
        jamb = i in (0, nseg - 1)
        depth = 0.45 if key else (0.3 if (jamb or i % 2 == 0) else 0.18)
        o0, o1 = outer[i], outer[i + 1]
        if key:
            o0, o1 = (o0[0] * 1.08, o0[1] + 0.3), (o1[0] * 1.08, o1[1] + 0.3)
        # fonds decales : pas de sommets communs entre claveaux voisins (iles fermees)
        back = -2.4 if key else (-2.6 if i % 2 == 0 else -2.5)
        prism_y_bm(body, [inner[i], inner[i + 1], o1, o0], FURN_CY - 3.2 - depth, back)

    hood = loft_chamfer_z_bm(bmesh.new(), FURN_HOOD, chamfer=0.14, cy=FURN_CY)

    glow = prism_y_bm(bmesh.new(), arch_pts(rx + 0.1, rz + 0.1, zc, 0.9), *FURN_GLOW_Y)
    tri_ngons(glow)

    embers = bmesh.new()
    for center, scale, rot in FURN_EMBERS:
        res = bmesh.ops.create_icosphere(embers, subdivisions=1, radius=1.0)
        mat = (Matrix.Translation(Vector(center)) @ Matrix.Rotation(math.radians(rot), 4, "Z")
               @ Matrix.Diagonal(Vector((scale[0], scale[1], scale[2], 1.0))))
        for v in res["verts"]:
            v.co = mat @ v.co

    lw.add_object(asset, "Base", base, coll, STONE)
    lw.add_object(asset, "Body", body, coll, BRICK)
    lw.add_object(asset, "Hood", hood, coll, HOOD_METAL)
    lw.add_object(asset, "Glow", glow, coll, GLOW)
    lw.add_object(asset, "Embers", embers, coll, EMBER)
    return finish(asset, [
        {"object": "Base", "color": STONE, "material": "Slate", "canCollide": True,
         "role": "fixed", "notes": "Socle de pierre 8 x 7,6 x 1 ; son dessus (Y Roblox = 1,0) est "
                                   "la sole de la bouche. Origine au sol, centre."},
        {"object": "Body", "color": BRICK, "material": "Brick", "canCollide": True,
         "role": "fixed", "notes": "Corps en briques, bouche en arche (4 x 2,8) face a -Z Roblox, "
                                   "claveaux en relief. Origine au sol, centre du socle."},
        {"object": "Hood", "color": HOOD_METAL, "material": "Metal", "canCollide": True,
         "role": "fixed", "notes": "Hotte et cheminee, sommet a Y Roblox = 10. Origine au sol."},
        {"object": "Glow", "color": GLOW, "material": "Neon", "canCollide": False,
         "role": "fixed", "notes": "Dalle (epaisseur 0,2) au fond de la bouche, face avant a "
                                   "Z Roblox = -1,8, normale vers l'avant. A rendre lumineux "
                                   "(PointLight orange). Origine au sol, centre du socle."},
        {"object": "Embers", "color": EMBER, "material": "Neon", "canCollide": False,
         "role": "fixed", "notes": "3 braises posees sur la sole, dans la bouche. Origine au sol."},
    ])


# ---------------------------------------------------------- FRG_Workbench
BENCH_TOP_Z = 3.5                   # dessus du plateau = z de DisplayPoint
BENCH_TOP = [(3.0, 3.88, 1.88), (3.12, 4.0, 2.0), (3.38, 4.0, 2.0), (BENCH_TOP_Z, 3.88, 1.88)]
BENCH_LEG = (3.25, 1.4)             # |x|, |y| des pieds
BENCH_VISE = (3.0, -1.2)            # centre de l'etau (coin avant droit)


def _grow(bm, start, pivot, scale, shift=(0.0, 0.0, 0.0)):
    """Grossit (proportions chunky) les sommets ajoutes depuis l'indice `start` autour de `pivot`."""
    pivot, shift = Vector(pivot), Vector(shift)
    for v in list(bm.verts)[start:]:
        d = v.co - pivot
        v.co = pivot + Vector((d.x * scale[0], d.y * scale[1], d.z * scale[2])) + shift


def build_frg_workbench():
    """Etabli : Top, Legs, Vise (coin avant droit), Props (laiton), Props_Steel, DisplayPoint."""
    asset = "FRG_Workbench"
    coll = lw.reset_collection(asset)
    tz = BENCH_TOP_Z

    top = loft_chamfer_z_bm(bmesh.new(), BENCH_TOP, chamfer=0.12)

    legs = bmesh.new()
    lx, ly = BENCH_LEG
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):                       # pieds, enfonces de 0,2 dans le plateau
            block_bm(legs, (0.7, 0.7, 3.2), (sx * lx, sy * ly, 1.6), bevel=0.1)
        block_bm(legs, (0.3, 2.3, 0.45), (sx * lx, 0.0, 0.95))            # traverses laterales
    for sy in (-1.0, 1.0):
        block_bm(legs, (6.0, 0.3, 0.45), (0.0, sy * ly, 0.95))            # traverses longues
        block_bm(legs, (6.0, 0.24, 0.5), (0.0, sy * (ly + 0.1), 2.8))     # ceintures

    # etau : semelle, glissiere, mors fixe (arriere), mors mobile (avant), vis et broche
    vise = bmesh.new()
    vx, vy = BENCH_VISE
    block_bm(vise, (1.2, 1.3, 0.3), (vx, vy, tz + 0.1), bevel=0.08)
    block_bm(vise, (0.44, 1.5, 0.24), (vx, vy - 0.2, tz + 0.36), bevel=0.06)
    block_bm(vise, (1.0, 0.34, 0.62), (vx, vy + 0.33, tz + 0.5), bevel=0.08)
    block_bm(vise, (1.0, 0.34, 0.62), (vx, vy - 0.4, tz + 0.5), bevel=0.08)
    cyl_bm(vise, 0.11, (vx, vy - 0.5, tz + 0.5), (vx, vy - 1.1, tz + 0.5))
    block_bm(vise, (0.26, 0.2, 0.26), (vx, vy - 1.1, tz + 0.5), bevel=0.05)
    cyl_bm(vise, 0.06, (vx - 0.1, vy - 1.1, tz + 0.2), (vx + 0.1, vy - 1.1, tz + 0.8), sides=6)
    _grow(vise, 0, (vx, vy, tz), (1.5, 1.5, 1.2), shift=(-0.05, 0.35, -0.01))

    brass = bmesh.new()
    steel = bmesh.new()
    # serrure en cours (cadenas a plat) : corps laiton, anse et entree de cle acier
    px, py = -2.8, 0.25
    nb, ns = len(brass.verts), len(steel.verts)
    block_bm(brass, (0.95, 0.85, 0.36), (px, py, tz + 0.16), bevel=0.08)
    for sx in (-1.0, 1.0):
        block_bm(steel, (0.17, 0.75, 0.17), (px + sx * 0.28, py + 0.62, tz + 0.17))
    block_bm(steel, (0.73, 0.17, 0.17), (px, py + 1.06, tz + 0.17), bevel=0.04)
    cyl_bm(steel, 0.15, (px, py - 0.05, tz + 0.2), (px, py - 0.05, tz + 0.4))
    _grow(brass, nb, (px, py, tz), (1.35, 1.35, 1.5), shift=(0.0, 0.0, -0.03))
    _grow(steel, ns, (px, py, tz), (1.35, 1.35, 1.5), shift=(0.0, 0.0, -0.03))
    # boite de goupilles : boite laiton, 4 goupilles acier debout
    bx, by = -2.65, -1.2
    nb, ns = len(brass.verts), len(steel.verts)
    block_bm(brass, (1.1, 0.62, 0.3), (bx, by, tz + 0.13), bevel=0.06, rot_z=-12.0)
    rot = Matrix.Rotation(math.radians(-12.0), 4, "Z")
    for k in range(4):
        p = rot @ Vector((-0.36 + 0.24 * k, 0.0, 0.0))
        cyl_bm(steel, 0.075, (bx + p.x, by + p.y, tz + 0.15), (bx + p.x, by + p.y, tz + 0.5),
               sides=6)
    _grow(brass, nb, (bx, by, tz), (1.5, 1.5, 1.5), shift=(0.0, 0.0, -0.03))
    _grow(steel, ns, (bx, by, tz), (1.5, 1.5, 1.5), shift=(0.0, 0.0, -0.03))
    # pince a plat (coin arriere droit) : deux branches croisees + axe
    qx, qy = 2.7, 1.2
    ns = len(steel.verts)
    for ang in (11.0, -11.0):
        block_bm(steel, (1.5, 0.15, 0.13), (qx, qy, tz + (0.055 if ang > 0 else 0.11)),
                 rot_z=ang)
    cyl_bm(steel, 0.13, (qx, qy, tz - 0.02), (qx, qy, tz + 0.24))
    _grow(steel, ns, (qx, qy, tz), (1.5, 1.5, 1.5))

    lw.add_object(asset, "Top", top, coll, WOOD)
    lw.add_object(asset, "Legs", legs, coll, WOOD_DARK)
    lw.add_object(asset, "Vise", vise, coll, IRON)
    lw.add_object(asset, "Props", brass, coll, BRASS)
    lw.add_object(asset, "Props_Steel", steel, coll, IRON)
    lw.add_marker(asset, "DisplayPoint", coll, (0.0, 0.0, tz))
    return finish(asset, [
        {"object": "Top", "color": WOOD, "material": "WoodPlanks", "canCollide": True,
         "role": "fixed", "notes": "Plateau 8 x 4, epaisseur 0,5, dessus a Y Roblox = 3,5. "
                                   "Origine au sol, centre."},
        {"object": "Legs", "color": WOOD_DARK, "material": "Wood", "canCollide": True,
         "role": "fixed", "notes": "4 pieds, traverses basses et ceintures. Origine au sol."},
        {"object": "Vise", "color": IRON, "material": "Metal", "canCollide": False,
         "role": "fixed", "notes": "Etau au coin avant droit dans Blender (+X, -Y), donc cote "
                                   "-X Roblox, bord avant (-Z). Origine au sol, centre."},
        {"object": "Props", "color": BRASS, "material": "Metal", "canCollide": False,
         "role": "fixed", "notes": "Laiton : corps du cadenas en cours, boite de goupilles. "
                                   "Origine au sol, centre."},
        {"object": "Props_Steel", "color": IRON, "material": "Metal", "canCollide": False,
         "role": "fixed", "notes": "Acier : anse et entree de cle du cadenas, goupilles, pince. "
                                   "Origine au sol, centre."},
        {"object": "DisplayPoint", "color": lw.MARKER_COLOR, "material": "SmoothPlastic",
         "canCollide": False, "role": "marker",
         "notes": "Centre du plateau, exactement sur le dessus : (0, 3.5, 0) Roblox. Zone libre "
                  "3,1 x 3,7 centrée sur le repère."},
    ])
