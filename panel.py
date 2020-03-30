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

blender_resources_dir = "/Applications/blender.app/Contents/Resources/2.81"


bohrToAngs = 0.529

bpy.types.Scene.MyString = StringProperty(name="Path:",
    attr="xyz_path",# this a variable that will set or get from the scene
    description="simple file path",
    maxlen= 1024,
    default= "")#this set the text

bpy.types.Scene.MyString2 = StringProperty(name="Path:",
    attr="cube_path",# this a variable that will set or get from the scene
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
        #box.label(text="Import Molecule")
        box = layout.box()

        box.operator("object.xyz_path")
        box.prop(context.scene,"MyString")

        row = box.row()
        row.label(text="Style")
        row.prop(context.window_manager.toggle_buttons, 'style', expand=True)
        if context.window_manager.toggle_buttons.style != "vdw":
            row = box.row()
            row.label(text="Stick size")
            row.prop(context.window_manager.toggle_buttons, "stick_size", expand=True)
        # style = context.window_manager.style_toggle.style
        row = box.row()
        row.label(text="Shader")
        row.prop(context.window_manager.toggle_buttons, 'shader', expand=True)
        #shader = context.window_manager.shader_toggle.shader
        if context.window_manager.toggle_buttons.shader != "Diffuse":
            row = box.row()
            row.prop(context.window_manager.toggle_buttons, "roughness", expand=True)
        row = box.row()
        row.prop(context.window_manager.toggle_buttons, "carbon_color")
        row = box.row()

        row.prop(context.window_manager.toggle_buttons, "trajectory")

        row = box.row()
        row.prop(context.window_manager.toggle_buttons, "hbonds")
        if context.window_manager.toggle_buttons.hbonds:
            row = box.row()
            row.prop(context.window_manager.toggle_buttons, "hbond_color")
            row = box.row()
            row.prop(context.window_manager.toggle_buttons, "hbond_dist")
            row.prop(context.window_manager.toggle_buttons, "hbond_tresh")
        row = box.row()
        row.prop(context.window_manager.toggle_buttons, "charges")
        row = box.row()
        row.prop(context.window_manager.toggle_buttons, "vectors")
        if context.window_manager.toggle_buttons.vectors:
            row = box.row()
            row.prop(context.window_manager.toggle_buttons, "vector_color")
        row = box.row()
        row.operator("object.import_structure_button")

        layout.row().separator()

        box = layout.box()
        box.operator("object.cube_path")
        box.prop(context.scene,"MyString2")

        row = box.row()
        row.label(text="Isovalue")
        #row = box.row()
        row.prop(context.window_manager.toggle_buttons, "isovalue1")
        row.label(text="x 10^")
        row.prop(context.window_manager.toggle_buttons, "isovalue2")
        row = box.row()
        row.label(text="Shader")
        row.prop(context.window_manager.toggle_buttons, 'shader', expand=True)
        if context.window_manager.toggle_buttons.shader != "Diffuse":
            row = box.row()
            row.prop(context.window_manager.toggle_buttons, "roughness")
        row = box.row()
        row.prop(context.window_manager.toggle_buttons, "pos_color")

        row = box.row()
        row.prop(context.window_manager.toggle_buttons, "neg_color")

        row = box.row()
        row.prop(context.window_manager.toggle_buttons, "alpha_cube")
        row = box.row()
        row.operator("object.import_cube_button")

        layout.row().separator()
        box = layout.box()
        # automatic lightning
        # brightness
        row = box.row()
        row.label(text="General Settings")
        row = box.row()
        row.operator("object.automatic_ligthning_button")
        row = box.row()
        row.prop(context.window_manager.toggle_buttons, "weight1")
        row.prop(context.window_manager.toggle_buttons, "weight2")
        row = box.row()
        row.operator("object.lookdev_button")
        row.operator("object.rendered_button")

        row = box.row()


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
    stick_size : bpy.props.EnumProperty(
    items=[
        ('1', '1', 'Use small sticksize', '', 0),
        ('2', '2', 'Use medium sticksize', '', 1),
        ('3', '3', 'Use large sticksize', '', 2)
    ],
    default='2'
)
    shader : bpy.props.EnumProperty(
    items=[
        ('Diffuse', 'Diffuse', 'Use diffuse shader', '', 0),
        ('Glossy', 'Glossy', 'Use glossy shader', '', 1),
        ('Principled', 'Plastic', 'Use Principled BSDF shader', '', 2)
    ],
    default='Principled'
)

    shader_cube : bpy.props.EnumProperty(
    items=[
        ('Diffuse', 'Diffuse', 'Use diffuse shader', '', 0),
        ('Glossy', 'Glossy', 'Use glossy shader', '', 1),
        ('Principled', 'Plastic', 'Use Principled BSDF shader', '', 2)
    ],
    default='Principled'
)

    roughness : bpy.props.EnumProperty(
    items=[
        ("0.0", 'Glossy', 'Use roughness of 0.0', '', 0),
        ("0.3", 'Semi', 'Use roughness of 0.3', '', 1),
        ("0.5", 'Diffuse', 'Use roughness of 0.5', '', 2)
    ],
    default="0.3"
)

    roughness_cube : bpy.props.FloatProperty(name="Roughness", default=0, soft_min=0.0, soft_max=1.0,
                                        min=0.0, max=1.0)

    alpha_cube : bpy.props.FloatProperty(name="Transparency", default=0, soft_min=0.0, soft_max=1.0,
                                        min=0.0, max=1.0)

    carbon_color : bpy.props.FloatVectorProperty(
                                     name = "Carbon Color",
                                     subtype = "COLOR",
                                     size = 4,
                                     min = 0.0,
                                     max = 1.0,
                                     default = (0.1,0.1,0.1,1.0),
                                     description = "Color of carbon atoms"
                                     )

    hbonds : bpy.props.BoolProperty(name="Hydrogen Bonds")

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

    trajectory : bpy.props.BoolProperty(name="as Trajectory",
                description=" dasd" )

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

    isovalue1: bpy.props.FloatProperty(name="", default=2.0, soft_min=0.0, soft_max=10.0,
                                        min=0.0, max=10.0, description="""Isovalue for cube""")
    isovalue2: bpy.props.IntProperty(name="", default=-2, soft_min=-5, soft_max=2,
                                        min=-7, max=5, description="""Isovalue for cube""")

    pos_color : bpy.props.FloatVectorProperty(
                                     name = "Positive Color",
                                     subtype = "COLOR",
                                     size = 4,
                                     min = 0.0,
                                     max = 1.0,
                                     default = (0.0,0.0,1.0,1.0),
                                     description = "Color of carbon atoms"
                                     )

    neg_color : bpy.props.FloatVectorProperty(
                                     name = "Negative Color",
                                     subtype = "COLOR",
                                     size = 4,
                                     min = 0.0,
                                     max = 1.0,
                                     default = (0.9,0.0,0.0,1.0),
                                     description = "Color of negative lobe"
                                     )


    weight1: bpy.props.FloatProperty(name="", default=0.95, soft_min=0.0, soft_max=1.0,
                                        min=-2.0, max=2.0, description="""Weight of studiolights""")

    weight2: bpy.props.FloatProperty(name="", default=0.1, soft_min=0.0, soft_max=1.0,
                                        min=-2.0, max=2.0, description="""Weight of studiolights""")

class OBJECT_OT_import_structure_button(bpy.types.Operator):
    bl_idname = "object.import_structure_button"
    bl_label = "Import Structure"
    __doc__ = "Simple Custom Button"

    def invoke(self, context, event):
        #when the button is press it print this to the log
        print("Load Molecule")
        print("path:",bpy.context.scene.MyString)
        import sys
        sys.path.append(blender_resources_dir + "/scripts/addons/qblend/")
        from lib.io import XyzFile
        from .molecule import Molecule
        from .base import Object
        from .meshes import Cube, UVsphere

        #object = Cube()
        #object2 = UVsphere()
        #from .Blender import clear_objects, save_blend, render_image

        s_size = [0.15, 0.2, 0.25]
        stick_size = int(context.window_manager.toggle_buttons.stick_size)
        stick_size = s_size[stick_size-1]
        style = context.window_manager.toggle_buttons.style
        shader = context.window_manager.toggle_buttons.shader
        roughness = context.window_manager.toggle_buttons.roughness

        traj = context.window_manager.toggle_buttons.trajectory

        bmol = Molecule(auto_bonds=True, align_com = True, atom_scale=1.)
        bmol.options.atom_scale = 1.0
        #reader = XyzFile("/Users/hochej/14.xyz", "r")
        reader = XyzFile(bpy.context.scene.MyString)
        if shader == "Diffuse":
            shader = "Principled"
        bmol.options.shader = shader
        bmol.options.stick_size = stick_size
        bmol.options.roughness = float(roughness)
        if style == "vdw":
            bmol.options.atom_size = "vdw_radius"
        bmol.options.carbon_color = context.window_manager.toggle_buttons.carbon_color
        read_status = reader.read(bmol)
        print("BEGIN0")
        bmol.add_repr(style)
        print("BEGIN")
        bmol.create()

        if traj:
            while(read_status):
                read_status = reader.read(bmol)
                bmol.update()


        return{'FINISHED'}


class OBJECT_OT_import_cube_button(bpy.types.Operator):
    bl_idname = "object.import_cube_button"
    bl_label = "Import Cube File"
    __doc__ = "Simple Custom Button"

    def invoke(self, context, event):
        #when the button is press it print this to the log
        print("Load Molecule")
        print("pat
        h:",bpy.context.scene.MyString2)
        import sys
        sys.path.append(blender_resources_dir + "/scripts/addons/qblend/")
        from lib.io import XyzFile
        from .molecule import Molecule
        from .base import Object
        from .meshes import Cube, UVsphere
        from lib.io import CubeFile

        s_size = [0.15, 0.2, 0.25]
        stick_size = int(context.window_manager.toggle_buttons.stick_size)
        stick_size = s_size[stick_size-1]
        style = context.window_manager.toggle_buttons.style
        shader = context.window_manager.toggle_buttons.shader
        roughness = float(context.window_manager.toggle_buttons.roughness)
        shader_c = context.window_manager.toggle_buttons.shader_cube
        roughness_c = float(context.window_manager.toggle_buttons.roughness_cube)
        isovalue1  = context.window_manager.toggle_buttons.isovalue1
        isovalue2 = context.window_manager.toggle_buttons.isovalue2
        iso1 = isovalue1 * 10**(isovalue2)

        bmol = Molecule(auto_bonds=True, align_com = True)
        bmol.options.stick_size = stick_size
        bmol.options.atom_scale = 1.0
        bmol.options.shader = shader
        bmol.options.roughness = 0.1#roughness
        if style == "vdw":
            bmol.options.atom_size = "vdw_radius"
        bmol.options.carbon_color = context.window_manager.toggle_buttons.carbon_color
        bmol.add_repr(style)
        bmol.options.shader = shader_c
        bmol.options.roughness = 0.1# roughness_c
        reprTD = bmol.add_repr('isosurface', "TD", "CubeData", [iso1, -iso1],
                                draw_box=False, on_update='remove')


        bmol.create()
        for i in range(2):
            cube = CubeFile(bpy.context.scene.MyString2)
            cube.read(bmol)
            bmol.update()

        #bmol.create()
        return{'FINISHED'}


class OBJECT_OT_automatic_ligthning_button(bpy.types.Operator):
    bl_idname = "object.automatic_ligthning_button"
    bl_label = "Use Studiolights"
    __doc__ = "Simple Custom Button"

    def invoke(self, context, event):
        #when the button is press it print this to the log
        import sys
        sys.path.append(blender_resources_dir + "/scripts/addons/qblend/")

        world_tree = bpy.data.worlds[0].node_tree
        w_out = world_tree.nodes['World Output']
        mixer = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeMixShader")
        mixer2 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeMixShader")
        mixer3 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeMixShader")
        env = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeTexEnvironment")
        env2 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeTexEnvironment")
        env3 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeTexEnvironment")
        bg1 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeBackground")
        bg2 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeBackground")
        bg3 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeBackground")
        bg4 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeBackground")
        value1 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeValue")
        value2 = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeValue")

        light_p = bpy.data.worlds[0].node_tree.nodes.new(type="ShaderNodeLightPath")

        world_tree.links.new(light_p.outputs['Is Camera Ray'], mixer.inputs[0])
        world_tree.links.new(value1.outputs['Value'], mixer2.inputs[0])
        world_tree.links.new(value2.outputs['Value'], mixer3.inputs[0])
        world_tree.links.new(bg1.outputs["Background"], mixer2.inputs[1])
        world_tree.links.new(bg3.outputs["Background"], mixer3.inputs[1])
        world_tree.links.new(bg4.outputs["Background"], mixer3.inputs[2])
        world_tree.links.new(env2.outputs['Color'], bg3.inputs['Color'])
        world_tree.links.new(env3.outputs['Color'], bg4.inputs['Color'])

        world_tree.links.new(mixer3.outputs['Shader'], mixer2.inputs[2])
        world_tree.links.new(mixer2.outputs['Shader'], mixer.inputs[1])
        world_tree.links.new(bg2.outputs["Background"], mixer.inputs[2])
        world_tree.links.new(mixer.outputs['Shader'], w_out.inputs['Surface'])
        world_tree.links.new(env.outputs['Color'], bg1.inputs['Color'])

        w1 = context.window_manager.toggle_buttons.weight1
        w2 = context.window_manager.toggle_buttons.weight2
        value1.outputs['Value'].default_value = w1
        value2.outputs['Value'].default_value = w2


        a = 0.035
        bg2.inputs['Color'].default_value = [a, a, a, 1.]

        path = blender_resources_dir + "/datafiles/studiolights/world/forest.exr"
        env.image = bpy.data.images.load(path)
        path = blender_resources_dir + "/datafiles/studiolights/world/studio.exr"
        env2.image = bpy.data.images.load(path)
        path = blender_resources_dir + "/datafiles/studiolights/world/night.exr"
        env3.image = bpy.data.images.load(path)

        #bpy.context.scene.render.alpha_mode = 'TRANSPARENT'

        return{'FINISHED'}


class OBJECT_OT_lookdev_button(bpy.types.Operator):
    bl_idname = "object.lookdev_button"
    bl_label = "Material View"
    __doc__ = "Simple Custom Button"

    def invoke(self, context, event):
        #when the button is press it print this to the log
        area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
        space = next(space for space in area.spaces if space.type == 'VIEW_3D')
        space.shading.type = 'MATERIAL'  # set the viewport shading

        return{'FINISHED'}

class OBJECT_OT_rendered_button(bpy.types.Operator):
    bl_idname = "object.rendered_button"
    bl_label = "Rendered View"
    __doc__ = "Simple Custom Button"

    def invoke(self, context, event):
        #when the button is press it print this to the log
        area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
        space = next(space for space in area.spaces if space.type == 'VIEW_3D')
        space.shading.type = 'RENDERED'  # set the viewport shading

        return{'FINISHED'}



class OBJECT_OT_xyz_path(bpy.types.Operator):
    bl_idname = "object.xyz_path"
    bl_label = "Select xyz Files"
    __doc__ = ""


    filename_ext = ".xyz"
    filter_glob : StringProperty(default="*.xyz", options={'HIDDEN'})


    #this can be look into the one of the export or import python file.
    #need to set a path so so we can get the file name and path
    filepath : StringProperty(name="File Path", description="Filepath files", maxlen= 1024, default= "")
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
        self.layout.box().operator('file.select_all_toggle')
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class OBJECT_OT_cube_path(bpy.types.Operator):
    bl_idname = "object.cube_path"
    bl_label = "Select Cube Files"
    __doc__ = ""


    filename_ext = ".cube"
    filter_glob : StringProperty(default="*.cub*", options={'HIDDEN'})


    #this can be look into the one of the export or import python file.
    #need to set a path so so we can get the file name and path
    filepath : StringProperty(name="File Path", description="Filepath files", maxlen= 1024, default= "")
    files : CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
        )
    def execute(self, context):
        #set the string path fo the file here.
        #this is a variable created from the top to start it
        bpy.context.scene.MyString2 = self.properties.filepath


        print("*************SELECTED FILES ***********")
        for file in self.files:
            print(file.name)

        print("FILEPATH %s"%self.properties.filepath)#display the file name and current path
        return {'FINISHED'}

    def draw(self, context):
        self.layout.box().operator('file.select_all_toggle')
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}
