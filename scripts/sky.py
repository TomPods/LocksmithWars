"""SKY_Warm : ciel de fin d'apres-midi (16 h 30) peint proceduralement dans Blender.

build_sky_warm() est idempotente : elle (re)cree la scene "SKY_Warm" (monde a degrade +
lueur solaire + nuages low-poly emissifs) et 6 cameras cubemap a 90 deg.
render_sky_warm(out_dir) rend les 6 faces 1024x1024 en PNG RGB.
Aucun asset externe, aucun generateur d'images.

Repere : Roblox (x, y, z) -> Blender (-x, z, y)  (rotation propre, pas de miroir).
Convention des faces (repere Roblox, image "haut" entre crochets) :
  Ft : regarde -Z  [haut +Y]     Bk : regarde +Z  [haut +Y]
  Lf : regarde -X  [haut +Y]     Rt : regarde +X  [haut +Y]
  Up : regarde +Y  [haut +Z]     Dn : regarde -Y  [haut -Z]
(croix standard : Up au-dessus de Ft, Dn en dessous, rangee Lf Ft Rt Bk)
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

SCENE = "SKY_Warm"
SUN_ROBLOX = Vector((-0.847, 0.351, -0.399)).normalized()

# Palette (sRGB hex)
PAL = {
    "dn":        "#D8AE7C",  # sol / sous l'horizon (miel assombri)
    "horizon":   "#F6D38C",  # miel
    "apricot":   "#F7C28F",  # abricot
    "peach":     "#F2B596",  # peche
    "rose":      "#DDB0B8",  # rose poudre
    "lavender":  "#B4AACF",  # lavande
    "zenith":    "#8F9DCB",  # bleu-lavande desature
    "glow":      "#FFD99E",  # lueur solaire
    "cl_under":  "#BFAFD3",  # dessous des nuages
    "cl_mid":    "#F2D3D0",  # flancs rose pale
    "cl_top":    "#FFF1DC",  # dessus creme
    "cl_sun":    "#FFE2B0",  # facettes tournees vers le soleil
}

FACES = {  # nom : (direction Roblox, haut image Roblox)
    "Ft": ((0, 0, -1), (0, 1, 0)),
    "Bk": ((0, 0, 1), (0, 1, 0)),
    "Lf": ((-1, 0, 0), (0, 1, 0)),
    "Rt": ((1, 0, 0), (0, 1, 0)),
    "Up": ((0, 1, 0), (0, 0, 1)),
    "Dn": ((0, -1, 0), (0, 0, -1)),
}


def rb2bl(v):
    return Vector((-v[0], v[2], v[1]))


def hex_lin(h, a=1.0):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, a)


def _ramp(nodes, stops, constant=False):
    r = nodes.new("ShaderNodeValToRGB")
    cr = r.color_ramp
    if constant:
        cr.interpolation = "CONSTANT"
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][0]
    cr.elements[0].color = hex_lin(PAL[stops[0][1]])
    for pos, key in stops[1:]:
        e = cr.elements.new(pos)
        e.color = hex_lin(PAL[key])
    return r


def _math(nodes, links, op, a, b=None, clamp=False):
    n = nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            links.new(v, n.inputs[i])
    return n.outputs[0]


def _world(sun_bl):
    w = bpy.data.worlds.get("SKY_Warm_World") or bpy.data.worlds.new("SKY_Warm_World")
    w.use_nodes = True
    nt = w.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    tc = nodes.new("ShaderNodeTexCoord")
    nrm = nodes.new("ShaderNodeVectorMath"); nrm.operation = "NORMALIZE"
    links.new(tc.outputs["Generated"], nrm.inputs[0])
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(nrm.outputs["Vector"], sep.inputs[0])
    z = sep.outputs["Z"]
    fac = _math(nodes, links, "MULTIPLY_ADD", z, 0.5)
    fac.node.inputs[2].default_value = 0.5
    # z -> fac = z/2 + 0.5 ; horizon a 0.5
    grad = _ramp(nodes, [
        (0.0, "dn"), (0.43, "dn"), (0.5, "horizon"), (0.555, "apricot"),
        (0.60, "peach"), (0.68, "rose"), (0.80, "lavender"), (1.0, "zenith")])
    links.new(fac, grad.inputs["Fac"])
    # lueur solaire : d = dot(dir, sun) ; g = 0.55 d^5 + 0.35 d^40, attenuee au-dessus de 20-37 deg
    dot = nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    links.new(nrm.outputs["Vector"], dot.inputs[0])
    dot.inputs[1].default_value = sun_bl
    d = _math(nodes, links, "MAXIMUM", dot.outputs["Value"], 0.0)
    g1 = _math(nodes, links, "MULTIPLY", _math(nodes, links, "POWER", d, 5.0), 0.55)
    g2 = _math(nodes, links, "MULTIPLY", _math(nodes, links, "POWER", d, 40.0), 0.40)
    g = _math(nodes, links, "ADD", g1, g2)
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.35
    mr.inputs["From Max"].default_value = 0.60
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    mr.clamp = True
    links.new(z, mr.inputs["Value"])
    # et pas de lueur sous l'horizon (raccord propre avec la face Dn)
    below = nodes.new("ShaderNodeMapRange")
    below.inputs["From Min"].default_value = -0.12
    below.inputs["From Max"].default_value = 0.0
    below.clamp = True
    links.new(z, below.inputs["Value"])
    gfac = _math(nodes, links, "MULTIPLY", _math(nodes, links, "MULTIPLY", g, mr.outputs[0]),
                 below.outputs[0], clamp=True)
    mix = nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    links.new(gfac, mix.inputs["Factor"])
    links.new(grad.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = hex_lin(PAL["glow"])
    bg = nodes.new("ShaderNodeBackground")
    links.new(mix.outputs[2], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    out = nodes.new("ShaderNodeOutputWorld")
    links.new(bg.outputs[0], out.inputs["Surface"])
    return w


def _cloud_material(sun_bl):
    m = bpy.data.materials.get("SKY_Cloud") or bpy.data.materials.new("SKY_Cloud")
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    geo = nodes.new("ShaderNodeNewGeometry")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geo.outputs["True Normal"], sep.inputs[0])
    fac = _math(nodes, links, "MULTIPLY_ADD", sep.outputs["Z"], 0.5)
    fac.node.inputs[2].default_value = 0.5
    r = _ramp(nodes, [(0.0, "cl_under"), (0.30, "cl_mid"), (0.62, "cl_top")], constant=True)
    links.new(fac, r.inputs["Fac"])
    dot = nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    links.new(geo.outputs["True Normal"], dot.inputs[0])
    dot.inputs[1].default_value = sun_bl
    step = _math(nodes, links, "GREATER_THAN", dot.outputs["Value"], 0.55)
    mix = nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    links.new(step, mix.inputs["Factor"])
    links.new(r.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = hex_lin(PAL["cl_sun"])
    em = nodes.new("ShaderNodeEmission")
    links.new(mix.outputs[2], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(em.outputs[0], out.inputs["Surface"])
    return m


def _make_cloud(name, rng, mat, coll):
    import bmesh
    bm = bmesh.new()
    n = rng.randint(3, 5)
    xs = sorted(rng.uniform(-1.0, 1.0) for _ in range(n))
    for i, x in enumerate(xs):
        center = abs(x) < 0.5
        rad = rng.uniform(0.55, 0.8) * (1.25 if center else 0.9)
        m = Matrix.Translation((x * 1.1, rng.uniform(-0.2, 0.2), rad * 0.25)) @ \
            Matrix.Diagonal((rad * 1.25, rad, rad * 0.8, 1)) @ \
            Matrix.Rotation(rng.uniform(0, 6.28), 4, "Z")
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0, matrix=m)
    # dessous plat
    zmin = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        if v.co.z < zmin + 0.35:
            v.co.z = zmin + 0.35 * 0.3
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def build_sky_warm(seed=7):
    scn = bpy.data.scenes.get(SCENE)
    if scn:
        for ob in list(scn.collection.all_objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        for c in list(scn.collection.children):
            bpy.data.collections.remove(c)
    else:
        scn = bpy.data.scenes.new(SCENE)
    coll = bpy.data.collections.new("SKY_Warm")
    scn.collection.children.link(coll)

    sun_bl = rb2bl(SUN_ROBLOX).normalized()
    scn.world = _world(sun_bl)
    mat = _cloud_material(sun_bl)

    # nuages : bande 7-28 deg, clairsemes, evitent le coeur de la lueur
    rng = random.Random(seed)
    sun_az = math.degrees(math.atan2(sun_bl.y, sun_bl.x))
    R = 1000.0
    k = 0
    azs = [i * 360 / 11 + rng.uniform(-10, 10) for i in range(11)]
    for az in azs:
        if abs(((az - sun_az + 180) % 360) - 180) < 22:
            continue
        el = rng.uniform(8, 24)
        size = rng.uniform(95, 150) * (1.0 - el / 90)
        ob = _make_cloud("SKY_Cloud_%02d" % k, rng, mat, coll)
        a, e = math.radians(az), math.radians(el)
        pos = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * R
        ob.location = pos
        ob.rotation_euler = (0, 0, a + math.pi / 2)
        ob.scale = (size, size * 0.8, size * 0.85)
        k += 1

    # cameras cubemap
    for face, (d, up) in FACES.items():
        f = rb2bl(d); u = rb2bl(up); r = f.cross(u)
        cd = bpy.data.cameras.new("SKY_Cam_" + face)
        cd.type = "PERSP"; cd.sensor_fit = "HORIZONTAL"; cd.angle = math.radians(90)
        cd.clip_start = 1.0; cd.clip_end = 5000.0
        cam = bpy.data.objects.new("SKY_Cam_" + face, cd)
        m = Matrix((r, u, -f)).transposed().to_4x4()
        cam.matrix_world = m
        coll.objects.link(cam)

    rs = scn.render
    try:
        rs.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        rs.engine = "BLENDER_EEVEE"
    rs.resolution_x = rs.resolution_y = 1024
    rs.resolution_percentage = 100
    rs.film_transparent = False
    rs.image_settings.file_format = "PNG"
    rs.image_settings.color_mode = "RGB"
    rs.image_settings.color_depth = "8"
    scn.view_settings.view_transform = "Standard"
    scn.view_settings.look = "None"
    scn.view_settings.exposure = 0.0
    scn.view_settings.gamma = 1.0
    try:
        scn.eevee.taa_render_samples = 16
    except Exception:
        pass
    return scn


def render_sky_warm(out_dir):
    import os
    scn = bpy.data.scenes[SCENE]
    win = bpy.context.window
    prev = win.scene
    win.scene = scn
    paths = []
    try:
        for face in FACES:
            scn.camera = bpy.data.objects["SKY_Cam_" + face]
            p = os.path.join(out_dir, "SKY_Warm_Skybox%s.png" % face)
            scn.render.filepath = p
            bpy.ops.render.render(write_still=True, scene=scn.name)
            paths.append(p)
    finally:
        win.scene = prev
    return paths
