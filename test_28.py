import bpy 
from bpy.props import *
import mathutils
import itertools
from mathutils import Vector
import numpy as np


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
       
# Global data for molecule visualization
isothreshold=0.10
spheresubdivisions=5
covalentradii={"B":0.77,"C":0.77,"H":0.37,"N":0.77,"O":0.77,"Zn":1.50,"S":1.50,"19":1.50,"13":1.50,"22":1.50,"21":1.50,"30":1.50/0.529,"14":1.50/0.529}
atomicradii={"H":0.7,"B":1.50,"C":1.50,"N":1.50,"Zn":2,"O":1.50,"79":2.00,"S":1.50,"19":2.00,"13":2.00,"22":2.00,"21":2.00,"14":2.00}
stickradius=0.25

atomicradii = atomicradii.fromkeys(atomicradii, stickradius)
 
"""
materials={"H":makeMat("H", (0.7, 0.7, 0.7)),"B":makeMat("B", (0., 0.9, 0.)),
           "C":makeMat("C", (0.2, 0.2, 0.2)),"N":makeMat("N", (0., 0., 1.)), 
           "O":makeMat("O", (1., 0., 0.)),"Si":makeMat("Si", (238.0/256, 180.0/256, 34.0/256)),
           "S":makeMat("S", (228.0/255.0, 202.0/255.0, 66.0/255.0)),
           "Zn":makeMat("Zn", (0.4, 0.4, 0.4))}
"""

atomcolors = {"H":(0.7, 0.7, 0.7, 1),
              "B":(0., 0.9, 0., 1),
              "C":(0.2, 0.2, 0.2, 1),
              "N":(0., 0., 1., 1), 
              "O":(1., 0., 0., 1),
              "Si":(238.0/256, 180.0/256, 34.0/256, 1),
              "S":(228.0/255.0, 202.0/255.0, 66.0/255.0, 1),
              "Zn":(0.4, 0.4, 0.4, 1)}

class coord(object):
    def __init__(self, x, unit="ang"):
        x = np.array(x)
        if unit == "au":
            self.x = x
        if unit == "angs":
            self.x = x / bohrToAngs
        if unit == "pm":
            self.x = x / bohrToAngs / 100
        if unit == "nm":
            self.x = x / bohrToAngs * 10

    @property
    def au(self):
        return self.x

    @property
    def ang(self):
        return self.x * bohrToAngs

    @property
    def pm(self):
        return self.x * bohrToAngs * 100.

    @property
    def nm(self):
        return self.x * bohrToAngs * 0.1

    def __sub__(self, other):
        return coord(self.x - other.x, unit="au")

class atom(object):
    rcov = {"C": 0.77, "H": 0.37, "O":0.73, "N":0.71, "S":0.75}
    atomic_number = {"H": 1, "C": 6, "N": 7, "O": 8, "S":16}

    def __init__(self, s, c, charge=0):
        self.symbol = s
        self.xyz = c
        self.charge = charge
        self.isaromatic = False
        self.label = None
        self.group = None

    @property
    def isAromatic(self):
        self.isaromatic = True

    def getRcov(self):
        return coord(self.rcov[self.symbol], unit="angs").au

    @property
    def color(self):
        return self.atomcolor[self.symbol]

    def getDistance(self, other):
        d = self.xyz.au - other.xyz.au
        return np.sqrt(np.dot(d, d))

    def setConnectivity(self, conn, neighb, sym):
        self.conn = conn
        self.neighbors = neighb
        self.neigh_sym = sym

    def bonding(self, other):
        bondtreshold = 0.25
        dist = self.getDistance(other)
        sum_rcov = self.getRcov() + other.getRcov()
        if abs(dist - sum_rcov) <= bondtreshold * sum_rcov:
            return True
        else:
            return False

    @property
    def number(self):
        return self.atomic_number[self.symbol]

    def __lt__(self, other):
         return self.number < other.number

    def __str__(self):
        return self.symbol

class graph:
    def __init__(self, dim):
        self.dim = dim
        self.adj = np.zeros((dim, dim))
        self.nodes = range(dim)

    def __getitem__(self, idx):
        return list(np.nonzero(self.adj[idx])[0])

    def setPower(self, n):
        self.pow = []
        for i in range(n):
            self.pow.append(self.getPower(i))

    def setPairs(self, n):
        self.pairs = []
        for i in range(n):
            self.pairs.append(self.getPairs(i))

    def setReachability(self, n):
        self.reachable = []
        mat = np.zeros((self.dim, self.dim))
        for i in range(n):
            mat = np.copy(mat) + self.pow[i]
            mat[mat > 1] = 1
            self.reachable.append(mat)

    def getIsReachable(self, i, j, n):
        return bool(self.reachable[n][i, j])

    def getPairs(self, n):
        mat = np.triu(self.pow[n]) - np.diag(np.diag(self.pow[n]))
        mat = mat - (1000 * self.reachable[n-1])
        mat[mat < 0] = 0
        return np.transpose(mat.nonzero())

    def getPower(self, n):
        if n ==0:
            return np.identity(self.dim)
        if n == 1:
            return self.adj
        else:
            mat = np.copy(self.adj)
            for i in range(1, n):
                mat = np.dot((self.adj), mat)
            return mat

class structure:
    def __init__(self,filename):
        self.filename = filename
        self.atomlist = []
        self.coord = []
        self.atomtypes = []
        
    def readXYZ(self):
        with open(self.filename, "r") as f:
            for line in f:
                tmp = line.split()
                if len(tmp) == 4:
                    self.atomlist.append(atom(tmp[0], coord(np.array(tmp[1:], dtype=float),
                                                            unit="angs")))
        self.natoms = len(self.atomlist)
            
    def getAdjacency(self):
        self.graph = graph(self.natoms)
        for pair in itertools.combinations(range(self.natoms), 2):
            if self.atomlist[pair[0]].bonding(self.atomlist[pair[1]]):
                self.graph.adj[pair[0], pair[1]] = 1
                self.graph.adj[pair[1], pair[0]] = 1
        self.graph.setPower(3)
        self.graph.setReachability(3)
        for idx, atom in enumerate(self.atomlist):
            syms = [at.symbol for at in np.array(self.atomlist)[self.graph[idx]]]
            atom.setConnectivity(len(self.graph[idx]), self.graph[idx], syms)
            
            
class xyz2blender:
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

    def blenderstructure(self):
        scale_cs = 2*0.97 # scaling factor between atom and bond size
        for i in range(len(self.structure.atomlist)): 
            bpy.ops.mesh.primitive_cube_add(size=scale_cs*stickradius)
            obj = bpy.context.active_object
            obj.modifiers.new(type="SUBSURF", name="subsurf")
            obj.modifiers["subsurf"].levels = 4
            obj.modifiers["subsurf"].render_levels = 6
            obj.modifiers.new(type="CAST", name="cast")
            obj.modifiers["cast"].factor = 1.
            #bpy.ops.object.modifier_apply(apply_as="DATA", modifier="subsurf")
            #bpy.ops.object.modifier_apply(apply_as="DATA", modifier="cast")
            material = makeMat(self.structure.atomlist[i].symbol, atomcolors[self.structure.atomlist[i].symbol], self.shader, self.roughness)
            
            obj.active_material = material
            bpy.ops.object.shade_smooth()
            tmp = self.structure.atomlist[i].xyz.ang
            bpy.ops.transform.translate(value=(tmp[0],tmp[1],tmp[2]))

        for p in self.structure.graph.getPairs(1):
            vec1 = mathutils.Vector(self.structure.atomlist[p[0]].xyz.ang)
            vec2 = mathutils.Vector(self.structure.atomlist[p[1]].xyz.ang)
            vec = vec2-vec1

            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=stickradius,depth=vec.length*0.5,end_fill_type="NOTHING")
            obj = bpy.context.active_object
            obj.modifiers.new(type="SUBSURF", name="subsurf")
            obj.modifiers["subsurf"].levels = 4
            obj.modifiers["subsurf"].render_levels = 6
            material = makeMat(self.structure.atomlist[p[0]].symbol, atomcolors[self.structure.atomlist[p[0]].symbol], self.shader, self.roughness)
            obj.active_material = material
            bpy.ops.object.shade_smooth()
            axis=mathutils.Vector([0,0,1]).cross(vec)
            angle=mathutils.Vector([0,0,1]).angle(vec)
            rot_mat=mathutils.Matrix.Rotation(angle,4,axis)
        
            orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
            orig_loc_mat = mathutils.Matrix.Translation(orig_loc)
        
            obj.matrix_world = orig_loc_mat @ rot_mat 
            value = ((vec1+vec2)*0.5+vec1)*0.5
        
            bpy.ops.transform.translate(value=value)
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=stickradius,depth=vec.length*0.5,end_fill_type="NOTHING")
            obj = bpy.context.active_object
            obj.modifiers.new(type="SUBSURF", name="subsurf")
            obj.modifiers["subsurf"].levels = 4
            obj.modifiers["subsurf"].render_levels = 6
            material = makeMat(self.structure.atomlist[p[1]].symbol, atomcolors[self.structure.atomlist[p[1]].symbol], self.shader, self.roughness)
            obj.active_material = material
            bpy.ops.object.shade_smooth()
            obj.matrix_world = orig_loc_mat @ rot_mat 
            bpy.ops.transform.translate(value=(((vec1+vec2)*0.5+vec2)*0.5))
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
                        me = bpy.ops.mesh.primitive_cylinder_add(radius=stickradius*0.8,depth=vec.length*0.1,end_fill_type="NGON")
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
        return (context.object is not None)


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
        row.prop(context.window_manager.toggle_buttons, "hbonds")
        if context.window_manager.toggle_buttons.hbonds:
            row = layout.row()
            row.prop(context.window_manager.toggle_buttons, "hbond_color")
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
        ('Principled', 'Plastic', 'Use principled BSDF shader', '', 2)
    ],
    default='Diffuse'
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
                                     default = (0.9,0.5,0.1,1.0)
                                     )
    vector_color : bpy.props.FloatVectorProperty(
                                     name = "Vector Color",
                                     subtype = "COLOR",
                                     size = 4,
                                     min = 0.0,
                                     max = 1.0,
                                     default = (0.9,0.,0.,1.0)
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
        structureobject = structure(bpy.context.scene.MyString)
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



    
classes = ( ToggleButtons,
            OBJECT_OT_import_structure_button,
            OBJECT_OT_xyz_path,
            PANEL_PT_molecule_panel,
          )

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.WindowManager.toggle_buttons = bpy.props.PointerProperty(type=ToggleButtons)

def unregister():
    del bpy.types.WindowManager.toggle_buttons
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
#register()
if __name__ == "main":
    register()