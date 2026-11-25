"""Plan SVG vu du dessus d'une variante de carte du lot 9 (bibliothèque standard uniquement).

Usage :
    python scripts/lot9_plan.py renders/lot9/A_mesures.json renders/lot9/A_plan.svg

Entrée : le fichier <X>_mesures.json écrit après le relevé dans Studio, avec au minimum :
  - "variante", "nom"
  - "geometrie" : liste {n (nom), g (dossier parent), c (classe), p [x,y,z], s [sx,sy,sz], ry (degrés), col (hex)}
    en coordonnées RELATIVES à l'origine de la variante ;
  - "parcelles" : {"PlotN": {"center": [x,y,z], "facingX": ±1}}  (ou "facing": [dx, dz]) ;
  - "reperes" : {"VaultDoor_PlotN", "AnvilStand", "SpawnPad", "MineCenter", "Ore_C*", "Ore_R*"} -> {"p": [...]} ;
  - "trajets" : {"PlotN": {"coffre_vers_gisement": {"s"}, "coffre_vers_enclume": {"s"}, "centre_mine_vers_coffre": {"s"}}} ;
  - "apparition_vers_enclume": {"s"} ; "dimensions" (optionnel) : zone_jouable_x/z, largeur_rue, cotes_rue_x.
Convention : nord (-Z) en haut, est (+X) à droite. Échelle constante (SCALE px par stud).
"""
import json
import math
import sys
from xml.sax.saxutils import escape

SCALE = 4.0
MARGIN = 60
PANEL = 330  # colonne de droite (légende + tableau)


def main(src, dst):
    d = json.load(open(src, encoding="utf-8"))
    geo = d["geometrie"]
    # emprise : toutes les pièces (y compris falaises)
    xs, zs = [], []
    for g in geo:
        hx, hz = g["s"][0] / 2, g["s"][2] / 2
        r = math.hypot(hx, hz) if abs(g.get("ry", 0)) % 90 > 0.5 else None
        if r:
            hx = hz = r
        elif abs(abs(g.get("ry", 0)) - 90) < 0.5:
            hx, hz = hz, hx
        xs += [g["p"][0] - hx, g["p"][0] + hx]
        zs += [g["p"][2] - hz, g["p"][2] + hz]
    x0, x1 = max(min(xs), -90), min(max(xs), 90)
    z0, z1 = max(min(zs), -160), min(max(zs), 130)
    W = (x1 - x0) * SCALE + 2 * MARGIN
    H = (z1 - z0) * SCALE + 2 * MARGIN

    def X(x):
        return MARGIN + (x - x0) * SCALE

    def Z(z):
        return MARGIN + (z - z0) * SCALE

    out = []
    a = out.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W + PANEL:.0f}" height="{H:.0f}" '
      f'viewBox="0 0 {W + PANEL:.0f} {H:.0f}" font-family="Segoe UI, Arial, sans-serif">')
    a('<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">'
      '<path d="M0,0 L8,4 L0,8 z" fill="#ffd23f"/></marker>'
      '<marker id="dim" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse">'
      '<path d="M0,0 L8,4 L0,8 z" fill="#111"/></marker></defs>')
    a(f'<rect width="100%" height="100%" fill="#f4f1ea"/>')

    # ordre de dessin : sol -> parcelles -> mine -> place -> clôtures -> falaises
    order = {"Ground": 0, "Mine": 2, "Ores": 4, "Square": 3, "Fences": 3, "Cliffs": 5}

    def key(g):
        if g["g"].startswith("Plot"):
            return 1 if g["n"] in ("Base", "Slab") else 3
        return order.get(g["g"], 2)

    for g in sorted(geo, key=key):
        if g["g"] == "Cliffs" and g["n"] == "CliffTilt":
            continue  # blocs inclinés au-dessus des falaises : inutiles en plan
        sx, sz = g["s"][0] * SCALE, g["s"][2] * SCALE
        cx, cz = X(g["p"][0]), Z(g["p"][2])
        # rotation Roblox autour de Y (ry > 0 = sens trigo vu du dessus) -> SVG (Z vers le bas) = -ry
        rot = -g.get("ry", 0)
        stroke = "#00000033"
        if g["g"] == "Cliffs":
            stroke = "#5a4e44"
        a(f'<rect x="{cx - sx / 2:.1f}" y="{cz - sz / 2:.1f}" width="{sx:.1f}" height="{sz:.1f}" '
          f'fill="#{g["col"]}" stroke="{stroke}" stroke-width="0.6" '
          f'transform="rotate({rot:.1f} {cx:.1f} {cz:.1f})"/>')

    rep = d.get("reperes", {})
    tr = d.get("trajets", {})

    def label(x, z, text, size=13, fill="#fff", bg="#1c1c22", anchor="middle"):
        w = len(text) * size * 0.58 + 10
        px, pz = X(x), Z(z)
        lx = px - w / 2 if anchor == "middle" else px
        a(f'<rect x="{lx:.1f}" y="{pz - size * 0.85:.1f}" width="{w:.1f}" height="{size * 1.45:.1f}" rx="4" fill="{bg}" opacity="0.88"/>')
        a(f'<text x="{lx + w / 2:.1f}" y="{pz + size * 0.38:.1f}" font-size="{size}" fill="{fill}" '
          f'text-anchor="middle" font-weight="bold">{escape(text)}</text>')

    # parcelles : flèche d'orientation du coffre + étiquettes + temps
    for name, p in sorted(d.get("parcelles", {}).items()):
        c = p["center"]
        f = p.get("facing") or [p.get("facingX", 0), 0]
        door = rep.get("VaultDoor_" + name, {}).get("p")
        vc = rep.get("VaultDoor_" + name, {}).get("vaultCenter") or c
        x2, z2 = vc[0] + f[0] * 11, vc[2] + f[1] * 11
        a(f'<line x1="{X(vc[0]):.1f}" y1="{Z(vc[2]):.1f}" x2="{X(x2):.1f}" y2="{Z(z2):.1f}" '
          f'stroke="#ffd23f" stroke-width="3" marker-end="url(#arr)"/>')
        label(c[0] - f[0] * 6, c[2] - 7, name, 14)
        t = tr.get(name)
        if t:
            label(c[0] - f[0] * 6, c[2] + 2, f'gis. {t["coffre_vers_gisement"]["s"]:.1f} s', 11, "#c8f7c5", "#20302a")
            label(c[0] - f[0] * 6, c[2] + 8, f'forge {t["coffre_vers_enclume"]["s"]:.1f} s', 11, "#ffd8a8", "#3a2a1c")
            label(c[0] - f[0] * 6, c[2] + 14, f'mine→coffre {t["centre_mine_vers_coffre"]["s"]:.1f} s', 11, "#cfe3ff", "#1c2638")

    # points clés
    def dot(pos, color, r=4):
        a(f'<circle cx="{X(pos[0]):.1f}" cy="{Z(pos[2]):.1f}" r="{r}" fill="{color}" stroke="#111" stroke-width="1"/>')

    for k, v in rep.items():
        if k.startswith("Ore_R"):
            dot(v["p"], "#b06bff", 4)
        elif k.startswith("Ore_C"):
            dot(v["p"], "#ffffff", 3)
    mc = rep.get("MineCenter", {}).get("p")
    an = rep.get("AnvilStand", {})
    sp = rep.get("SpawnPad", {}).get("p")
    if mc:
        dot(mc, "#ff4d4d", 5)
    ores = [v["p"] for k, v in rep.items() if k.startswith("Ore_")]
    rares = [v["p"] for k, v in rep.items() if k.startswith("Ore_R")]
    if ores:
        zmin = min(o[2] for o in ores)
        label(sum(o[0] for o in ores) / len(ores), zmin - 9, "Mine", 14)
    if rares:
        label(sum(o[0] for o in rares) / len(rares) + 16, sum(o[2] for o in rares) / len(rares), "Rares", 13, "#fff", "#5b2a8a")
    anvil = an.get("anvilCenter") or an.get("p")
    if anvil:
        dot(anvil, "#ff8c1a", 5)
        label(anvil[0] - 16, anvil[2] - 14, "Forge (enclume)", 13, "#fff", "#7a3e10")
    if sp:
        dot(sp, "#4d7cff", 5)
        label(sp[0], sp[2] + 9, "Apparition", 13, "#fff", "#24406e")
        if anvil and "apparition_vers_enclume" in d:
            a(f'<line x1="{X(sp[0]):.1f}" y1="{Z(sp[2]):.1f}" x2="{X(anvil[0]):.1f}" y2="{Z(anvil[2]):.1f}" '
              f'stroke="#24406e" stroke-width="1.5" stroke-dasharray="5 4"/>')
            label((sp[0] + anvil[0]) / 2, (sp[2] + anvil[2]) / 2 - 3,
                  f'{d["apparition_vers_enclume"]["s"]:.1f} s', 11, "#fff", "#24406e")
    boards = [g for g in geo if g["n"].startswith("Board") and "Post" not in g["n"]]
    if boards:
        bx = sum(g["p"][0] for g in boards) / len(boards)
        bz = sum(g["p"][2] for g in boards) / len(boards)
        label(bx, bz - 6, "Classements", 13, "#fff", "#333a4a")

    # cotes
    dims = d.get("dimensions", {})

    def cote(xa, za, xb, zb, text, off=0):
        a(f'<line x1="{X(xa):.1f}" y1="{Z(za):.1f}" x2="{X(xb):.1f}" y2="{Z(zb):.1f}" stroke="#111" '
          f'stroke-width="1.4" marker-start="url(#dim)" marker-end="url(#dim)"/>')
        label((xa + xb) / 2, (za + zb) / 2 + off, text, 12, "#111", "#ffffffdd")

    zx = dims.get("zone_jouable_x")
    zz = dims.get("zone_jouable_z")
    if "largeur_rue" in dims:
        half = dims["largeur_rue"] / 2
        cote(-half, 76 if not zz else min(zz[1] - 6, 76), half, 76 if not zz else min(zz[1] - 6, 76),
             f'rue {dims["largeur_rue"]}')
    if zx and zz:
        cote(zx[0], zz[0] - 6, zx[1], zz[0] - 6, f'{zx[1] - zx[0]:.0f} studs', -4)
        a(f'<line x1="{X(zx[1] + 9):.1f}" y1="{Z(zz[0]):.1f}" x2="{X(zx[1] + 9):.1f}" y2="{Z(zz[1]):.1f}" '
          f'stroke="#111" stroke-width="1.4" marker-start="url(#dim)" marker-end="url(#dim)"/>')
        label(zx[1] + 9, (zz[0] + zz[1]) / 2, f'{zz[1] - zz[0]:.0f}', 12, "#111", "#ffffffdd")

    # rose des vents + échelle
    a(f'<text x="{MARGIN - 40}" y="{MARGIN - 20}" font-size="16" font-weight="bold">N ↑ (−Z)</text>')
    a(f'<line x1="{MARGIN}" y1="{H - 25}" x2="{MARGIN + 32 * SCALE}" y2="{H - 25}" stroke="#111" stroke-width="3"/>')
    a(f'<text x="{MARGIN}" y="{H - 32}" font-size="12">32 studs (une parcelle)</text>')

    # panneau de droite
    px = W + 10
    y = MARGIN
    a(f'<text x="{px}" y="{y}" font-size="20" font-weight="bold">Variante {escape(d.get("variante", "?"))}</text>')
    y += 22
    a(f'<text x="{px}" y="{y}" font-size="14">{escape(d.get("nom", ""))}</text>')
    y += 30
    a(f'<text x="{px}" y="{y}" font-size="13" font-weight="bold">Temps à 16 studs/s (chemins PathfindingService)</text>')
    y += 20
    a(f'<text x="{px}" y="{y}" font-size="12" font-weight="bold" font-family="Consolas, monospace" xml:space="preserve">Parcelle gisement  forge  mine→coffre</text>')
    for name in sorted(tr):
        y += 17
        t = tr[name]
        a(f'<text x="{px}" y="{y}" font-size="12" font-family="Consolas, monospace" xml:space="preserve">{name:<9}'
          f'{t["coffre_vers_gisement"]["s"]:>6.1f} s {t["coffre_vers_enclume"]["s"]:>6.1f} s '
          f'{t["centre_mine_vers_coffre"]["s"]:>7.1f} s</text>')
    if "apparition_vers_enclume" in d:
        y += 22
        a(f'<text x="{px}" y="{y}" font-size="12">Apparition → enclume : {d["apparition_vers_enclume"]["s"]:.1f} s</text>')
    vm = d.get("validation_marche", {})
    if vm.get("client_MoveTo"):
        y += 18
        a(f'<text x="{px}" y="{y}" font-size="12">Marche réelle {escape(vm.get("trajet", "").split(" (")[0])} :</text>')
        y += 16
        a(f'<text x="{px}" y="{y}" font-size="12">  {vm["client_MoveTo"]["temps_reel_s"]:.2f} s mesuré / '
          f'{vm.get("temps_calcule_s", 0):.2f} s calculé</text>')
    vis = d.get("visibilite", {}).get("depuis_centre_mine_y_plus_5")
    if vis:
        y += 22
        a(f'<text x="{px}" y="{y}" font-size="12">Coffres visibles du centre de la mine : {vis["coffres_visibles"]}/8</text>')
    cost = d.get("cout", {})
    if cost:
        y += 18
        a(f'<text x="{px}" y="{y}" font-size="12">Pièces du blockout : {cost.get("pieces_geometrie")}</text>')
    y += 30
    legend = [("#ffd23f", "flèche = porte du coffre"), ("#ffffff", "gisement commun"), ("#b06bff", "gisement rare"),
              ("#ff4d4d", "centre de la mine"), ("#ff8c1a", "enclume"), ("#4d7cff", "socle d'apparition")]
    for col, txt in legend:
        a(f'<circle cx="{px + 6}" cy="{y - 4}" r="5" fill="{col}" stroke="#111"/>'
          f'<text x="{px + 18}" y="{y}" font-size="12">{escape(txt)}</text>')
        y += 18
    a('</svg>')
    open(dst, "w", encoding="utf-8").write("\n".join(out))
    print("écrit", dst, f"{W + PANEL:.0f}x{H:.0f}")


# ---------------------------------------------------------------------------
# Mode « planche » : les 3 plans côte à côte, même échelle, légende unique.
#   python scripts/lot9_plan.py --planche renders/lot9/A_mesures.json renders/lot9/B_mesures.json \
#          renders/lot9/C_mesures.json renders/lot9_variantes.svg
# Les couleurs viennent de la CATÉGORIE de chaque pièce (pas de la couleur Studio), pour que la
# légende soit strictement identique pour les trois variantes.
# ---------------------------------------------------------------------------
PL_SCALE = 3.5  # px par stud, identique pour les 3 plans
PL_COLORS = {
    "sol": "#8d8f86",        # sol hors rue
    "rue": "#e6d39a",        # rue et place
    "mine": "#94704a",       # zone de la mine (cuvette, monticule, îlots, rochers de bordure)
    "parcelle": "#9cc58a",   # parcelle (socle, terrasse, rampe)
    "dalle": "#7aa36a",      # dalle du coffre
    "coffre": "#3b3b40",     # coffre
    "porte": "#c0392b",      # face avant du coffre
    "cloture": "#1c1c22",    # clôtures / murs séparateurs
    "falaise": "#4f4842",    # falaises
    "forge": "#e07b24",      # forge, enclume, terrasse de forge
    "apparition": "#2f6fd6", # socle d'apparition
    "classement": "#17a2a2", # panneaux de classement
    "commun": "#f4f4f4",     # gisement commun
    "rare": "#9b4dff",       # gisement rare
    "fleche": "#ffd23f",     # flèche = porte du coffre
}


def _categorie(g):
    grp, n = g["g"], g["n"]
    if grp == "Cliffs":
        return None if n == "CliffTilt" else "falaise"
    if grp == "Fences":
        return "cloture"
    if grp == "Mine":
        return "mine"
    if grp == "Ores":
        return "rare" if n.startswith("Ore_R") else "commun"
    if grp == "Ground":
        if n in ("Street", "Square"):
            return "rue"
        if n in ("IslandPatch", "PlazaUnder"):
            return "mine"
        return "sol"
    if grp.startswith("Plot"):
        return {"Vault": "coffre", "VaultFront": "porte", "Slab": "dalle"}.get(n, "parcelle")
    if grp == "Square":
        if n == "SpawnPad":
            return "apparition"
        if n.startswith("Board"):
            return "classement"
        return "forge"
    return "sol"


def _emprise(geo):
    xs, zs = [], []
    for g in geo:
        hx, hz = g["s"][0] / 2, g["s"][2] / 2
        if abs(g.get("ry", 0)) % 90 > 0.5:
            hx = hz = math.hypot(hx, hz)
        elif abs(abs(g.get("ry", 0)) - 90) < 0.5:
            hx, hz = hz, hx
        xs += [g["p"][0] - hx, g["p"][0] + hx]
        zs += [g["p"][2] - hz, g["p"][2] + hz]
    return max(min(xs), -90), min(max(xs), 90), max(min(zs), -170), min(max(zs), 130)


def _dec(v):
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(str(v)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)).replace(".", ",")


def planche(srcs, dst):
    S = PL_SCALE
    data = [json.load(open(s, encoding="utf-8")) for s in srcs]
    boxes = [_emprise(d["geometrie"]) for d in data]
    z0 = min(b[2] for b in boxes)  # même plage Z pour les 3 : les plans sont alignés nord-sud
    z1 = max(b[3] for b in boxes)
    GAP, M, TOP = 70, 40, 120
    widths = [(b[1] - b[0]) * S for b in boxes]
    plan_h = (z1 - z0) * S
    W = M * 2 + sum(widths) + GAP * (len(data) - 1)
    LEG_H = 170
    H = TOP + plan_h + 95 + LEG_H
    out = []
    a = out.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
      f'viewBox="0 0 {W:.0f} {H:.0f}" font-family="Segoe UI, Arial, sans-serif">')
    a('<defs><marker id="arr" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">'
      f'<path d="M0,0 L7,3.5 L0,7 z" fill="{PL_COLORS["fleche"]}"/></marker></defs>')
    a('<rect width="100%" height="100%" fill="#f4f1ea"/>')
    a(f'<text x="{M}" y="44" font-size="28" font-weight="bold" fill="#1c1c22">Lot 9 — « La rue des serruriers » : '
      f'les 3 variantes vues du dessus</text>')
    a(f'<text x="{M}" y="72" font-size="15" fill="#333">Même échelle pour les trois plans ({_dec(S)} px par stud), '
      f'nord (−Z, forge et apparition) en haut, plans alignés sur la même profondeur. Temps à 16 studs/s '
      f'(chemins PathfindingService).</text>')
    xoff = M
    for d, b, w in zip(data, boxes, widths):
        x0 = b[0]

        def X(x, xoff=xoff, x0=x0):
            return xoff + (x - x0) * S

        def Z(z):
            return TOP + (z - z0) * S

        cid = f'clip{d["variante"]}'
        a(f'<clipPath id="{cid}"><rect x="{xoff:.1f}" y="{TOP:.1f}" width="{w:.1f}" height="{plan_h:.1f}"/></clipPath>')
        a(f'<text x="{xoff + w / 2:.1f}" y="{TOP - 16}" font-size="22" font-weight="bold" text-anchor="middle" '
          f'fill="#1c1c22">VARIANTE {escape(d["variante"])} — {escape(d["nom"])}</text>')
        a(f'<g clip-path="url(#{cid})">')
        a(f'<rect x="{xoff:.1f}" y="{TOP:.1f}" width="{w:.1f}" height="{plan_h:.1f}" fill="#ffffff"/>')
        order = {"sol": 0, "rue": 1, "mine": 2, "parcelle": 3, "dalle": 4, "cloture": 5, "forge": 5,
                 "apparition": 5, "classement": 6, "coffre": 6, "porte": 7, "commun": 8, "rare": 8, "falaise": 9}
        geo = [(g, _categorie(g)) for g in d["geometrie"]]
        for g, cat in sorted([t for t in geo if t[1]], key=lambda t: order[t[1]]):
            sx, sz = g["s"][0], g["s"][2]
            if cat == "classement" and "Post" not in g["n"]:
                sz = max(sz, 3)  # panneau de 1 stud d'épaisseur : épaissi pour rester lisible
            if cat == "porte":
                sx, sz = max(sx, 1.5), max(sz, 1.5)
            sx, sz = sx * S, sz * S
            cx, cz = X(g["p"][0]), Z(g["p"][2])
            stroke = "#2e2924" if cat == "falaise" else "#00000040"
            a(f'<rect x="{cx - sx / 2:.1f}" y="{cz - sz / 2:.1f}" width="{sx:.1f}" height="{sz:.1f}" '
              f'fill="{PL_COLORS[cat]}" stroke="{stroke}" stroke-width="0.6" '
              f'transform="rotate({-g.get("ry", 0):.1f} {cx:.1f} {cz:.1f})"/>')
        rep = d.get("reperes", {})
        # flèches de porte de coffre
        for name, p in sorted(d.get("parcelles", {}).items()):
            f = p.get("facing") or [p.get("facingX", 0), 0]
            vc = rep.get("VaultDoor_" + name, {}).get("vaultCenter") or p["center"]
            x2, z2 = vc[0] + f[0] * 10, vc[2] + f[1] * 10
            a(f'<line x1="{X(vc[0]):.1f}" y1="{Z(vc[2]):.1f}" x2="{X(x2):.1f}" y2="{Z(z2):.1f}" '
              f'stroke="{PL_COLORS["fleche"]}" stroke-width="3" marker-end="url(#arr)"/>')
            # numéro de parcelle, du côté opposé à la porte
            c = p["center"]
            nx, nz = X(c[0] - f[0] * 7), Z(c[2])
            a(f'<circle cx="{nx:.1f}" cy="{nz:.1f}" r="10" fill="#ffffffd0" stroke="#1c1c22" stroke-width="1"/>'
              f'<text x="{nx:.1f}" y="{nz + 5:.1f}" font-size="14" font-weight="bold" text-anchor="middle" '
              f'fill="#1c1c22">{name[4:]}</text>')
        # gisements (points sur les repères)
        for k, v in rep.items():
            if k.startswith("Ore_"):
                cat = "rare" if k.startswith("Ore_R") else "commun"
                a(f'<circle cx="{X(v["p"][0]):.1f}" cy="{Z(v["p"][2]):.1f}" r="{6 if cat == "rare" else 5}" '
                  f'fill="{PL_COLORS[cat]}" stroke="#111" stroke-width="1.3"/>')
        a('</g>')
        a(f'<rect x="{xoff:.1f}" y="{TOP:.1f}" width="{w:.1f}" height="{plan_h:.1f}" fill="none" stroke="#1c1c22" stroke-width="1.5"/>')
        # chiffres clés
        tr = d["trajets"]
        fmax = max(t["coffre_vers_enclume"]["s"] for t in tr.values())
        mc = [t["centre_mine_vers_coffre"]["s"] for t in tr.values()]
        dims = d["dimensions"]
        lx = dims["zone_jouable_x"][1] - dims["zone_jouable_x"][0]
        lz = dims["zone_jouable_z"][1] - dims["zone_jouable_z"][0]
        y = TOP + plan_h + 30
        a(f'<text x="{xoff + w / 2:.1f}" y="{y:.1f}" font-size="16" font-weight="bold" text-anchor="middle" '
          f'fill="#1c1c22">coffre → forge max {_dec(fmax)} s · mine → coffre {_dec(min(mc))}–{_dec(max(mc))} s</text>')
        a(f'<text x="{xoff + w / 2:.1f}" y="{y + 22:.1f}" font-size="15" text-anchor="middle" fill="#333">'
          f'zone jouable {lx:.0f} × {lz:.0f} studs · apparition → enclume {_dec(d["apparition_vers_enclume"]["s"])} s</text>')
        xoff += w + GAP
    # légende commune
    y0 = TOP + plan_h + 95
    a(f'<rect x="{M}" y="{y0 - 22}" width="{W - 2 * M:.0f}" height="{LEG_H - 10}" rx="8" fill="#ffffff" stroke="#bbb"/>')
    a(f'<text x="{M + 16}" y="{y0 + 4}" font-size="16" font-weight="bold">Légende (identique pour les trois plans)</text>')
    items = [("rect", "parcelle", "parcelle"), ("rect", "dalle", "dalle du coffre"), ("rect", "coffre", "coffre"),
             ("rect", "porte", "face avant du coffre"), ("arrow", "fleche", "porte du coffre (sens)"),
             ("rect", "rue", "rue et place"), ("rect", "sol", "sol hors rue"), ("rect", "mine", "zone de la mine"),
             ("dot", "commun", "gisement commun"), ("dot", "rare", "gisement rare"), ("rect", "forge", "forge et enclume"),
             ("rect", "apparition", "socle d'apparition"), ("rect", "classement", "panneaux de classement"),
             ("rect", "falaise", "falaises"), ("rect", "cloture", "clôture / mur")]
    cols = 5
    colw = (W - 2 * M - 32) / cols
    for i, (kind, cat, txt) in enumerate(items):
        cx = M + 16 + (i % cols) * colw
        cy = y0 + 34 + (i // cols) * 30
        if kind == "rect":
            a(f'<rect x="{cx:.1f}" y="{cy - 12:.1f}" width="26" height="16" fill="{PL_COLORS[cat]}" stroke="#111" stroke-width="0.8"/>')
        elif kind == "dot":
            a(f'<circle cx="{cx + 13:.1f}" cy="{cy - 4:.1f}" r="7" fill="{PL_COLORS[cat]}" stroke="#111" stroke-width="1.3"/>')
        else:
            a(f'<line x1="{cx:.1f}" y1="{cy - 4:.1f}" x2="{cx + 22:.1f}" y2="{cy - 4:.1f}" stroke="{PL_COLORS[cat]}" '
              f'stroke-width="3" marker-end="url(#arr)"/>')
        a(f'<text x="{cx + 36:.1f}" y="{cy + 1:.1f}" font-size="15" fill="#1c1c22">{escape(txt)}</text>')
    yb = y0 + 34 + 3 * 30 + 4
    a(f'<line x1="{M + 16}" y1="{yb}" x2="{M + 16 + 32 * S:.1f}" y2="{yb}" stroke="#111" stroke-width="4"/>')
    a(f'<text x="{M + 26 + 32 * S:.1f}" y="{yb + 5}" font-size="14">32 studs (une parcelle) · cercle numéroté = parcelle Plot1 à Plot8</text>')
    a('</svg>')
    open(dst, "w", encoding="utf-8").write("\n".join(out))
    print("écrit", dst, f"{W:.0f}x{H:.0f}", f"échelle {S} px/stud")


if __name__ == "__main__":
    if sys.argv[1] == "--planche":
        planche(sys.argv[2:-1], sys.argv[-1])
    else:
        main(sys.argv[1], sys.argv[2])
