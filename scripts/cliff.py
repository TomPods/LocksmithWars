"""Locksmith Wars - lot 9, falaises de bordure de carte (ENV_Cliff_*).

Meme langage de formes que la roche d'ORE_F1 et les MIN_Rock_Deco (facettes
larges, plans francs, biseaux visibles, aucun bruit), a l'echelle d'un decor.

Construction : chaque strate est un solide extrude a partir d'anneaux de
contour (vue de dessus) poses a differentes hauteurs. Le contour avant est une
ligne brisee irreguliere (gros plans casses) ; les anneaux successifs reculent
(fruit de la paroi, 80-85 deg) et la strate suivante deborde legerement de la
precedente avec un biseau a 45 deg en sous-face : la paroi lit en strates
epaisses, sans aucune surface horizontale accessible (pas de corniche).
Le chapeau d'herbe est une dalle plate qui deborde de 0,35 a 0,5 stud.

Repere : face avant vers -Y, pivot = base centree (0, 0, 0) au sol.
Tout est parametrable (largeur, profondeur, hauteur, strates, graine) pour
decliner ENV_Cliff_B, ENV_Cliff_Corner, ENV_Cliff_Peak.
"""
import random

import bmesh
from mathutils import Vector

import lw_common as lw

CATEGORY = "ENV"
ROCK_COLOR = "#6E6A66"      # roche d'ORE_F1
STRATA_COLOR = "#8A847C"    # strates claires
GRASS_COLOR = "#7A9A4A"
GRASS_MATERIAL = "SmoothPlastic"   # Grass n'est pas dans la liste autorisee ; couleur unie
LIP = 0.6       # debord + biseau a 45 deg sous chaque strate (stud)
MARGIN = 0.15   # la strate superieure couvre toujours le dessus de la precedente


# ---------------------------------------------------------------- outils
def solid_from_rings(rings, bm=None):
    """Solide ferme a partir d'anneaux [(pts [(x, y, z)...]), ...] de meme taille.

    Faces laterales entre anneaux successifs, n-gones en bas et en haut,
    puis triangulation (resultat deterministe dans Roblox).
    """
    if bm is None:
        bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    m = len(rings[0])
    new_faces = []
    for lo, hi in zip(vs, vs[1:]):
        for i in range(m):
            j = (i + 1) % m
            new_faces.append(bm.faces.new((lo[i], lo[j], hi[j], hi[i])))
    new_faces.append(bm.faces.new(list(reversed(vs[0]))))
    new_faces.append(bm.faces.new(vs[-1]))
    bmesh.ops.triangulate(bm, faces=new_faces, quad_method="BEAUTY", ngon_method="BEAUTY")
    return bm


class Outline:
    """Contour de base d'un module, vu de dessus, parcouru dans le sens trigonometrique :
    points de facade (de l'extremite gauche a l'extremite droite, la roche a gauche du
    sens de parcours), flanc droit, points arriere, flanc gauche.

    Chaque point de facade porte : Q (position sur la ligne de reference), n (normale
    sortante, vers les joueurs ; NON normalisee a l'angle rentrant d'un coin, pour que
    le recul reste parallele aux deux pans) et t (tangente, sens de parcours).
    Position d'un point : Q + t * dx - n * (y_avant + dy), y_avant etant la distance
    (negative = vers les joueurs) a la ligne de reference, comme pour un pan droit.
    """

    def __init__(self, front, back, back_out, back_y, dip_axis, end_recess=1.6):
        self.front = front                  # [(Q, n, t), ...]
        self.n_front = len(front)
        self.back = back                    # [(x, y), ...]
        self.back_out = back_out            # direction sortante de chaque point arriere
        self.back_y = back_y                # profondeur de l'arriere derriere la reference
        self.dip_axis = dip_axis            # z += pendage * (p . dip_axis)
        self.end_recess = end_recess

    @classmethod
    def straight(cls, width, back_y, n_front, seed, end_recess=1.6, back_pts=3):
        """Pan droit (ENV_Cliff_A, ENV_Cliff_B) : facade le long de X, regardant -Y."""
        rng = random.Random(seed)
        half = width / 2.0
        step = width / (n_front - 1)
        xs = [-half + i * step + (rng.uniform(-0.3, 0.3) * step if 0 < i < n_front - 1 else 0.0)
              for i in range(n_front)]
        n, t = Vector((0.0, -1.0, 0.0)), Vector((1.0, 0.0, 0.0))
        front = [(Vector((x, 0.0, 0.0)), n, t) for x in xs]
        back = [(half - 1.0 - i * (width - 2.0) / (back_pts - 1), back_y) for i in range(back_pts)]
        return cls(front, back, [(0.0, 1.0)] * back_pts, back_y,
                   (1.0 / (2.0 * half), 0.0), end_recess)

    @classmethod
    def corner(cls, length, back_y, n_branch, seed, end_recess=1.6, gap=9.0):
        """Coin rentrant a 90 deg : branche 2 le long de Y (regarde +X), angle en (0, 0),
        branche 1 le long de X (regarde -Y). La roche occupe le L derriere les deux pans.
        Aucun point de facade a moins de `gap` de l'angle sur la ligne de reference : le
        pied avance de 6 a 7,5 studs, un point plus proche passerait de l'autre cote de
        l'angle (contour qui se recoupe)."""
        rng = random.Random(seed)
        step = (length - gap) / (n_branch - 1)
        front = []
        n2, t2 = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0))
        n1, t1 = Vector((0.0, -1.0, 0.0)), Vector((1.0, 0.0, 0.0))
        for i in range(n_branch):                       # branche 2, de (0, -L) vers l'angle
            j = rng.uniform(-0.25, 0.25) * step if 0 < i < n_branch - 1 else 0.0
            front.append((Vector((0.0, -length + i * step + j, 0.0)), n2, t2))
        front.append((Vector((0.0, 0.0, 0.0)), n1 + n2, Vector((0.0, 0.0, 0.0))))   # angle
        for i in range(n_branch):                       # branche 1, de l'angle vers (L, 0)
            j = rng.uniform(-0.25, 0.25) * step if 0 < i < n_branch - 1 else 0.0
            front.append((Vector((gap + i * step + j, 0.0, 0.0)), n1, t1))
        back = [(length - 1.0, back_y), (length * 0.35, back_y), (-back_y, back_y),
                (-back_y, -length * 0.35), (-back_y, -length + 1.0)]
        back_out = [(0.0, 1.0), (0.0, 1.0), (-1.0, 1.0), (-1.0, 0.0), (-1.0, 0.0)]
        return cls(front, back, back_out, back_y, (0.5 / length, 0.5 / length), end_recess)

    def end(self, right):
        return self.front[-1] if right else self.front[0]


def stratum_rings(plan, levels, seed, amp=1.2, ring_amp=0.25, x_amp=0.9, side_amp=1.0,
                  dip=0.0, dip_top=None, notch=1.9, bulge=1.3, end_amp=0.9):
    """Anneaux d'une strate.

    levels : [(z, y_avant_moyen), ...] du bas vers le haut.
    Un decalage de base par point (commun a la strate) donne les grands plans
    casses ; un petit ecart par anneau incline les facettes. `dip` incline les
    joints de strate (pendage, en stud d'un bord a l'autre) : le joint bas suit
    `dip`, le joint haut `dip_top`, les anneaux intermediaires interpolent.
    (Ordre des tirages aleatoires = celui d'ENV_Cliff_A valide : ne pas le changer.)
    """
    rng = random.Random(seed)
    if dip_top is None:
        dip_top = dip
    nf = plan.n_front
    base = [rng.uniform(-amp, amp) for _ in range(nf)]
    # un gros plan casse rentrant et un bombement par strate (jamais aux bords)
    inner = list(range(2, nf - 2))
    k_notch = rng.choice(inner)
    k_bulge = rng.choice([k for k in inner if abs(k - k_notch) > 1] or inner)
    base[k_notch] += notch
    base[k_bulge] -= bulge
    side = [rng.uniform(-side_amp, side_amp) for _ in range(2)]
    ends = [rng.uniform(-end_amp, end_amp * 0.4), rng.uniform(-end_amp * 0.4, end_amp)]
    ax, ay = plan.dip_axis
    z_lo, z_hi = levels[0][0], levels[-1][0]
    rings = []
    for z, yf in levels:
        tt = 0.0 if z_hi == z_lo else (z - z_lo) / (z_hi - z_lo)
        d = dip + (dip_top - dip) * tt

        def pt(p):
            return (p.x, p.y, z + d * (p.x * ax + p.y * ay))

        pts = []
        for i, (Q, n, t) in enumerate(plan.front):
            end = i in (0, nf - 1)
            if end:
                dx = ends[0 if i == 0 else 1] + rng.uniform(-0.2, 0.2)
            else:
                dx = rng.uniform(-x_amp, x_amp)
            dy = base[i] * (0.35 if end else 1.0) + rng.uniform(-ring_amp, ring_amp)
            if end:
                dy += plan.end_recess          # bords biseautes vers l'arriere
            pts.append(pt(Q + t * dx - n * (yf + dy)))
        mid = (yf + plan.back_y) * 0.5 - 0.5
        Q, n, t = plan.end(True)
        pts.append(pt(Q + t * (0.35 + side[0]) - n * mid))             # flanc droit
        for x, y in plan.back:
            pts.append(pt(Vector((x, y, 0.0))))
        Q, n, t = plan.end(False)
        pts.append(pt(Q + t * (side[1] - 0.35) - n * (mid + 0.4)))     # flanc gauche
        rings.append(pts)
    return rings


def lip_ring(plan, prev_top, z):
    """Anneau bas d'une strate : copie du dessus de la precedente, abaissee de -z.
    Pan droit : tout l'anneau avance de MARGIN vers -Y (ENV_Cliff_A valide).
    Autres contours : la facade avance de MARGIN le long de sa normale."""
    if plan.dip_axis[1] == 0.0:
        return [(x, y - MARGIN, pz + z) for (x, y, pz) in prev_top]
    out = []
    for k, (x, y, pz) in enumerate(prev_top):
        if k < plan.n_front:
            n = plan.front[k][1]
            out.append((x + n.x * MARGIN, y + n.y * MARGIN, pz + z))
        else:
            out.append((x, y, pz + z))
    return out


def grass_rings(plan, top_ring, z_top, seed, over=0.4, thick=0.9, inset=0.35):
    """Chapeau d'herbe : debord leger, bord inferieur irregulier, dessus plat."""
    rng = random.Random(seed)
    nf = plan.n_front
    m = len(top_ring)
    t_left = plan.end(False)[2]
    t_right = plan.end(True)[2]

    def offset(ring, o, z_of):
        res = []
        for k, (x, y, _z) in enumerate(ring):
            p = Vector((x, y, 0.0))
            if k < nf:
                p = p + plan.front[k][1] * o
                if k == 0:
                    p = p - t_left * o
                elif k == nf - 1:
                    p = p + t_right * o
            elif k == nf:
                p = p + t_right * o
            elif k == m - 1:
                p = p - t_left * o
            else:
                bx, by = plan.back_out[k - nf - 1]
                p = p + Vector((bx, by, 0.0)) * (o * 0.5)
            res.append((p.x, p.y, z_of(k)))
        return res

    drop = [rng.uniform(0.0, 0.7) if k < nf else 0.2 for k in range(m)]
    pz = [p[2] for p in top_ring]
    bottom = offset(top_ring, over - 0.25, lambda k: pz[k] - 0.5 - drop[k])
    edge = offset(top_ring, over, lambda k: min(pz[k] + 0.15, z_top - thick + 0.6) - drop[k] * 0.4)
    upper = offset(top_ring, over - 0.05, lambda k: z_top - 0.25)
    top = offset(top_ring, over - inset, lambda k: z_top)
    return [bottom, edge, upper, top]


def shoulder(bms, x0, x1, z_start, z_top, drop):
    """Epaulement : au-dessus de z_start, ecrase la falaise d'autant plus que x depasse x0
    (rien avant x0, `drop` studs en moins au sommet apres x1, rampe lineaire entre deux)."""
    for bm in bms:
        for v in bm.verts:
            if v.co.z <= z_start:
                continue
            f = min(1.0, max(0.0, (v.co.x - x0) / (x1 - x0)))
            k = 1.0 - f * drop / (z_top - z_start)
            v.co.z = z_start + (v.co.z - z_start) * k
    return bms


# ----------------------------------------------------------------- module
def build_cliff_module(asset, width=32.0, back_y=6.6, foot_y=-6.0, height=36.0,
                       strata=None, n_front=9, seed=901, end_recess=1.6, plan=None,
                       post=None):
    """Falaise a strates sur un contour `plan` (pan droit par defaut), parametrable.

    strata : liste de (z_haut, y_avant_haut, couleur, pendage_haut) du bas vers le
    haut ; la premiere strate porte le pied evase (y = foot_y au sol, joint plat).
    post : fonction(liste de bmesh) appliquee avant creation des objets (epaulement...).
    """
    if strata is None:
        strata = default_strata(height)
    coll = lw.reset_collection(asset)
    if plan is None:
        plan = Outline.straight(width, back_y, n_front, seed, end_recess=end_recess)
    groups = {ROCK_COLOR: None, STRATA_COLOR: None}
    prev_top = None
    prev_z = 0.0
    prev_y = foot_y
    prev_dip = 0.0
    nf = plan.n_front
    t_left, t_right = plan.end(False)[2], plan.end(True)[2]
    for s, (z1, y1, color, dip) in enumerate(strata):
        if s == 0:
            fy = foot_y + 1.8
            levels = [(0.0, foot_y), (2.6, fy)] + mids(2.6, fy, z1, y1) + [(z1, y1)]
            rings = stratum_rings(plan, levels, seed + 10 * s, dip=0.0, dip_top=dip)
        else:
            z0 = prev_z
            yb = prev_y - LIP                 # debord de la strate
            levels = [(z0 + LIP, yb)] + mids(z0 + LIP, yb, z1, y1) + [(z1, y1)]
            body = stratum_rings(plan, levels, seed + 10 * s, dip=prev_dip, dip_top=dip)
            rings = [lip_ring(plan, prev_top, -0.1)] + body
            # le pied du biseau ne doit jamais etre en retrait du dessus precedent
            # ni plus etroit sur les flancs (sinon petit biseau tourne vers le haut)
            m = len(rings[0])
            fixed = []
            for k, (x, y, z) in enumerate(rings[1]):
                x0, y0, _z0 = rings[0][k]
                p, p0 = Vector((x, y, 0.0)), Vector((x0, y0, 0.0))
                if k < nf:
                    n = plan.front[k][1]
                    adv = (p - p0).dot(n) / n.length_squared
                    if adv < LIP * 0.8:
                        p = p + n * (LIP * 0.8 - adv)
                out = None
                if k in (0, m - 1):
                    out = -t_left
                elif k in (nf - 1, nf):
                    out = t_right
                if out is not None:
                    cur = (p - p0).dot(out)
                    if cur < 0.3:
                        p = p + out * (0.3 - cur)
                fixed.append((p.x, p.y, z))
            rings[1] = fixed
        groups[color] = solid_from_rings(rings, groups[color])
        prev_top, prev_z, prev_y, prev_dip = rings[-1], z1, y1, dip
    grass = solid_from_rings(grass_rings(plan, prev_top, height, seed + 99))
    if post is not None:
        post([b for b in (groups[ROCK_COLOR], groups[STRATA_COLOR], grass) if b is not None])
    out = []
    for color, part in ((ROCK_COLOR, "Rock"), (STRATA_COLOR, "Strata")):
        if groups[color] is not None:
            out.append(lw.add_object(asset, part, groups[color], coll, color))
    out.append(lw.add_object(asset, "Grass", grass, coll, GRASS_COLOR))
    recenter(out)
    return coll, out


def mids(za, ya, zb, yb, bow=0.2):
    """Deux anneaux intermediaires (a 1/3 et 2/3), legerement bombes vers l'avant."""
    return [(za + (zb - za) * t, ya + (yb - ya) * t - bow) for t in (0.36, 0.7)]


def recenter(objs):
    """Pivot = base centree : recentre l'emprise XY commune de toutes les pieces sur l'origine."""
    pts = [v.co for ob in objs for v in ob.data.vertices]
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2.0
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2.0
    for ob in objs:
        for v in ob.data.vertices:
            v.co.x -= cx
            v.co.y -= cy
        ob.data.update()
    return cx, cy


def default_strata(height):
    """4 strates epaisses alternees (sombre / claire), fruit global ~84 deg."""
    k = height / 36.0
    return [
        (12.0 * k, -3.0, ROCK_COLOR, 1.2),
        (18.8 * k, -2.6, STRATA_COLOR, -0.9),
        (28.0 * k, -1.9, ROCK_COLOR, 0.8),
        (34.4 * k, -1.3, STRATA_COLOR, -0.4),
    ]


def manifest(asset, extra="", collide=True, grass_note=""):
    col = ("CollisionFidelity Hull ou Box conseille (murs invisibles poses par l'integrateur)."
           if collide else "Hors de portee des joueurs : aucune collision.")
    lw.update_manifest(asset, [
        {"object": "Rock", "color": ROCK_COLOR, "material": "Slate", "canCollide": collide,
         "role": "fixed", "notes": "Strates sombres + pied evase. " + col + " " + extra},
        {"object": "Strata", "color": STRATA_COLOR, "material": "Slate", "canCollide": collide,
         "role": "fixed", "notes": "Strates claires (rythme). " + col},
        {"object": "Grass", "color": GRASS_COLOR, "material": GRASS_MATERIAL, "canCollide": False,
         "role": "fixed", "notes": (grass_note or "Chapeau d'herbe plat.") + " SmoothPlastic "
                                   "(couleur unie, valide pour toute la famille)."},
    ])


def finish(asset):
    path = lw.export_asset(asset, CATEGORY)
    total = lw.report(asset)
    lw.save_blend()
    return path, total


# ---------------------------------------------------------------- assets
def build_env_cliff_a():
    """ENV_Cliff_A : pan de falaise droit 32 x 14 x 36, avant -Y, base centree."""
    asset = "ENV_Cliff_A"
    build_cliff_module(asset)
    manifest(asset, "Pan droit 32 x 14 x 36 (X x Z x Y Roblox), face avant vers -Z Roblox, pied "
                    "avant a ~6 studs du pivot. Modules a poser cote a cote avec 2 a 4 studs de "
                    "recouvrement, tournes de quelques degres. Origine = base centree.")
    return finish(asset)


# ------------------------------------------------------------- ENV_Cliff_B
B_HEIGHT = 42.0
B_STRATA = [                       # 5 strates plus fines, pendage inverse de A
    (10.5, -3.0, ROCK_COLOR, -1.1),
    (17.0, -2.6, STRATA_COLOR, 0.9),
    (24.5, -2.1, ROCK_COLOR, -0.8),
    (32.5, -1.6, STRATA_COLOR, 0.7),
    (40.4, -1.0, ROCK_COLOR, -0.3),
]
B_SHOULDER = dict(x0=-1.0, x1=5.5, z_start=25.0, drop=9.0)   # cote +X Blender = -X Roblox


def build_env_cliff_b():
    """ENV_Cliff_B : pan droit plus haut et plus etroit (~24 x 14 x 42), epaulement a +X."""
    asset = "ENV_Cliff_B"
    sh = B_SHOULDER

    def post(bms):
        shoulder(bms, sh["x0"], sh["x1"], sh["z_start"], B_HEIGHT, sh["drop"])

    build_cliff_module(asset, width=24.0, height=B_HEIGHT, strata=B_STRATA, n_front=7, seed=902,
                       post=post)
    manifest(asset, "Pan droit ~24 x 14 x 42 (X x Z x Y Roblox), 5 strates, face avant vers -Z "
                    "Roblox. Epaulement : le sommet descend a ~33 studs du cote -X Roblox "
                    "(+X Blender). Origine = base centree.",
             grass_note="Chapeau d'herbe : plat a 42 cote +X Roblox, rampe puis palier a ~33 "
                        "cote -X Roblox.")
    return finish(asset)


# -------------------------------------------------------- ENV_Cliff_Corner
CORNER_HEIGHT = 38.0
CORNER_STRATA = [
    (11.5, -3.0, ROCK_COLOR, 0.9),
    (19.5, -2.5, STRATA_COLOR, -0.7),
    (29.0, -1.9, ROCK_COLOR, 0.6),
    (36.4, -1.3, STRATA_COLOR, -0.3),
]


def build_env_cliff_corner():
    """ENV_Cliff_Corner : coin rentrant 90 deg, pans de ~20 studs, 38 de haut.
    Face 1 regarde -Y Blender (-Z Roblox), face 2 regarde +X Blender (-X Roblox)."""
    asset = "ENV_Cliff_Corner"
    plan = Outline.corner(19.5, 6.6, 4, seed=903)
    build_cliff_module(asset, height=CORNER_HEIGHT, strata=CORNER_STRATA, seed=903, plan=plan)
    manifest(asset, "Coin rentrant 90 deg, 38 de haut. Face 1 regarde -Z Roblox (-Y Blender), "
                    "face 2 regarde -X Roblox (+X Blender) : l'interieur de la carte est le quart "
                    "-X / -Z Roblox vu depuis l'angle. Origine = centre de l'emprise au sol "
                    "(angle interieur au pied : voir rapport du lot 9).")
    return finish(asset)


# ---------------------------------------------------------- ENV_Cliff_Peak
PEAK_HEIGHT = 60.0
# (fraction de hauteur du joint haut, fraction de rayon en haut, couleur, pendage_haut)
PEAK_MAIN = [
    (0.21, 0.88, ROCK_COLOR, 1.0),
    (0.40, 0.76, STRATA_COLOR, -0.9),
    (0.60, 0.64, ROCK_COLOR, 0.9),
    (0.79, 0.53, STRATA_COLOR, -0.7),
    (0.975, 0.42, ROCK_COLOR, -0.3),
]
PEAK_SUB = [
    (0.30, 0.86, ROCK_COLOR, -0.8),
    (0.56, 0.72, STRATA_COLOR, 0.7),
    (0.80, 0.60, ROCK_COLOR, -0.6),
    (0.965, 0.50, STRATA_COLOR, 0.2),
]


def peak_shell(groups, grass_parts, origin, radius, height, strata, n, seed, lean):
    """Massif ferme a strates (contour polygonal irregulier de n directions).

    Meme recette que les pans : pied evase, debord + biseau a 45 deg sous chaque strate,
    un gros plan casse rentrant et un bombement par strate, pendage des joints, chapeau
    d'herbe plat. `lean` = deplacement du centre par stud de hauteur (devers)."""
    import math
    rng = random.Random(seed)
    ph1, ph2 = rng.uniform(0.0, 6.28), rng.uniform(0.0, 6.28)
    dirs = []
    for i in range(n):
        a = 2.0 * math.pi * (i + rng.uniform(-0.2, 0.2)) / n
        ell = 1.0 + 0.12 * math.cos(a - ph1) + 0.08 * math.cos(2.0 * a - ph2)
        dirs.append((Vector((math.cos(a), math.sin(a), 0.0)), ell))
    o = Vector((origin[0], origin[1], 0.0))
    lx, ly = lean

    def ring(z, r, base, d):
        c = o + Vector((lx * z, ly * z, 0.0))
        pts = []
        for i, (u, ell) in enumerate(dirs):
            p = c + u * (r * ell + base[i] + rng.uniform(-0.25, 0.25))
            pts.append((p.x, p.y, z + d * 0.5 * u.x))
        return pts

    prev_top, prev_z, prev_r, prev_d = None, 0.0, radius, 0.0
    for s, (fz, fr, color, dip) in enumerate(strata):
        z1, r1 = fz * height, fr * radius
        srng = random.Random(seed + 10 * s)
        base = [srng.uniform(-0.9, 0.9) for _ in range(n)]
        k1 = srng.randrange(n)
        base[k1] -= 2.2                                     # gros plan casse rentrant
        base[(k1 + srng.choice((3, 4, 5))) % n] += 1.3      # bombement
        if s == 0:
            levels = [(0.0, radius + 1.8, 0.0), (2.6, radius, 0.0)]
            za, ra = 2.6, radius
        else:
            levels = [(prev_z + LIP, prev_r + LIP, prev_d)]
            za, ra = prev_z + LIP, prev_r + LIP
        for t in (0.36, 0.7):
            levels.append((za + (z1 - za) * t, ra + (r1 - ra) * t + 0.2,
                           prev_d + (dip - prev_d) * t))
        levels.append((z1, r1, dip))
        rings = [ring(z, r, base, d) for z, r, d in levels]
        if s > 0:
            lip, fixed = [], []
            for i, (u, _ell) in enumerate(dirs):
                x, y, pz = prev_top[i]
                lip.append((x + u.x * MARGIN, y + u.y * MARGIN, pz - 0.1))
                q = Vector((rings[0][i][0], rings[0][i][1], 0.0))
                adv = (q - Vector((lip[i][0], lip[i][1], 0.0))).dot(u)
                if adv < LIP * 0.8:
                    q = q + u * (LIP * 0.8 - adv)
                fixed.append((q.x, q.y, rings[0][i][2]))
            rings = [lip, fixed] + rings[1:]
        groups[color] = solid_from_rings(rings, groups[color])
        prev_top, prev_z, prev_r, prev_d = rings[-1], z1, r1, dip
    # chapeau d'herbe plat
    grng = random.Random(seed + 99)
    drop = [grng.uniform(0.0, 0.7) for _ in range(n)]
    top = prev_top

    def grass_ring(off, z_of):
        return [(top[i][0] + u.x * off, top[i][1] + u.y * off, z_of(i, top[i][2]))
                for i, (u, _ell) in enumerate(dirs)]

    H = height
    grass_parts.append(solid_from_rings([
        grass_ring(0.15, lambda i, pz: pz - 0.5 - drop[i]),
        grass_ring(0.45, lambda i, pz: min(pz + 0.15, H - 0.3) - drop[i] * 0.4),
        grass_ring(0.4, lambda i, pz: H - 0.25),
        grass_ring(0.05, lambda i, pz: H),
    ]))


def build_env_cliff_peak(asset="ENV_Cliff_Peak"):
    """ENV_Cliff_Peak : pic de fond ~30 x 30 x 60 : sommet principal deverse vers -X
    (flanc +X en gradins, flanc -X presque vertical) + epaulement secondaire de 36 a +X.
    Deux massifs fermes qui s'interpenetrent (pas de collision, vu de loin)."""
    import bpy
    coll = lw.reset_collection(asset)
    groups = {ROCK_COLOR: None, STRATA_COLOR: None}
    grass_parts = []
    peak_shell(groups, grass_parts, (-2.0, 1.5), 10.8, PEAK_HEIGHT, PEAK_MAIN, 10, 904,
               lean=(-0.07, 0.03))
    peak_shell(groups, grass_parts, (6.5, -6.0), 7.6, 36.0, PEAK_SUB, 9, 914, lean=(0.05, -0.03))
    grass = grass_parts[0]
    for extra in grass_parts[1:]:
        tmp = bpy.data.meshes.new("__lw_tmp__")
        extra.to_mesh(tmp)
        extra.free()
        grass.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    objs = []
    for color, part in ((ROCK_COLOR, "Rock"), (STRATA_COLOR, "Strata")):
        objs.append(lw.add_object(asset, part, groups[color], coll, color))
    objs.append(lw.add_object(asset, "Grass", grass, coll, GRASS_COLOR))
    recenter(objs)
    manifest(asset, "Pic de fond ~30 x 30 x 60 (sommet principal + epaulement de 36), a poser "
                    "derriere les falaises. Deux massifs fermes qui s'interpenetrent. Origine = "
                    "base centree.", collide=False,
             grass_note="Deux calottes d'herbe plates (60 et 36).")
    return finish(asset)


def build_all():
    return [build_env_cliff_a(), build_env_cliff_b(), build_env_cliff_corner(),
            build_env_cliff_peak()]


# ================================================================ planche
SUN_COLOR = (1.0, 0.78, 0.55)
SKY_COLOR = (0.95, 0.74, 0.62)      # peche (lavande -> peche -> miel)
GROUND_COLOR = "#6F8F43"            # sol d'herbe de la planche (un ton sous le chapeau)


def _pv_copy(asset, offset, turn_deg=0.0, mirror=False, tag=""):
    import math
    import bpy
    import preview as pv
    objs = pv.place(asset, ("Rock", "Strata", "Grass"), (0.0, 0.0, 0.0), tag=tag)
    for ob in objs:
        ob.location = lw.Vector(offset)
        ob.rotation_euler = (0.0, 0.0, math.radians(turn_deg))
        if mirror:
            ob.scale = (-1.0, 1.0, 1.0)
    return objs


def _camera(name, loc, target, ortho=None, lens=35.0):
    import bpy
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.clip_end = 1000.0
    cam = bpy.data.objects.new(name, cd)
    cam.location = loc
    d = lw.Vector(target) - lw.Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.data.collections["_PREVIEW"].objects.link(cam)
    return cam


def _caption(cam, text, res):
    """Etiquette collee en bas a gauche du cadre de la camera."""
    import math
    import bpy
    cu = bpy.data.curves.new("PV_Caption", type="FONT")
    cu.body = text
    ob = bpy.data.objects.new("PV_Caption", cu)
    cu.materials.append(lw.material("#1E2227"))
    bpy.data.collections["_PREVIEW"].objects.link(ob)
    ob.parent = cam
    aspect = res[1] / res[0]
    if cam.data.type == "ORTHO":
        dist = 5.0
        half_w = cam.data.ortho_scale / 2.0
    else:
        dist = 2.0
        half_w = dist * math.tan(cam.data.angle / 2.0)
    half_h = half_w * aspect
    cu.size = half_h * 0.075
    ob.location = (-half_w * 0.95, -half_h * 0.9, -dist)
    return ob


def _render_panel(cam, res, path, caption):
    import bpy
    scene = bpy.context.scene
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    cap = _caption(cam, caption, res)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cap, do_unlink=True)
    img = bpy.data.images.load(path)
    return img


def _compose(panels, layout, size, out_path):
    """panels : images ; layout : (x, y_haut) en pixels de chaque panneau."""
    import bpy
    import numpy as np
    W, H = size
    canvas = np.ones((H, W, 4), dtype=np.float32)
    canvas[..., :3] = 0.93
    for img, (x, y) in zip(panels, layout):
        w, h = img.size
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        y0 = H - y - h          # pixels Blender : origine en bas a gauche
        canvas[y0:y0 + h, x:x + w] = px
    out = bpy.data.images.new("PV_Board", W, H, alpha=False)
    out.pixels = canvas.ravel()
    out.filepath_raw = out_path
    out.file_format = "PNG"
    out.save()
    for img in panels:
        bpy.data.images.remove(img)
    bpy.data.images.remove(out)
    return out_path


def board_cliff(asset="ENV_Cliff_A", filename="lot9_cliff_A.png", overlap=3.0, keep=False):
    """Planche : module seul (face, 3/4, dessus) + rangee de 3 (recouvrement `overlap`,
    +8 / miroir X / -8 deg) avec mannequin, sol d'herbe, soleil chaud bas."""
    import math
    import os
    import tempfile
    import bpy
    import preview as pv

    scene = bpy.context.scene
    old_cam = scene.camera
    old_res = (scene.render.resolution_x, scene.render.resolution_y, scene.render.filepath)
    vs = scene.view_settings
    old_vt = vs.view_transform
    pv.clear()
    coll = bpy.data.collections["_PREVIEW"]
    # sol, soleil chaud bas, ciel peche
    g = lw.add_object("_PREVIEW", "Ground", lw.box_bm((2400.0, 2400.0, 0.2), (0.0, 0.0, -0.1)),
                      coll, GROUND_COLOR)
    g.name = "PV_Ground"
    sd = bpy.data.lights.new("PV_Sun", "SUN")
    sd.energy = 4.0
    sd.color = SUN_COLOR
    sd.angle = math.radians(3.0)
    sun = bpy.data.objects.new("PV_Sun", sd)
    sun.rotation_euler = (math.radians(66.0), 0.0, math.radians(-38.0))   # ~24 deg au-dessus
    coll.objects.link(sun)
    world = scene.world
    bg = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
    old_bg = (tuple(bg.inputs[0].default_value), bg.inputs[1].default_value) if bg else None
    if bg is not None:
        bg.inputs[0].default_value = SKY_COLOR + (1.0,)
        bg.inputs[1].default_value = 0.45

    # module seul + mannequin ; rangee de 3 plus loin
    _pv_copy(asset, (0.0, 0.0, 0.0), tag="_solo")
    pv.mannequin((-21.0, -6.0, 0.0))
    width = max(v.co.x for v in bpy.data.objects[asset + ".Rock"].data.vertices) - \
        min(v.co.x for v in bpy.data.objects[asset + ".Rock"].data.vertices)
    step = width - overlap
    rx, row_y = 400.0, 0.0
    _pv_copy(asset, (rx - step, row_y, 0.0), turn_deg=8.0, tag="_r1")
    _pv_copy(asset, (rx, row_y, 0.0), mirror=True, tag="_r2")
    _pv_copy(asset, (rx + step, row_y, 0.0), turn_deg=-8.0, tag="_r3")
    pv.mannequin((rx - 4.0, row_y - 16.0, 0.0))
    pv.hide_assets(True)
    coll.hide_render = False

    try:
        vs.view_transform = "Standard"
    except TypeError:
        pass
    tmp = tempfile.mkdtemp(prefix="lw_cliff_")
    shots = [
        (_camera("PV_Front", (-6.0, -150.0, 18.0), (-6.0, 0.0, 18.0), ortho=48.0), (900, 760),
         "Face (mannequin 5 studs)"),
        (_camera("PV_34", (-42.0, -52.0, 16.0), (0.0, 0.0, 15.0), lens=30.0), (900, 760),
         "3/4 avant"),
        (_camera("PV_Top", (0.0, -40.0, 150.0), (0.0, 0.0, 0.0), ortho=40.0), (900, 760),
         "Dessus (legerement de face)"),
        (_camera("PV_Row", (rx - 10.0, row_y - 62.0, 5.0), (rx, row_y, 17.0), lens=24.0), (1350, 840),
         "Rangee de 3 : +8 deg / miroir X / -8 deg, recouvrement %.0f studs - vue joueur" % overlap),
        (_camera("PV_RowHigh", (rx - 60.0, row_y - 75.0, 62.0), (rx, row_y, 14.0), lens=30.0),
         (1350, 840), "Rangee de 3 vue de haut (coutures)"),
    ]
    imgs = []
    for i, (cam, res, cap) in enumerate(shots):
        imgs.append(_render_panel(cam, res, os.path.join(tmp, "p%d.png" % i), cap))
    out = os.path.join(lw.RENDERS, filename)
    _compose(imgs, [(0, 0), (900, 0), (1800, 0), (0, 760), (1350, 760)], (2700, 1600), out)

    vs.view_transform = old_vt
    scene.render.resolution_x, scene.render.resolution_y, scene.render.filepath = old_res
    if bg is not None and old_bg is not None:
        bg.inputs[0].default_value, bg.inputs[1].default_value = old_bg
    scene.camera = old_cam
    if not keep:
        pv.cleanup()
    return out


def _bounds(asset):
    """Bornes XY (Rock + Strata) d'un module dans son repere local."""
    import bpy
    xs, ys = [], []
    for part in ("Rock", "Strata"):
        for v in bpy.data.objects[asset + "." + part].data.vertices:
            xs.append(v.co.x)
            ys.append(v.co.y)
    return min(xs), max(xs), min(ys), max(ys)


def assembly_layout(overlap=3.0):
    """Petit angle ferme : B, A (pan 2, regarde +X Blender) - Corner - A, B (pan 1, regarde
    -Y Blender). Renvoie [(asset, (x, y), rotation_deg)], le coin a l'origine.
    Les dos des pans sont alignes sur les dos des branches du coin ; recouvrement `overlap`."""
    cx0, cx1, cy0, cy1 = _bounds("ENV_Cliff_Corner")
    out = [("ENV_Cliff_Corner", (0.0, 0.0), 0.0)]
    # pan 1 : vers +X, dos sur cy1
    x_end = cx1
    for asset in ("ENV_Cliff_A", "ENV_Cliff_B"):
        x0, x1, _y0, y1 = _bounds(asset)
        px = x_end - overlap - x0
        out.append((asset, (px, cy1 - y1), 0.0))
        x_end = px + x1
    # pan 2 : vers -Y, modules tournes de +90 deg (avant local -Y -> +X monde,
    # x local -> +Y monde, dos local +Y -> -X monde)
    y_end = cy0
    for asset in ("ENV_Cliff_A", "ENV_Cliff_B"):
        x0, x1, _y0, y1 = _bounds(asset)
        py = y_end + overlap - x1
        out.append((asset, (cx0 + y1, py), 90.0))
        y_end = py + x0
    return out


def board_cliffs(filename="lot9_cliffs.png", overlap=3.0, keep=False):
    """Planche de la famille : les 4 modules alignes avec mannequin, puis un angle ferme
    (B, A, Corner, A, B + Peak derriere) vu a hauteur de joueur et de 3/4 haut."""
    import math
    import os
    import tempfile
    import bpy
    import preview as pv

    scene = bpy.context.scene
    old_cam = scene.camera
    old_res = (scene.render.resolution_x, scene.render.resolution_y, scene.render.filepath)
    vs = scene.view_settings
    old_vt = vs.view_transform
    pv.clear()
    coll = bpy.data.collections["_PREVIEW"]
    g = lw.add_object("_PREVIEW", "Ground", lw.box_bm((2400.0, 2400.0, 0.2), (0.0, 0.0, -0.1)),
                      coll, GROUND_COLOR)
    g.name = "PV_Ground"
    sd = bpy.data.lights.new("PV_Sun", "SUN")
    sd.energy = 4.0
    sd.color = SUN_COLOR
    sd.angle = math.radians(3.0)
    sun = bpy.data.objects.new("PV_Sun", sd)
    sun.rotation_euler = (math.radians(66.0), 0.0, math.radians(-38.0))
    coll.objects.link(sun)
    world = scene.world
    bg = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
    old_bg = (tuple(bg.inputs[0].default_value), bg.inputs[1].default_value) if bg else None
    if bg is not None:
        bg.inputs[0].default_value = SKY_COLOR + (1.0,)
        bg.inputs[1].default_value = 0.45

    # 1) les 4 modules alignes (le coin tourne de -45 deg pour montrer ses deux faces)
    lx = 600.0
    x = lx
    pv.mannequin((x + 4.0, -12.0, 0.0))
    row = [("ENV_Cliff_A", 0.0, "A"), ("ENV_Cliff_B", 0.0, "B"),
           ("ENV_Cliff_Corner", -45.0, "Corner"), ("ENV_Cliff_Peak", 0.0, "Peak")]
    centers = []
    for asset, turn, tag in row:
        x0, x1, _y0, _y1 = _bounds(asset)
        half = (x1 - x0) / 2.0 if turn == 0.0 else 19.5
        x += half
        _pv_copy(asset, (x, 0.0, 0.0), turn_deg=turn, tag="_l" + tag)
        centers.append(x)
        x += half + 7.0
    line_c = (lx + x) / 2.0

    # 2) l'angle ferme, coin a l'origine + pic derriere
    for i, (asset, (px, py), rot) in enumerate(assembly_layout(overlap)):
        _pv_copy(asset, (px, py, 0.0), turn_deg=rot, tag="_a%d" % i)
    cx0, _cx1, _cy0, cy1 = _bounds("ENV_Cliff_Corner")
    _pv_copy("ENV_Cliff_Peak", (cx0 - 26.0, cy1 + 30.0, 0.0), turn_deg=20.0, tag="_apk")
    pv.mannequin((12.0, -14.0, 0.0))
    pv.hide_assets(True)
    coll.hide_render = False
    try:
        vs.view_transform = "Standard"
    except TypeError:
        pass

    tmp = tempfile.mkdtemp(prefix="lw_cliffs_")
    span = x - lx
    shots = [
        (_camera("PV_Line", (line_c, -300.0, 115.0), (line_c, 0.0, 29.0),
                 ortho=max(span + 16.0, 72.0 * 3.0)),
         (2700, 900), "ENV_Cliff_A / ENV_Cliff_B / ENV_Cliff_Corner (tourne de -45 deg) / "
                      "ENV_Cliff_Peak - mannequin 5 studs"),
        (_camera("PV_AsmLow", (40.0, -46.0, 5.5), (-4.0, 4.0, 21.0), lens=17.0), (1350, 900),
         "Angle ferme B, A, Corner, A, B + Peak - vue joueur"),
        (_camera("PV_AsmHigh", (105.0, -120.0, 85.0), (-8.0, 8.0, 10.0), lens=28.0), (1350, 900),
         "Angle ferme - 3/4 haut (recouvrement %.0f studs)" % overlap),
    ]
    imgs = []
    for i, (cam, res, cap) in enumerate(shots):
        imgs.append(_render_panel(cam, res, os.path.join(tmp, "p%d.png" % i), cap))
    out = os.path.join(lw.RENDERS, filename)
    _compose(imgs, [(0, 0), (0, 900), (1350, 900)], (2700, 1800), out)

    vs.view_transform = old_vt
    scene.render.resolution_x, scene.render.resolution_y, scene.render.filepath = old_res
    if bg is not None and old_bg is not None:
        bg.inputs[0].default_value, bg.inputs[1].default_value = old_bg
    scene.camera = old_cam
    if not keep:
        pv.cleanup()
    return out
