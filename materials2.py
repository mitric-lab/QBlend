from .base import LazyMaterial
from .utils import *

Colors = {
    'white':    (1., 1., 1.),
    'black':    (.0, .0, .0),
    'darkgrey':     (.2, .2, .2),
    'grey':     (.35, .35, .35),
    'lightgrey':     (.8, .8, .8),
    'silver':   (.6, .6, .6),

    # redish
    'red':      (1., 0., 0.),
    'darkred':  (.67, .06, .07),
    'pink':     (.93, .63, .63),
    'purple':   (.55, .07, .56),
    'mauve':    (.82, .44, .68),
    'magenta':      (.76, .09, .78),
    'magentared':   (.84, .09, .60),

    # yellowish
    'yellow':       (1., 1., .0),
    'orange':       (.7, .4, 0.),
    'darkyellow':   (.8, .7, .1),
    'yellowgreen':  (.59, .85, .18),
    'ochre':        (.46, .30, .08),
    'tan':          (.49, .49, .27),
    'gold':         (.69, .56, .22),

     # greenish
    'green':        (0., 1., 0.),
    'darkgreen':    (.14, .81, .15),
    'greenblue':    (.15, .82, .51),
    'lime':         (.56, .85, .47),
    'cyan':         (.34, .71, .70),
    'lightcyan':    (.15, .82, .89),
    'darkcyan':     (.14, .71, .87),

    # blueish
    'blue':         (0., 0., 1.),
    'greyblue':     (.09, .36, .57),
    'darkblue':     (.03, .07, .73),
    'ice':          (.51, .51, .69),
    'violet':       (.24, .05, .78),
    }


def make_material(name, color=(0., 0., 1.), shader="Diffuse", roughness=0.0):
    if shader == "Diffuse":
        roughness = 0.5
    r = str(np.round(roughness, decimals=2))
    name = name + "_" + shader + "_" + r
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name) # create new material
    mat.use_nodes = True # use nodes
    mat.node_tree.nodes.remove(mat.node_tree.nodes[1]) # delete default principled shader
    shader = mat.node_tree.nodes.new(type="ShaderNodeBsdf"+shader) # create new node
    shader.inputs[0].default_value = color
    shader.inputs['Roughness'].default_value = roughness
    mat_input = mat.node_tree.nodes.get("Material Output").inputs[0]
    mat.node_tree.links.new(shader.outputs["BSDF"], mat_input)
    return mat


def make_glas_material(name, **kw):
    mat = {
        'name': name,
        'emit': 0.32,
        'specular_intensity': 1.,
        'specular_hardness': 500,
        'diffuse_shader': 'OREN_NAYAR',
        'translucency': .153,
        'use_transparency': True,
        'alpha': 0.5,
        'transparency_method': 'RAYTRACE',
        'raytrace_transparency': {'ior': 1.51, 'depth_max': 3, 'fresnel': 3. }
        }

    for k, v in mat.items():
        kw[k] = v if k not in kw else kw[k]

    return make_lazy_material(**kw)



Materials = {
    'Glas': make_glas_material('Glas')
    }

def getColor(name, default = (.35, .35, .35)):
    return Colors[name] if name in Colors else default
