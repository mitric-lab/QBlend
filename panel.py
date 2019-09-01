import bpy
from bpy.props import *
import mathutils
import itertools
from mathutils import Vector
import numpy as np
import time

#from . import Blender
#from . import materials, meshes, curves, collections
#from .base import Object, Material, LazyMaterial, Empty

#from .molecule import Molecule
#from .marching_cube import triangulate

bohrToAngs = 0.529

bpy.types.Scene.MyString = StringProperty(name="Path:",
    attr="xyz_path",# this a variable that will set or get from the scene
    description="simple file path",
    maxlen= 1024,
    default= "")#this set the text


bpy.types.Scene.MyPath = StringProperty(name="file path",
    attr="xyz_path",# this a variable that will set or get from the scene
    description="simple file path",
    maxlen= 1024,
    subtype='FILE_PATH',
    default= "")#this set the text

def makeMat(name, color, shader, roughness=0.0):
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

def recurLayerCollection(layerColl, collName):
    found = None
    if (layerColl.name == collName):
        return layerColl
    for layer in layerColl.children:
        found = recurLayerCollection(layer, collName)
        if found:
            return found


class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        return True#(context.object is not None)


class PANEL_PT_molecule_panel(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_test_1"
    bl_label = "Molecule"

    def draw(self, context):
        layout = self.layout
        #layout.label(text="Import Molecule")
        box = layout.box()

        box.operator("object.xyz_path")
        box.prop(context.scene,"MyString")

        row = layout.row()
        row.label(text="Style")
        row.prop(context.window_manager.toggle_buttons, 'style', expand=True)
        # style = context.window_manager.style_toggle.style
        row = layout.row()
        row.label(text="Shader")
        row.prop(context.window_manager.toggle_buttons, 'shader', expand=True)
        #shader = context.window_manager.shader_toggle.shader
        if context.window_manager.toggle_buttons.shader != "Diffuse":
            row = layout.row()
            row.prop(context.window_manager.toggle_buttons, "roughness")
        row = layout.row()
        row.prop(context.window_manager.toggle_buttons, "carbon_color")
        row = layout.row()
        row.prop(context.window_manager.toggle_buttons, "hbonds")
        if context.window_manager.toggle_buttons.hbonds:
            row = layout.row()
            row.prop(context.window_manager.toggle_buttons, "hbond_color")
            row = layout.row()
            row.prop(context.window_manager.toggle_buttons, "hbond_dist")
            row.prop(context.window_manager.toggle_buttons, "hbond_tresh")
        row = layout.row()
        row.prop(context.window_manager.toggle_buttons, "charges")
        row = layout.row()
        row.prop(context.window_manager.toggle_buttons, "vectors")
        if context.window_manager.toggle_buttons.vectors:
            row = layout.row()
            row.prop(context.window_manager.toggle_buttons, "vector_color")
        row = layout.row()
        row.operator("object.import_structure_button")


class ToggleButtons(bpy.types.PropertyGroup):
    # (unique identifier, property name, property description, icon identifier, number)
    style : bpy.props.EnumProperty(
    items=[
        ('cpk', 'CPK', 'Use ball-stick representation', '', 0),
        ('stick', 'Licorice', 'Use stick representation', '', 1),
        ('vdw', 'vdW', 'Use van-der-Waals representation', '', 2)
    ],
    default='cpk'
)
    shader : bpy.props.EnumProperty(
    items=[
        ('Diffuse', 'Diffuse', 'Use diffuse shader', '', 0),
        ('Glossy', 'Glossy', 'Use glossy shader', '', 1),
        ('Principled', 'Plastic', 'Use Principled BSDF shader', '', 2)
    ],
    default='Diffuse'
)
    carbon_color : bpy.props.FloatVectorProperty(
                                     name = "Carbon Color",
                                     subtype = "COLOR",
                                     size = 4,
                                     min = 0.0,
                                     max = 1.0,
                                     default = (0.3,0.3,0.3,1.0),
                                     description = "Color of carbon atoms"
                                     )

    hbonds : bpy.props.BoolProperty(name="Hydrogen Bonds")
    roughness : bpy.props.FloatProperty(name="Roughness", default=0, soft_min=0.0, soft_max=1.0,
                                        min=0.0, max=1.0)
    hbond_color : bpy.props.FloatVectorProperty(
                                     name = "H-Bond Color",
                                     subtype = "COLOR",
                                     size = 4,
                                     min = 0.0,
                                     max = 1.0,
                                     default = (0.9,0.5,0.1,1.0),
                                     description = "Color of hydrogen bonds"
                                     )

    hbond_dist : bpy.props.FloatProperty(name="Length", default=1.8, soft_min=1.5, soft_max=3.,
                                        min=0.0, max=10.0, description="""Length of the hydrogen bonds. All possible
                                        hydrogens are found, which are in the range of Length +/- Threshold""")

    hbond_tresh: bpy.props.FloatProperty(name="Threshold", default=0.1, soft_min=0.0, soft_max=2.0,
                                        min=0.0, max=5.0, description="""Threshold of the hydrogen bonds. All possible
                                        hydrogens are found, which are in the range of Length +/- Threshold""")

    vector_color : bpy.props.FloatVectorProperty(
                                     name = "Vector Color",
                                     subtype = "COLOR",
                                     size = 4,
                                     min = 0.0,
                                     max = 1.0,
                                     default = (0.9,0.,0.,1.0),
                                     description = "Color of vector arrows (Principled Shader)"
                                     )

    charges : bpy.props.BoolProperty(name="Read and Show Charges",
                description="""Expects the following type of xyz file:
                [NUMBER OF ATOMS]

                SYMBOL   X_COORD   Y_COORD   Z_COORD   CHARGE
                ....""")
    vectors : bpy.props.BoolProperty(name="Read and Show Vectors",
                description="""Expects the following type of xyz file:
                [NUMBER OF ATOMS]

                SYMBOL   X_COORD   Y_COORD   Z_COORD
                ...
                SYMBOL   X_COORD   Y_COORD   Z_COORD
                X_VALUE   Y_VALUE   Z_VALUE
                ... (for each atom 1 vector)""")

class OBJECT_OT_import_structure_button(bpy.types.Operator):
    bl_idname = "object.import_structure_button"
    bl_label = "Import Structure"
    __doc__ = "Simple Custom Button"

    def invoke(self, context, event):
        #when the button is press it print this to the log
        print("Load Molecule")
        print("path:",bpy.context.scene.MyString)
        import sys
        sys.path.append("/Applications/blender.app/Contents/Resources/2.80/scripts/addons/qblend/")
        from lib.io import XyzFile
        from .molecule import Molecule
        from .base import Object
        from .meshes import Cube, UVsphere

        #object = Cube()
        #object2 = UVsphere()
        #from .Blender import clear_objects, save_blend, render_image

        style = context.window_manager.toggle_buttons.style
        shader = context.window_manager.toggle_buttons.shader
        roughness = context.window_manager.toggle_buttons.roughness

        bmol = Molecule(auto_bonds=True, align_com = False, atom_scale=1.)
        reader = XyzFile("/Users/hochej/14.xyz", "r")
        bmol.options.shader = shader
        bmol.options.roughness = roughness
        if style == "vdw":
            bmol.options.atom_size = "vdw_radius"
        reader.read(bmol)
        print("BEGIN0")
        bmol.add_repr(style)
        print("BEGIN")
        bmol.create()

        return{'FINISHED'}

class OBJECT_OT_xyz_path(bpy.types.Operator):
    bl_idname = "object.xyz_path"
    bl_label = "Select xyz Files"
    __doc__ = ""


    filename_ext = ".xyz"
    filter_glob : StringProperty(default="*.xyz", options={'HIDDEN'})


    #this can be look into the one of the export or import python file.
    #need to set a path so so we can get the file name and path
    filepath : StringProperty(name="File Path", description="Filepath iles", maxlen= 1024, default= "")
    files : CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
        )
    def execute(self, context):
        #set the string path fo the file here.
        #this is a variable created from the top to start it
        bpy.context.scene.MyString = self.properties.filepath


        print("*************SELECTED FILES ***********")
        for file in self.files:
            print(file.name)

        print("FILEPATH %s"%self.properties.filepath)#display the file name and current path
        return {'FINISHED'}


    def draw(self, context):
        self.layout.operator('file.select_all_toggle')
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}
