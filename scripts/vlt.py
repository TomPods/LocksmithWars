"""Locksmith Wars - categorie VLT (coffres a voler : Lvl1 bois cercle, Lvl2 coffre-fort, Lvl3 chambre forte).

Contrat commun (voir docs/CONTEXTE_PROJET.md) :
- racine : Body, pieces fixes (Bands, Corners...), Interior, reperes LockSocket, BeaconPoint, GoldPoint ;
- groupe DoorAssembly (Empty a l'identite + collection enfant) : Door et tout ce qui bouge avec la porte ;
- le jeu fait pivoter DoorAssembly autour du bord -X Roblox de sa boite englobante = bord +X Blender :
  charnieres cote +X Blender, rien de DoorAssembly ne depasse l'emprise X de Door ;
- zone libre de 2,6 x 2,6 autour de LockSocket : face de porte plane, aucun relief.
Noms de pieces communs aux trois niveaux : Body, Bands, Corners, Interior, DoorAssembly, Door,
DoorFrame, DoorStuds, Handle.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import frg
import lw_common as lw

CATEGORY = "VLT"
WOOD = "#8B5A2B"
IRON = "#5A5F66"
CORNER = "#3B3F45"
DOOR_STEEL = "#737A84"      # tole striee : acier froid un ton plus clair que les cerclages
BRASS = "#C9A14A"
DARK = "#2A2A2A"

LOCK_HEIGHT = 3.5           # contrat : serrure toujours a 3,5 studs du sol
LOCK_ZONE = 1.3             # demi-cote de la zone libre autour de LockSocket
GAP = 0.02                  # decollement Interior / parois du Body (anti z-fighting)
GROUP = "DoorAssembly"


# ------------------------------------------------------- briques communes
def door_group(asset, coll):
    """Collection enfant <asset>.DoorAssembly + Empty DoorAssembly a l'identite."""
    sub = lw.reset_collection(asset + "." + GROUP, parent=coll)
    return sub, lw.add_group(asset, GROUP, sub)


def cut_cavity(body, hx, z0, z1, y_front, y_back):
    """Perce le Body : ouverture 2*hx x (z1 - z0) en facade, cavite jusqu'a y_back.

    Les cotes donnees sont celles de la surface visible (Interior) ; le Body est perce GAP plus large.
    """
    cutter = lw.box_bm((2.0 * (hx + GAP), y_back + GAP - (y_front - 2.0), z1 - z0 + 2.0 * GAP),
                       (0.0, (y_back + GAP + y_front - 2.0) / 2.0, (z0 + z1) / 2.0))
    return frg.tri_ngons(frg.boolean_cut(body, cutter))


def interior_bm(hx, z0, z1, y_front, y_back):
    """Parois interieures de la cavite (sol, plafond, cotes, fond), ouvertes vers l'avant.

    A creer avec lw.add_object(..., flip=True) : normales vers l'interieur de la cavite.
    """
    bm = bmesh.new()
    yf = y_front + GAP
    a = [bm.verts.new(p) for p in ((-hx, yf, z0), (hx, yf, z0), (hx, yf, z1), (-hx, yf, z1))]
    b = [bm.verts.new(p) for p in ((-hx, y_back, z0), (hx, y_back, z0), (hx, y_back, z1),
                                   (-hx, y_back, z1))]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(b)
    return bm


def hinge_fixed(bm, x, y, z, x_door, radius=0.15, height=0.7, leaf_h=0.5, leaf_t=0.1, y_wall=-2.5):
    """Partie FIXE d'une charniere (va dans une piece fixe) : noeud vertical + platine sur le corps.

    La platine part a 0,15 du bord de porte x_door et depasse le noeud de 0,1 ; le noeud est ecarte
    du bord de porte pour rester hors du balayage des reliefs de la porte quand elle s'ouvre.
    """
    frg.cyl_bm(bm, radius, (x, y, z - height / 2.0), (x, y, z + height / 2.0))
    x0, x1 = x_door + 0.15, x + radius + 0.1
    frg.block_bm(bm, (x1 - x0, leaf_t, leaf_h), ((x0 + x1) / 2.0, y_wall + GAP - leaf_t / 2.0, z))
    return bm


def stud_bm(bm, x, y, z, base=0.24, top=0.12, depth=0.08):
    """Rivet : tronc de pyramide pointant vers -Y, pose sur le plan y."""
    hb, ht = base / 2.0, top / 2.0
    a = [bm.verts.new((x + sx * hb, y, z + sz * hb)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    b = [bm.verts.new((x + sx * ht, y - depth, z + sz * ht))
         for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(b)
    bm.faces.new(list(reversed(a)))
    return bm


def vault_markers(asset, coll, lock, beacon, gold):
    lw.add_marker(asset, "LockSocket", coll, lock)
    lw.add_marker(asset, "BeaconPoint", coll, beacon)
    lw.add_marker(asset, "GoldPoint", coll, gold)


def marker_entries(lock, beacon, gold, gold_note):
    def rbx(p):
        return "(%g, %g, %g)" % (-p[0] + 0.0, p[2], p[1])
    base = {"color": lw.MARKER_COLOR, "material": "SmoothPlastic", "canCollide": False,
            "role": "marker"}
    return [
        dict(base, object="LockSocket",
             notes="Racine du coffre. %s Roblox : face avant de la porte, a 3,5 du sol. Zone libre "
                   "2,6 x 2,6 autour (face de porte plane, aucun relief)." % rbx(lock)),
        dict(base, object="BeaconPoint", notes="Racine du coffre. %s Roblox." % rbx(beacon)),
        dict(base, object="GoldPoint",
             notes="Racine du coffre. %s Roblox : sol de la cavite, centre en X. %s"
                   % (rbx(gold), gold_note)),
    ]


def group_entry():
    return {"object": GROUP, "color": "#000000", "material": "SmoothPlastic", "canCollide": False,
            "role": "moving",
            "notes": "GROUPE (noeud vide du FBX -> Model Roblox), pas une piece : ne lui appliquer ni "
                     "couleur ni materiau. A l'identite. Contient Door et les pieces mobiles ; "
                     "pivote autour de son bord -X Roblox (+X Blender)."}


def pose_door(asset, angle_deg=0.0, pivot_y=None):
    """Controle visuel : ouvre DoorAssembly de angle_deg autour de l'axe vertical de son bord +X.

    pivot_y None = milieu en Y de la boite englobante du groupe. angle 0 = retour a l'identite.
    """
    grp = bpy.data.objects[asset + "." + GROUP]
    grp.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()
    if not angle_deg:
        return None
    lo, hi = group_bounds(asset)
    pivot = Vector((hi.x, (lo.y + hi.y) / 2.0 if pivot_y is None else pivot_y, 0.0))
    grp.matrix_world = (Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(angle_deg), 4, "Z")
                        @ Matrix.Translation(-pivot))
    bpy.context.view_layer.update()
    return pivot


def swing_report(asset, lock, angles=(2, 5, 10, 15, 30, 45, 60, 75, 90, 100, 105, 110, 115),
                 lock_depth=0.7):
    """Controle du balayage : paires de faces qui se croisent entre DoorAssembly ouvert et le fixe.

    Reproduit TweenFX.animateDoor : axe vertical au bord +X Blender de la boite englobante de
    DoorAssembly, a mi-profondeur (Y) de cette boite. Deux cas : sans serrure, puis avec une
    serrure factice (2,6 x 2,6 x lock_depth devant LockSocket) qui epaissit la boite vers l'avant.
    Angle positif = ouverture vers l'avant (-Y). Remet la porte a l'identite. Retourne le total.
    """
    from mathutils.bvhtree import BVHTree

    def tree(bm, matrix):
        bm.transform(matrix)
        t = BVHTree.FromBMesh(bm, epsilon=0.0)
        bm.free()
        return t

    def mesh_bm(ob):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        return bm

    coll = bpy.data.collections[asset]
    grp = bpy.data.objects[asset + "." + GROUP]
    pose_door(asset, 0.0)
    fixed = [(ob["lw_part"], tree(mesh_bm(ob), ob.matrix_world))
             for ob in lw.meshes(coll.objects) if not ob.get("lw_marker")]
    lo, hi = group_bounds(asset)
    door = next(ob for ob in door_parts(asset) if ob["lw_part"] == "Door")
    dlo, _ = lw.world_bounds(door)
    print("%s : boite DoorAssembly y [%.3f, %.3f] ; saillie max devant la face de Door = %.3f, "
          "devant LockSocket = %.3f" % (asset, lo.y, hi.y, dlo.y - lo.y, lock[1] - lo.y))
    total = 0
    for label, depth in (("sans serrure", 0.0), ("serrure factice %.1f" % lock_depth, lock_depth)):
        y_min = min(lo.y, lock[1] - depth) if depth else lo.y
        py = (y_min + hi.y) / 2.0
        bad = {}
        for a in angles:
            pose_door(asset, a, py)
            movers = [(ob["lw_part"], tree(mesh_bm(ob), ob.matrix_world)) for ob in door_parts(asset)]
            if depth:
                box = lw.box_bm((2.0 * LOCK_ZONE, depth, 2.0 * LOCK_ZONE),
                                (lock[0], lock[1] - depth / 2.0, lock[2]))
                movers.append(("Serrure", tree(box, grp.matrix_world.copy())))
            for mn, mt in movers:
                for fn, ft in fixed:
                    n = len(mt.overlap(ft))
                    if n:
                        bad.setdefault(a, {})["%s/%s" % (mn, fn)] = n
                        total += n
        print("  %-20s pivot (x=%.3f, y=%.3f), %d angles de %d a %d : %s"
              % (label, hi.x, py, len(angles), angles[0], angles[-1], bad or "0 croisement"))
    pose_door(asset, 0.0)
    return total


def door_parts(asset):
    return lw.meshes(bpy.data.collections[asset + "." + GROUP].objects)


def group_bounds(asset):
    los, his = zip(*(lw.world_bounds(ob) for ob in door_parts(asset)))
    return (Vector([min(p[i] for p in los) for i in range(3)]),
            Vector([max(p[i] for p in his) for i in range(3)]))


def check_vault(asset, lock, round_door=None, eps=1e-5):
    """Preuves chiffrees du contrat ; leve AssertionError si une regle est violee.

    round_door = (cx, cz, rayon) pour une porte ronde (test « rien de fixe devant la porte »).
    """
    from mathutils.bvhtree import BVHTree
    bpy.context.view_layer.update()
    coll = bpy.data.collections[asset]
    grp = bpy.data.objects[asset + "." + GROUP]
    assert grp.matrix_world == Matrix.Identity(4), "DoorAssembly n'est pas a l'identite"
    moving = door_parts(asset)
    door = next(ob for ob in moving if ob["lw_part"] == "Door")
    dlo, dhi = lw.world_bounds(door)
    glo, ghi = group_bounds(asset)
    print("Door        x [%.3f, %.3f]  y [%.3f, %.3f]  z [%.3f, %.3f]"
          % (dlo.x, dhi.x, dlo.y, dhi.y, dlo.z, dhi.z))
    print("DoorAssembly x [%.3f, %.3f]  y [%.3f, %.3f]  z [%.3f, %.3f]"
          % (glo.x, ghi.x, glo.y, ghi.y, glo.z, ghi.z))
    for ob in moving:
        lo, hi = lw.world_bounds(ob)
        print("  %-10s x [%.3f, %.3f]  marge au bord +X de Door = %.3f, au bord -X = %.3f"
              % (ob["lw_part"], lo.x, hi.x, dhi.x - hi.x, lo.x - dlo.x))
        assert hi.x <= dhi.x + eps and lo.x >= dlo.x - eps, ob.name + " depasse la porte en X"
    # zone libre : aucune face de l'asset (hors reperes) devant le plan de LockSocket dans la zone
    x0, x1 = lock[0] - LOCK_ZONE, lock[0] + LOCK_ZONE
    z0, z1 = lock[2] - LOCK_ZONE, lock[2] + LOCK_ZONE
    hits = 0
    nearest = 1e9
    for ob in lw.meshes(coll.all_objects):
        if ob.get("lw_marker"):
            continue
        for poly in ob.data.polygons:
            pts = [ob.matrix_world @ ob.data.vertices[i].co for i in poly.vertices]
            if min(p.y for p in pts) >= lock[1] - eps:
                continue                                  # sur le plan de pose ou derriere
            fx0, fx1 = min(p.x for p in pts), max(p.x for p in pts)
            fz0, fz1 = min(p.z for p in pts), max(p.z for p in pts)
            dx = max(x0 - fx1, fx0 - x1, 0.0)
            dz = max(z0 - fz1, fz0 - z1, 0.0)
            nearest = min(nearest, max(dx, dz))
            if dx <= eps and dz <= eps:
                hits += 1
    print("Zone libre x [%.2f, %.2f] z [%.2f, %.2f] : %d face(s) en avant de y = %.2f dedans ; "
          "relief le plus proche a %.3f du bord de la zone" % (x0, x1, z0, z1, hits, lock[1], nearest))
    assert hits == 0, "relief dans la zone libre"
    # surface de pose : un rayon tire de l'avant doit toucher DoorAssembly exactement a y = lock y
    bm = bmesh.new()
    for ob in moving:
        tmp = ob.data.copy()
        tmp.transform(ob.matrix_world)
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    zs1 = min(z1, dhi.z)                                  # la zone peut depasser le haut de la porte
    n, miss, worst, m = 27, 0, 0.0, 1e-3
    for i in range(n):
        for j in range(n):
            x = x0 + m + (x1 - x0 - 2 * m) * i / (n - 1)      # m : retrait des bords
            z = z0 + m + (zs1 - z0 - 2 * m) * j / (n - 1)
            hit = tree.ray_cast(Vector((x, lock[1] - 10.0, z)), Vector((0.0, 1.0, 0.0)))[0]
            if hit is None:
                miss += 1
            else:
                worst = max(worst, abs(hit.y - lock[1]))
    print("Surface de pose : %d rayons sur x [%.2f, %.2f] z [%.2f, %.2f] ; %d sans surface ; ecart "
          "max au plan y = %.2f : %.5f" % (n * n, x0, x1, z0, zs1, miss, lock[1], worst))
    assert miss == 0 and worst < 1e-4, "la zone libre n'est pas une surface plane au niveau de LockSocket"
    # rien de fixe devant la porte (emprise de Door, y < face arriere de Door)
    fixed_hits = 0
    for ob in lw.meshes(coll.objects):
        if ob.get("lw_marker"):
            continue
        for poly in ob.data.polygons:
            pts = [ob.matrix_world @ ob.data.vertices[i].co for i in poly.vertices]
            if min(p.y for p in pts) >= dhi.y - eps:
                continue
            if round_door is not None:
                cx, cz, rad = round_door
                c = sum(pts, Vector()) / len(pts)
                if min(math.hypot(p.x - cx, p.z - cz) for p in pts + [c]) < rad - 1e-3:
                    fixed_hits += 1
            elif (max(p.x for p in pts) > dlo.x + eps and min(p.x for p in pts) < dhi.x - eps
                    and max(p.z for p in pts) > dlo.z + eps and min(p.z for p in pts) < dhi.z - eps):
                fixed_hits += 1
    print("Pieces fixes devant la porte : %d face(s)" % fixed_hits)
    assert fixed_hits == 0, "piece fixe devant la porte"
    return True


def finish(asset, entries, lock, round_door=None):
    check_vault(asset, lock, round_door)
    lw.update_manifest(asset, entries)
    path = lw.export_asset(asset, CATEGORY)
    lw.report(asset)
    lw.save_blend()
    return path


# ------------------------------------------------ primitives rondes (Lvl2, Lvl3)
def annulus_y_bm(bm, cx, cz, r_in, r_out, y_front, y_back, segs=24, phase=-90.0, chamfer=0.0,
                 only=None):
    """Anneau d'axe Y (section rectangulaire, aretes avant chanfreinees si chamfer > 0).

    only = indices de segments : chaque segment devient un coin ferme independant (bandes alternees).
    """
    c = chamfer
    prof = [(r_in, y_back), (r_in, y_front + c)]
    if c:
        prof += [(r_in + c, y_front), (r_out - c, y_front)]
    prof += [(r_out, y_front + c), (r_out, y_back)]
    n = len(prof)

    def ring(i):
        t = math.radians(phase + 360.0 * i / segs)
        return [bm.verts.new((cx + r * math.cos(t), y, cz + r * math.sin(t))) for r, y in prof]

    def skin(a, b):
        for k in range(n):
            m = (k + 1) % n
            bm.faces.new((a[k], a[m], b[m], b[k]))

    if only is None:
        rings = [ring(i) for i in range(segs)]
        for i in range(segs):
            skin(rings[i], rings[(i + 1) % segs])
    else:
        for i in only:
            a, b = ring(i), ring(i + 1)
            skin(a, b)
            bm.faces.new(a)
            bm.faces.new(list(reversed(b)))
    return bm


def round_profile(cz, r, floor, segs=24, phase=-90.0):
    """Profil (x, z) d'une ouverture ronde a seuil plat : cercle facette coupe a z = floor."""
    pts = [(r * math.cos(t), cz + r * math.sin(t))
           for t in (math.radians(phase + 360.0 * i / segs) for i in range(segs))]
    out = []
    for i, p in enumerate(pts):
        q = pts[(i + 1) % segs]
        if p[1] >= floor:
            out.append(p)
        if (p[1] >= floor) != (q[1] >= floor):
            t = (floor - p[1]) / (q[1] - p[1])
            out.append((p[0] + t * (q[0] - p[0]), floor))
    return out


def cut_cavity_profile(body, pts, y_front, y_back):
    """Perce le Body selon un profil (x, z) quelconque, de la facade jusqu'a y_back."""
    cutter = frg.prism_y_bm(bmesh.new(), pts, y_front - 2.0, y_back)
    return frg.tri_ngons(frg.boolean_cut(body, cutter))


def interior_profile_bm(pts, y_front, y_back):
    """Parois interieures d'une cavite de profil (x, z) quelconque (add_object(..., flip=True))."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y_front + GAP, z)) for x, z in pts]
    b = [bm.verts.new((x, y_back, z)) for x, z in pts]
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(b)
    return frg.tri_ngons(bm)


def wheel_bm(cx, cz, y_face, hub_r, hub_y, rim_r, rim_w, rim_y, spokes, spoke_w, grip_r=0.0,
             grip_span=(0.0, 0.0), segs=12, phase=90.0, flange=None, grip_sides=6):
    """Volant d'axe Y pose sur la face y_face. Retourne (volant, poignees) en deux bmesh.

    hub_y = y avant du moyeu ; rim_y = (y avant, y arriere) du cercle ; grip_span = (r debut, r fin)
    des poignees dans le prolongement des branches ; flange = (rayon, epaisseur) d'une embase.
    """
    wheel, grips = bmesh.new(), bmesh.new()
    frg.cyl_bm(wheel, hub_r, (cx, y_face + GAP, cz), (cx, hub_y, cz))
    if flange:
        frg.cyl_bm(wheel, flange[0], (cx, y_face + GAP, cz), (cx, y_face - flange[1], cz), sides=12)
    annulus_y_bm(wheel, cx, cz, rim_r - rim_w, rim_r, rim_y[0], rim_y[1], segs=segs, phase=phase)
    ym = (rim_y[0] + rim_y[1]) / 2.0
    th = (rim_y[1] - rim_y[0]) * 0.8
    r0, r1 = hub_r * 0.6, rim_r - rim_w * 0.5
    for k in range(spokes):
        t = math.radians(phase + 360.0 * k / spokes)
        mat = (Matrix.Translation((cx, ym, cz)) @ Matrix.Rotation(-t, 4, "Y")
               @ Matrix.Translation(((r0 + r1) / 2.0, 0.0, 0.0)))
        res = bmesh.ops.create_cube(wheel, size=1.0)
        for v in res["verts"]:
            v.co = mat @ Vector((v.co.x * (r1 - r0), v.co.y * th, v.co.z * spoke_w))
        if grip_r:
            d = Vector((math.cos(t), 0.0, math.sin(t)))
            c = Vector((cx, ym, cz))
            frg.cyl_bm(grips, grip_r, c + d * grip_span[0], c + d * grip_span[1], sides=grip_sides)
    return wheel, grips


# --------------------------------------------------------------- VLT_Lvl1
L1_HALF = 2.5                                   # encombrement 5 x 5 x 5
L1_DOOR_C = (0.0, -2.7, 2.5)
L1_DOOR_S = (3.6, 0.4, 3.6)
L1_LOCK = (0.0, -2.9, LOCK_HEIGHT)
L1_BEACON = (0.0, 0.0, 5.1)
# cavite visible : demi-largeur, z bas, z haut, y fond (ouverture 3,1 x 3,1 < porte 3,6 x 3,6)
L1_CAVITY = (1.55, 0.95, 4.05, 1.5)
L1_GOLD = (0.0, -0.5, 0.95)                     # centre du sol de la cavite
L1_HINGE_Z = (1.5, 3.5)
L1_STUD_Z = (0.98, 2.5, 4.02)                   # rivets : hors des hauteurs de charniere
L1_HANDLE_HUB = (0.55, 1.7)                     # x, z du moyeu du levier (bande basse de la porte)
L1_HANDLE_TILT = -12.0                         # autour de +Y : pommeau (cote -X) vers le bas


def build_vlt_lvl1():
    """Coffre de debutant : caisse en bois cerclee d'acier, porte en tole striee, levier laiton."""
    asset = "VLT_Lvl1"
    coll = lw.reset_collection(asset)
    sub, grp = door_group(asset, coll)
    h = L1_HALF
    front = -h
    hx, cz0, cz1, cyb = L1_CAVITY
    dx, dy, dz = L1_DOOR_C
    sx, sy, sz = L1_DOOR_S
    face = dy - sy / 2.0                         # face avant de la porte (y = -2,9)
    x_hinge = dx + sx / 2.0                      # bord +X de la porte
    pivot = (x_hinge, dy, dz - sz / 2.0)         # origine des pieces mobiles : pied de l'axe de charniere

    # --- fixe
    body = frg.block_bm(bmesh.new(), (2 * h, 2 * h, 2 * h), (0.0, 0.0, h), bevel=0.12)
    body = cut_cavity(body, hx, cz0, cz1, front, cyb)
    interior = interior_bm(hx, cz0, cz1, front, cyb)

    bands = bmesh.new()
    frg.loft_chamfer_z_bm(bands, [(0.0, h + 0.1, h + 0.1), (0.37, h + 0.1, h + 0.1), (0.45, h, h)],
                          chamfer=0.14)                                       # plinthe
    frg.loft_chamfer_z_bm(bands, [(4.46, h, h), (4.54, h + 0.1, h + 0.1), (4.78, h + 0.1, h + 0.1),
                                  (4.86, h, h)], chamfer=0.14)                # cerclage haut
    for s in (-1.0, 1.0):                                                     # sangle en U par-dessus
        frg.block_bm(bands, (0.16, 0.8, 4.7), (s * h, 0.0, 2.65))
    frg.block_bm(bands, (2 * h + 0.16, 0.8, 0.16), (0.0, 0.0, 2 * h))
    for z in L1_HINGE_Z:                                                      # charnieres, partie fixe
        hinge_fixed(bands, x_hinge + 0.52, front - 0.12, z, x_hinge, y_wall=front)

    corners = bmesh.new()
    cs, ch, out = 0.8, 0.7, 0.15
    for ax in (-1.0, 1.0):
        for ay in (-1.0, 1.0):
            c = h + out - cs / 2.0
            frg.block_bm(corners, (cs, cs, ch), (ax * c, ay * c, ch / 2.0), bevel=0.1)
            frg.block_bm(corners, (cs, cs, ch), (ax * c, ay * c, 2 * h + 0.12 - ch / 2.0), bevel=0.1)

    # --- mobile (DoorAssembly)
    door = frg.loft_chamfer_z_bm(bmesh.new(), [(dz - sz / 2.0, sx / 2.0, sy / 2.0),
                                              (dz + sz / 2.0, sx / 2.0, sy / 2.0)],
                                 chamfer=0.08, cy=dy)

    frame = bmesh.new()                          # U de fer : montants dans les marges, traverse basse
    relief = 0.14
    fy = face - relief / 2.0 + GAP / 2.0
    ft = relief + GAP
    for s in (-1.0, 1.0):
        frg.block_bm(frame, (0.4, ft, sz - 0.1), (s * 1.55, fy, dz))
    frg.block_bm(frame, (2.7, ft, 0.4), (0.0, fy, dz - sz / 2.0 + 0.28))

    studs = bmesh.new()
    for s in (-1.0, 1.0):
        for z in L1_STUD_Z:
            stud_bm(studs, s * 1.55, face - relief, z)

    handle = bmesh.new()
    ux, uz = L1_HANDLE_HUB
    frg.cyl_bm(handle, 0.38, (ux, face + GAP, uz), (ux, face - 0.2, uz))            # moyeu
    frg.cyl_bm(handle, 0.17, (ux, face - 0.2, uz), (ux, face - 0.42, uz))           # bossage
    frg.block_bm(handle, (1.3, 0.18, 0.26), (ux - 0.6, face - 0.28, uz), bevel=0.05)  # levier
    ball = bmesh.ops.create_icosphere(handle, subdivisions=1, radius=0.22)           # pommeau
    for v in ball["verts"]:
        v.co += Vector((ux - 1.3, face - 0.3, uz))
    tilt = (Matrix.Translation((ux, 0.0, uz)) @ Matrix.Rotation(math.radians(L1_HANDLE_TILT), 4, "Y")
            @ Matrix.Translation((-ux, 0.0, -uz)))
    bmesh.ops.transform(handle, matrix=tilt, verts=handle.verts)

    for bm in (bands, door, handle):
        frg.tri_ngons(bm)
    lw.add_object(asset, "Body", body, coll, WOOD)
    lw.add_object(asset, "Bands", bands, coll, IRON)
    lw.add_object(asset, "Corners", corners, coll, CORNER)
    lw.add_object(asset, "Interior", interior, coll, DARK, flip=True)
    lw.add_object(asset, "Door", door, sub, DOOR_STEEL, origin=pivot, parent=grp)
    lw.add_object(asset, "DoorFrame", frame, sub, IRON, origin=pivot, parent=grp)
    lw.add_object(asset, "DoorStuds", studs, sub, BRASS, origin=pivot, parent=grp)
    lw.add_object(asset, "Handle", handle, sub, BRASS, origin=pivot, parent=grp)
    vault_markers(asset, coll, L1_LOCK, L1_BEACON, L1_GOLD)

    in_group = " Enfant du groupe DoorAssembly ; origine au pied de l'axe de charniere (%g, %g, %g) Roblox." \
               % (-pivot[0], pivot[2], pivot[1])
    return finish(asset, [
        {"object": "Body", "color": WOOD, "material": "WoodPlanks", "canCollide": True,
         "role": "fixed",
         "notes": "Caisse 5 x 5 x 5, base centree, face avant a Z Roblox = -2,5. Ouverture 3,14 x 3,14 "
                  "derriere la porte, cavite profonde de 4,0. Collision : utiliser une decomposition "
                  "fidele ou un pave 5 x 5 x 5 selon le besoin du jeu (la cavite est creuse)."},
        {"object": "Bands", "color": IRON, "material": "Metal", "canCollide": False,
         "role": "fixed",
         "notes": "Plinthe, cerclage haut, sangle en U (cotes + dessus) et partie fixe des deux "
                  "charnieres (cote -X Roblox). Depasse l'encombrement de 0,1 au plus. Origine au sol."},
        {"object": "Corners", "color": CORNER, "material": "Metal", "canCollide": False,
         "role": "fixed", "notes": "8 coins renforces, depassent de 0,15 (0,12 au-dessus). Origine au sol."},
        {"object": "Interior", "color": DARK, "material": "SmoothPlastic", "canCollide": False,
         "role": "fixed",
         "notes": "Parois de la cavite (sol, plafond, cotes, fond), normales vers l'interieur, a 0,02 "
                  "des faces du Body. Cavite visible 3,1 x 3,1 x 3,98 ; sol a Y Roblox = 0,95."},
        group_entry(),
        {"object": "Door", "color": DOOR_STEEL, "material": "DiamondPlate", "canCollide": True,
         "role": "moving",
         "notes": "Tole striee 3,6 x 3,6 x 0,4, face avant plane a Z Roblox = -2,9." + in_group},
        {"object": "DoorFrame", "color": IRON, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "U de fer en relief de 0,14 : deux montants dans les marges laterales et traverse "
                  "basse, hors zone libre." + in_group},
        {"object": "DoorStuds", "color": BRASS, "material": "Metal", "canCollide": False,
         "role": "moving", "notes": "6 rivets laiton sur les montants." + in_group},
        {"object": "Handle", "color": BRASS, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Levier a pommeau laiton dans la bande basse de la porte (sous la zone libre)."
                  + in_group},
    ] + marker_entries(L1_LOCK, L1_BEACON, L1_GOLD,
                       "Le tas d'or 2 x 2 x 0,6 tient dans la cavite (3,1 x 3,98 au sol, 3,1 de haut)."),
        L1_LOCK)


# --------------------------------------------------------------- VLT_Lvl2
GREEN = "#2F4A3A"
GREEN_DARK = "#1F2E26"
GREEN_DOOR = "#3A5A47"      # porte : vert un ton plus clair que le corps, pour qu'elle se detache

L2_HALF = 3.8                                   # encombrement 7,6 x 7,6 x 9
L2_TOP = 9.0
L2_DOOR_C = (0.0, -3.8, 4.6)
L2_DOOR_S = (5.0, 0.6, 6.6)
L2_LOCK = (0.0, -4.1, LOCK_HEIGHT)
L2_BEACON = (0.0, 0.0, 9.0)
L2_CAVITY = (2.1, 1.75, 7.45, 2.9)              # ouverture 4,2 x 5,7 < porte 5 x 6,6
L2_GOLD = (0.0, -0.3, 1.75)
L2_HINGE_Z = (2.6, 6.6)
L2_WHEEL = (0.0, 6.3)                           # x, z de l'axe du volant (au-dessus de la zone libre)


def build_vlt_lvl2():
    """Coffre-fort vert et laiton : socle, fut a panneaux, corniche, porte encadree, volant a poignees."""
    asset = "VLT_Lvl2"
    coll = lw.reset_collection(asset)
    sub, grp = door_group(asset, coll)
    h = L2_HALF
    hx, cz0, cz1, cyb = L2_CAVITY
    dx, dy, dz = L2_DOOR_C
    sx, sy, sz = L2_DOOR_S
    face = dy - sy / 2.0                         # face avant de la porte (y = -4,1)
    wall = dy + sy / 2.0                         # facade du fut = dos de la porte (y = -3,5)
    x_hinge = dx + sx / 2.0
    pivot = (x_hinge, dy, dz - sz / 2.0)
    sh, scy = 3.55, (wall + 3.55) / 2.0          # fut : x +-3,55 ; y de wall a +3,55
    shy = (3.55 - wall) / 2.0

    # --- fixe
    shaft = frg.loft_chamfer_z_bm(bmesh.new(), [(0.9, sh, shy), (8.3, sh, shy)], chamfer=0.15, cy=scy)
    body = cut_cavity(shaft, hx, cz0, cz1, wall, cyb)
    frg.loft_chamfer_z_bm(body, [(8.15, sh, sh), (8.38, h, h), (8.8, h, h), (L2_TOP, h - 0.2, h - 0.2)],
                          chamfer=0.15)                                       # corniche
    for s in (-1.0, 1.0):                                                     # panneaux en relief
        frg.block_bm(body, (0.24, 5.2, 5.4), (s * sh, scy, 4.6), bevel=0.1)
    frg.block_bm(body, (5.2, 0.24, 5.4), (0.0, 3.55, 4.6), bevel=0.1)
    frg.tri_ngons(body)
    interior = interior_bm(hx, cz0, cz1, wall, cyb)

    base = frg.loft_chamfer_z_bm(bmesh.new(), [(0.0, h, h), (0.8, h, h), (1.0, h - 0.18, h - 0.18)],
                                 chamfer=0.15)
    frg.tri_ngons(base)

    trim = bmesh.new()
    b0, b1 = sh + 0.05, sh + 0.11                # moulures laiton autour du fut (facade a y = -3,61)
    for z in (1.0, 7.94):
        frg.loft_chamfer_z_bm(trim, [(z, b0, shy + 0.05), (z + 0.06, b1, shy + 0.11),
                                     (z + 0.2, b1, shy + 0.11), (z + 0.26, b0, shy + 0.05)],
                              chamfer=0.15, cy=scy)
    for z in L2_HINGE_Z:                                                      # charnieres, partie fixe
        hinge_fixed(trim, x_hinge + 0.55, wall - 0.3, z, x_hinge, radius=0.22, height=1.0,
                    leaf_h=0.7, leaf_t=0.12, y_wall=wall)
    frg.block_bm(trim, (2.2, 0.14, 0.34), (0.0, -h - 0.03, 8.59), bevel=0.04)  # plaque sur la corniche
    frg.tri_ngons(trim)

    # --- mobile (DoorAssembly)
    door = frg.loft_chamfer_z_bm(bmesh.new(), [(dz - sz / 2.0, sx / 2.0, sy / 2.0),
                                              (dz + sz / 2.0, sx / 2.0, sy / 2.0)],
                                 chamfer=0.1, cy=dy)
    frg.tri_ngons(door)

    frame = bmesh.new()                          # cadre laiton + pentures cote charniere
    relief = 0.12
    fy = face - relief / 2.0 + GAP / 2.0
    ft = relief + GAP
    fw = 0.35
    for s in (-1.0, 1.0):
        frg.block_bm(frame, (fw, ft, sz), (s * (sx / 2.0 - fw / 2.0), fy, dz))
        frg.block_bm(frame, (sx - 0.5, ft, fw), (0.0, fy, dz + s * (sz / 2.0 - fw / 2.0)))
    for z in L2_HINGE_Z:
        frg.block_bm(frame, (0.75, ft + 0.04, 0.44), (x_hinge - fw - 0.375, fy - 0.02, z))

    ux, uz = L2_WHEEL
    wheel, grips = wheel_bm(ux, uz, face, hub_r=0.34, hub_y=face - 0.5, rim_r=1.15, rim_w=0.26,
                            rim_y=(face - 0.48, face - 0.28), spokes=4, spoke_w=0.22, grip_r=0.14,
                            grip_span=(1.1, 1.55), segs=12, phase=45.0, flange=(0.58, 0.14))
    for f in grips.faces:                        # poignees laiton fusionnees au volant
        wheel.faces.new([wheel.verts.new(v.co) for v in f.verts])
    grips.free()
    frg.tri_ngons(wheel)

    handle = bmesh.new()                         # poignee de tirage, marge laterale cote ouverture
    kx = -1.78
    frg.cyl_bm(handle, 0.12, (kx, face - 0.32, 2.85), (kx, face - 0.32, 4.35))
    for z in (3.1, 4.1):
        frg.block_bm(handle, (0.22, 0.36, 0.22), (kx, face - 0.16, z))
    frg.tri_ngons(handle)

    lw.add_object(asset, "Body", body, coll, GREEN)
    lw.add_object(asset, "Base", base, coll, GREEN_DARK)
    lw.add_object(asset, "Trim", trim, coll, BRASS)
    lw.add_object(asset, "Interior", interior, coll, DARK, flip=True)
    lw.add_object(asset, "Door", door, sub, GREEN_DOOR, origin=pivot, parent=grp)
    lw.add_object(asset, "DoorFrame", frame, sub, BRASS, origin=pivot, parent=grp)
    lw.add_object(asset, "Wheel", wheel, sub, BRASS, origin=(ux, face, uz), parent=grp)
    lw.add_object(asset, "Handle", handle, sub, BRASS, origin=pivot, parent=grp)
    vault_markers(asset, coll, L2_LOCK, L2_BEACON, L2_GOLD)

    in_group = " Enfant du groupe DoorAssembly ; origine au pied de l'axe de charniere (%g, %g, %g) Roblox." \
               % (-pivot[0], pivot[2], pivot[1])
    return finish(asset, [
        {"object": "Body", "color": GREEN, "material": "Metal", "canCollide": True, "role": "fixed",
         "notes": "Fut 7,1 x 7,05 (facade a Z Roblox = -3,5) + corniche 7,6 x 7,6, sommet a Y = 9. "
                  "Panneaux en relief sur les cotes et le dos. Ouverture 4,24 x 5,74 derriere la porte, "
                  "cavite creuse profonde de 6,4. Origine au sol, centre."},
        {"object": "Base", "color": GREEN_DARK, "material": "Metal", "canCollide": True,
         "role": "fixed", "notes": "Socle 7,6 x 7,6 x 1. Origine au sol, centre."},
        {"object": "Trim", "color": BRASS, "material": "Metal", "canCollide": False, "role": "fixed",
         "notes": "Laiton fixe : moulures basse et haute autour du fut, partie fixe des deux "
                  "charnieres (cote -X Roblox), plaque sur la corniche. Origine au sol, centre."},
        {"object": "Interior", "color": DARK, "material": "SmoothPlastic", "canCollide": False,
         "role": "fixed",
         "notes": "Parois de la cavite, normales vers l'interieur, a 0,02 du Body. Cavite visible "
                  "4,2 x 5,7 x 6,38 ; sol a Y Roblox = 1,75."},
        group_entry(),
        {"object": "Door", "color": GREEN_DOOR, "material": "Metal", "canCollide": True,
         "role": "moving",
         "notes": "Porte 5 x 6,6 x 0,6, face avant plane a Z Roblox = -4,1." + in_group},
        {"object": "DoorFrame", "color": BRASS, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Cadre laiton (relief 0,12) et deux pentures cote charniere, hors zone libre."
                  + in_group},
        {"object": "Wheel", "color": BRASS, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Volant a 4 branches et 4 poignees, entierement au-dessus de la zone libre. Enfant du "
                  "groupe DoorAssembly ; origine SUR SON AXE (%g, %g, %g) Roblox, axe de rotation = Z "
                  "Roblox." % (-ux, uz, face)},
        {"object": "Handle", "color": BRASS, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Poignee de tirage verticale dans la marge laterale opposee aux charnieres." + in_group},
    ] + marker_entries(L2_LOCK, L2_BEACON, L2_GOLD,
                       "Le tas d'or 3 x 3 x 1,2 tient dans la cavite (4,2 x 6,38 au sol, 5,7 de haut)."),
        L2_LOCK)


# --------------------------------------------------------------- VLT_Lvl3
GUNMETAL = "#3B3F45"
DOOR_GUN = "#4C525A"        # disque de porte : acier entre le gris canon du corps et les anneaux
STEEL_LIGHT = "#8A8F98"     # volant et boulons : acier clair
HAZ_YELLOW = "#F2C12E"
HAZ_BLACK = "#1E1E1E"

L3_HX, L3_HY, L3_TOP = 6.0, 4.0, 13.0           # encombrement 12 x 8 x 13
L3_DOOR = (0.0, 6.5, 4.5)                       # cx, cz, rayon du disque (diametre 9)
L3_DOOR_Y = (-5.0, -4.0)                        # face avant, dos du disque
L3_LOCK = (0.0, -5.25, LOCK_HEIGHT)             # 0,25 devant le disque : platine de serrure
L3_BEACON = (0.0, 0.0, 13.1)
L3_BORE = (4.1, 3.0, 3.0)                       # rayon de l'ouverture, z du seuil plat, y du fond
L3_GOLD = (0.0, -0.5, 3.0)
L3_HINGE_Z = (4.3, 8.7)
L3_SEGS = 24


def build_vlt_lvl3():
    """Chambre forte gris canon : porte ronde a anneaux, grand volant a 5 branches, bandes de danger."""
    asset = "VLT_Lvl3"
    coll = lw.reset_collection(asset)
    sub, grp = door_group(asset, coll)
    cx, cz, rad = L3_DOOR
    face, wall = L3_DOOR_Y
    bore_r, floor, cyb = L3_BORE
    plate = L3_LOCK[1]                           # plan de pose de la serrure (y = -5,25)
    x_hinge = cx + rad
    pivot = (x_hinge, (face + wall) / 2.0, cz - rad)
    sh = 5.7                                     # fut : x +-5,7 ; y de wall a +3,7
    scy, shy = (wall + 3.7) / 2.0, (3.7 - wall) / 2.0
    ecy, ehy = -0.06, 4.06                       # socle et corniche : y de -4,12 a +4,0

    # --- fixe
    shaft = frg.loft_chamfer_z_bm(bmesh.new(), [(0.8, sh, shy), (12.2, sh, shy)], chamfer=0.2, cy=scy)
    body = cut_cavity_profile(shaft, round_profile(cz, bore_r + GAP, floor - GAP, L3_SEGS),
                              wall, cyb + GAP)
    frg.loft_chamfer_z_bm(body, [(0.0, L3_HX, ehy), (0.75, L3_HX, ehy), (0.95, L3_HX - 0.2, ehy - 0.16)],
                          chamfer=0.2, cy=ecy)                                # socle
    frg.loft_chamfer_z_bm(body, [(12.05, sh, ehy - 0.16), (12.32, L3_HX, ehy), (12.78, L3_HX, ehy),
                                 (L3_TOP, L3_HX - 0.22, ehy - 0.2)], chamfer=0.2, cy=ecy)  # corniche
    frg.tri_ngons(body)
    interior = interior_profile_bm(round_profile(cz, bore_r, floor, L3_SEGS), wall, cyb)

    trim = bmesh.new()
    for sx in (-1.0, 1.0):                                                    # montants d'angle
        for y in (wall + 0.15, 3.7 - 0.15):
            frg.block_bm(trim, (0.6, 0.6, 11.2), (sx * 5.55, y, 6.5), bevel=0.12)
        for z in (4.0, 9.0):                                                  # nervures laterales
            frg.block_bm(trim, (0.3, 6.6, 0.6), (sx * sh, scy, z), bevel=0.1)
    for z in L3_HINGE_Z:                                                      # gonds, partie fixe
        frg.block_bm(trim, (1.25, 0.5, 1.5), (5.25, wall - 0.25, z), bevel=0.1)
        frg.cyl_bm(trim, 0.42, (5.4, -4.85, z - 0.75), (5.4, -4.85, z + 0.75))
        for s in (-1.0, 1.0):                                                 # chapeaux de gond
            frg.cyl_bm(trim, 0.52, (5.4, -4.85, z + s * 0.75), (5.4, -4.85, z + s * 0.93))
    frg.tri_ngons(trim)

    haz_y, haz_k = bmesh.new(), bmesh.new()      # bandes de danger autour de l'ouverture
    for bm, start in ((haz_y, 0), (haz_k, 1)):
        annulus_y_bm(bm, cx, cz, rad + 0.08, 5.2, wall - 0.1, wall + GAP, segs=L3_SEGS,
                     only=range(start, L3_SEGS, 2))
        frg.tri_ngons(bm)

    # --- mobile (DoorAssembly)
    door = frg.prism_y_bm(bmesh.new(),
                          [(cx + rad * math.cos(t), cz + rad * math.sin(t))
                           for t in (math.radians(-90.0 + 360.0 * i / L3_SEGS) for i in range(L3_SEGS))],
                          face, wall)
    frg.tri_ngons(door)

    frame = bmesh.new()                          # anneaux concentriques, platine de serrure, bras de gond
    ring_y = face - 0.2
    annulus_y_bm(frame, cx, cz, 3.8, rad, ring_y, face + GAP, segs=L3_SEGS, chamfer=0.1)
    annulus_y_bm(frame, cx, cz, 2.05, 2.65, ring_y, face + GAP, segs=L3_SEGS, chamfer=0.1)
    frg.block_bm(frame, (2.9, face + GAP - plate, 2.95),
                 (L3_LOCK[0], (face + GAP + plate) / 2.0, cz - rad + 1.475))
    for z in L3_HINGE_Z:
        frg.block_bm(frame, (1.9, 1.15, 0.7), (x_hinge - 0.95, -4.775, z), bevel=0.1)
    frg.tri_ngons(frame)

    studs = bmesh.new()                          # boulons sur l'anneau exterieur (hors platine)
    for k in range(12):
        t = math.radians(-75.0 + 30.0 * k)
        x, z = cx + 4.15 * math.cos(t), cz + 4.15 * math.sin(t)
        if abs(x) < 1.8 and z < 5.3:
            continue
        stud_bm(studs, x, ring_y, z, base=0.42, top=0.22, depth=0.14)

    wheel, grips = wheel_bm(cx, cz, face, hub_r=0.5, hub_y=face - 0.9, rim_r=1.5, rim_w=0.3,
                            rim_y=(face - 0.8, face - 0.55), spokes=5, spoke_w=0.26, grip_r=0.17,
                            grip_span=(1.42, 1.9), segs=20, phase=90.0, flange=(0.95, 0.25),
                            grip_sides=8)
    frg.tri_ngons(wheel)
    frg.tri_ngons(grips)

    lw.add_object(asset, "Body", body, coll, GUNMETAL)
    lw.add_object(asset, "Trim", trim, coll, IRON)
    lw.add_object(asset, "Hazard_Yellow", haz_y, coll, HAZ_YELLOW)
    lw.add_object(asset, "Hazard_Black", haz_k, coll, HAZ_BLACK)
    lw.add_object(asset, "Interior", interior, coll, DARK, flip=True)
    lw.add_object(asset, "Door", door, sub, DOOR_GUN, origin=pivot, parent=grp)
    lw.add_object(asset, "DoorFrame", frame, sub, IRON, origin=pivot, parent=grp)
    lw.add_object(asset, "DoorStuds", studs, sub, STEEL_LIGHT, origin=pivot, parent=grp)
    lw.add_object(asset, "Wheel", wheel, sub, STEEL_LIGHT, origin=(cx, face, cz), parent=grp)
    lw.add_object(asset, "WheelGrips", grips, sub, HAZ_YELLOW, origin=(cx, face, cz), parent=grp)
    vault_markers(asset, coll, L3_LOCK, L3_BEACON, L3_GOLD)

    in_group = " Enfant du groupe DoorAssembly ; origine au pied de la tangente de charniere (%g, %g, %g) Roblox." \
               % (-pivot[0], pivot[2], pivot[1])
    on_axis = " Enfant du groupe DoorAssembly ; origine SUR L'AXE du volant (%g, %g, %g) Roblox, axe de " \
              "rotation = Z Roblox." % (-cx, cz, face)
    return finish(asset, [
        {"object": "Body", "color": GUNMETAL, "material": "DiamondPlate", "canCollide": True,
         "role": "fixed",
         "notes": "Fut 11,4 x 7,7 (facade a Z Roblox = -4,0), socle et corniche 12 x 8,12 (debord avant "
                  "0,12), sommet a Y = 13. Ouverture ronde de rayon 4,12 centree a Y = 6,5, seuil plat "
                  "a Y = 2,98, cavite creuse profonde de 7. Origine au sol, centre."},
        {"object": "Trim", "color": IRON, "material": "Metal", "canCollide": False, "role": "fixed",
         "notes": "Acier fixe : 4 montants d'angle, nervures laterales, partie fixe des deux gonds "
                  "massifs (cote -X Roblox). Origine au sol, centre."},
        {"object": "Hazard_Yellow", "color": HAZ_YELLOW, "material": "SmoothPlastic",
         "canCollide": False, "role": "fixed",
         "notes": "12 segments jaunes de l'anneau de danger (rayon 4,58 a 5,2, relief 0,1) autour de "
                  "l'ouverture, alternes avec Hazard_Black. Origine au sol, centre."},
        {"object": "Hazard_Black", "color": HAZ_BLACK, "material": "SmoothPlastic",
         "canCollide": False, "role": "fixed",
         "notes": "12 segments noirs de l'anneau de danger. Origine au sol, centre."},
        {"object": "Interior", "color": DARK, "material": "SmoothPlastic", "canCollide": False,
         "role": "fixed",
         "notes": "Parois de la cavite (tunnel rond de rayon 4,1 a sol plat), normales vers "
                  "l'interieur, a 0,02 du Body. Sol a Y Roblox = 3,0, large de 4,2 ; profondeur 6,98."},
        group_entry(),
        {"object": "Door", "color": DOOR_GUN, "material": "Metal", "canCollide": True,
         "role": "moving",
         "notes": "Disque de diametre 9 (24 cotes), epaisseur 1, face avant a Z Roblox = -5,0." + in_group},
        {"object": "DoorFrame", "color": IRON, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Deux anneaux concentriques (relief 0,2), platine de serrure 2,9 x 2,95 dont la face "
                  "avant plane est a Z Roblox = -5,25 (plan de LockSocket, couvre toute la zone libre), "
                  "deux bras de gond cote charniere." + in_group},
        {"object": "DoorStuds", "color": STEEL_LIGHT, "material": "Metal", "canCollide": False,
         "role": "moving", "notes": "Boulons acier clair sur l'anneau exterieur." + in_group},
        {"object": "Wheel", "color": STEEL_LIGHT, "material": "Metal", "canCollide": False,
         "role": "moving",
         "notes": "Grand volant a 5 branches au centre de la porte, au-dessus de la zone libre." + on_axis},
        {"object": "WheelGrips", "color": HAZ_YELLOW, "material": "SmoothPlastic", "canCollide": False,
         "role": "moving", "notes": "5 poignees jaunes du volant (tournent avec Wheel)." + on_axis},
    ] + marker_entries(L3_LOCK, L3_BEACON, L3_GOLD,
                       "Le tas d'or 4 x 4 x 2 tient dans la cavite (sol 4,2 x 6,98, tunnel de rayon 4,1)."),
        L3_LOCK, round_door=L3_DOOR)
