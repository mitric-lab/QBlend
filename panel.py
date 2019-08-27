import bpy
from bpy.props import *
import mathutils
import itertools
from mathutils import Vector
import numpy as np
from . import molecule
from . import atom
import time

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

class xyz2blender:
    stickradius=0.25

    def __init__(self, structure):
        self.structure=structure
        mol_name = self.structure.filename.split("/")[-1][:-4] # name of the xyz file
        self.mol_coll = bpy.data.collections.new(mol_name) # create a new collection with xyz filename
        bpy.context.scene.collection.children.link(self.mol_coll) # link new collection to scene
        layer_collection = bpy.context.view_layer.layer_collection # get layer collections
        layerColl = recurLayerCollection(layer_collection, self.mol_coll.name) # search recursively for molecule collection
        bpy.context.view_layer.active_layer_collection = layerColl # make molecule collection active
        self.scene = bpy.context.scene
        self.style = bpy.context.window_manager.toggle_buttons.style
        self.shader = bpy.context.window_manager.toggle_buttons.shader
        self.roughness = bpy.context.window_manager.toggle_buttons.roughness

    def add_atom(self, symbol, atomsize):
        #bpy.ops.mesh.primitive_cube_add(size=atomsize)
        #obj = bpy.context.active_object
        #obj.modifiers.new(type="SUBSURF", name="subsurf")
        #obj.modifiers["subsurf"].levels = 4
        #obj.modifiers["subsurf"].render_levels = 6
        #obj.modifiers.new(type="CAST", name="cast")
        #obj.modifiers["cast"].factor = 1.
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(radius=atomsize)
        obj = bpy.context.active_object
        obj.data.name = symbol.upper()
        bpy.data.curves[symbol.upper()].resolution_u = 8
        bpy.data.curves[symbol.upper()].resolution_v = 8
        if symbol.upper() == "C":
            material = makeMat(symbol, bpy.context.window_manager.toggle_buttons.carbon_color,
                               self.shader, self.roughness)
        else:
            material = makeMat(symbol, atom.atomcolors[symbol], self.shader, self.roughness)
        obj.active_material = material
        bpy.ops.object.shade_smooth()
        return obj

    def get_atomsize(self, symbol, representation):
        if representation == "licorice":
            return atom.stickradius #* 2 * 0.97
        elif representation == "cpk" and symbol.upper() == "H":
            return atom.stickradius #* 2 * 0.97
        elif representation == "cpk" and symbol.upper() != "H":
            return atom.stickradius * 2#4
        elif representation == "vdW":
            return atom.vdw_radius[symbol]

    def copy_object(self, obj):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.duplicate_move_linked()
        obj = bpy.context.selected_objects[0]
        return obj

    def copy_atom(self, ref_obj):
        obj = bpy.data.objects.new("Atom", ref_obj.data)
        bpy.context.collection.objects.link(obj)
        #obj.hide_select = True
        return obj

    def copy_bond(self, ref_obj):
        obj = bpy.data.objects.new("Bond", ref_obj.data)
        bpy.context.collection.objects.link(obj)
        return obj

    def get_stickradius(self, symbol, representation):
        if representation == "licorice":
            return atom.stickradius
        elif representation == "cpk":
            return atom.stickradius * 0.5
        elif representation == "vdW":
            return None

    def add_bond(self, symbol, stickradius):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=stickradius, depth=1, end_fill_type="NOTHING")
        obj = bpy.context.active_object
        obj.modifiers.new(type="SUBSURF", name="subsurf")
        obj.modifiers["subsurf"].levels = 4
        obj.modifiers["subsurf"].render_levels = 6
        material = makeMat(symbol, atom.atomcolors[symbol], self.shader, self.roughness)
        obj.active_material = material
        bpy.ops.object.shade_smooth()
        return obj

    def blenderstructure(self):
        created_elements = []
        atom_objects = {}
        join_objects = {}
        element_offset = {}
        created_elem_bonds = []
        ref_bond_objects = {}
        ref_bond_locations = {}
        ref_bond_orig = {}
        ref_bond_rotmat = {}
        ref_bond_scales = {}
        time_a = time.time()
        flag = True
        bpy.context.space_data.overlay.show_relationship_lines = False
        bpy.ops.object.empty_add(type='SPHERE', view_align=False)
        empty_sphere = bpy.context.active_object
        bpy.ops.object.empty_add(type='ARROWS', view_align=False)
        empty_arrows = bpy.context.active_object
        empty_arrows.hide_select = True
        #empty_arrows.scale = [3, 3, 3]
        for i in range(len(self.structure.atomlist)):
            atom_symbol = self.structure.atomlist[i].symbol
            if atom_symbol not in created_elements:
                flag = True
                a_size = self.get_atomsize(atom_symbol, self.style)
                obj = self.add_atom(atom_symbol, a_size)
                created_elements.append(atom_symbol)
                atom_objects[atom_symbol] = obj
            else:
                flag = False

            obj = self.copy_atom(atom_objects[atom_symbol])
            obj.parent = empty_sphere
            obj.location = self.structure.atomlist[i].xyz.ang



        for sym in created_elements:
            bpy.data.objects.remove(atom_objects[sym], do_unlink=True)
        print(time.time() - time_a)
        """
        for p in self.structure.graph.getPairs(1):
            vec1 = mathutils.Vector(self.structure.atomlist[p[0]].xyz.ang)
            vec2 = mathutils.Vector(self.structure.atomlist[p[1]].xyz.ang)
            vec = vec2 - vec1
            axis = mathutils.Vector([0,0,1]).cross(vec)
            angle = mathutils.Vector([0,0,1]).angle(vec)
            rot_mat = mathutils.Matrix.Rotation(angle,4,axis)
            for j in p:
                atom_symbol = self.structure.atomlist[j].symbol
                translation_vector = ((vec1+vec2)*0.5+mathutils.Vector(self.structure.atomlist[j].xyz.ang))*0.5
                if atom_symbol not in created_elem_bonds:
                    s_radius = self.get_stickradius(atom, self.style)
                    obj = self.add_bond(atom_symbol, s_radius)
                    ref_bond_locations[atom_symbol] = translation_vector
                    ref_bond_scales[atom_symbol] = vec.length * 0.5
                    ref_bond_objects[atom_symbol] = obj
                    ref_bond_rotmat[atom_symbol] = rot_mat
                    created_elem_bonds.append(atom_symbol)
                else:
                    obj = self.copy_object(ref_bond_objects[atom_symbol])
                    orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
                    orig_loc_mat = mathutils.Matrix.Translation(orig_loc)
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    obj.matrix_world = orig_loc_mat @ rot_mat
                    bpy.ops.transform.translate(value=translation_vector)
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.delta_scale[2] = vec.length * 0.5

        for symbol in created_elem_bonds:
            obj = ref_bond_objects[symbol]
            orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
            orig_loc_mat = mathutils.Matrix.Translation(orig_loc)
            obj.matrix_world = orig_loc_mat @ ref_bond_rotmat[symbol]
            obj.select_set(True)
            bpy.ops.transform.translate(value=ref_bond_locations[symbol])
            bpy.ops.object.select_all(action='DESELECT')
            obj.delta_scale[2] = ref_bond_scales[symbol]
        """
        """
        hydrogendist = 1.8
        for p in itertools.combinations(range(self.structure.natoms), 2):
            atompair = [self.structure.atomlist[p[0]].symbol,self.structure.atomlist[p[1]].symbol]
            if "O" in atompair and "H" in atompair:
                vec1 = mathutils.Vector(self.structure.atomlist[p[0]].xyz.ang)
                vec2 = mathutils.Vector(self.structure.atomlist[p[1]].xyz.ang)
                vec = vec2-vec1
                if self.structure.atomlist[p[atompair.index("H")]].neigh_sym[0] != "C" and abs(vec.length-hydrogendist)<=0.20*hydrogendist:
                    n=6
                    for i in range(1,n):
                        me = bpy.ops.mesh.primitive_cylinder_add(radius=atom.stickradius*0.8,depth=vec.length*0.1,end_fill_type="NGON")
                        setMaterial(bpy.context.object, matHbond)
                        bpy.ops.object.shade_smooth()
                        axis=mathutils.Vector([0,0,1]).cross(vec)
                        angle=mathutils.Vector([0,0,1]).angle(vec)
                        rot_mat=mathutils.Matrix.Rotation(angle,4,axis)
                        obj = bpy.context.active_object
                        orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
                        orig_loc_mat = mathutils.Matrix.Translation(orig_loc)
                        obj.matrix_world = orig_loc_mat * rot_mat
                        bpy.ops.transform.translate(value=vec1+i*(1./(n))*vec)
        """

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
        ('licorice', 'Licorice', 'Use stick representation', '', 1),
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
        structureobject = molecule.structure(bpy.context.scene.MyString)
        structureobject.readXYZ()
        structureobject.getAdjacency()
        xyz2blenderobject = xyz2blender(structureobject)
        xyz2blenderobject.blenderstructure()
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
