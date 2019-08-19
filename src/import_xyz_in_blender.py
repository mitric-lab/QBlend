import bpy
from bpy.props import *
import mathutils
import itertools
from mathutils import Vector
import numpy as np

#this one add a variable to the scene
bohrToAngs = 0.529
bpy.types.Scene.MyString = StringProperty(name="file path",
    attr="custompath",# this a variable that will set or get from the scene
    description="simple file path",
    maxlen= 1024,
    default= "")#this set the text
    
    
bpy.types.Scene.MyPath = StringProperty(name="file path",
    attr="custompath",# this a variable that will set or get from the scene
    description="simple file path",
    maxlen= 1024,
    subtype='FILE_PATH',
    default= "")#this set the text

matHbond = bpy.data.materials.new("Hbond")
matHbond.diffuse_color = (1, 0.7, 0)
matHbond.diffuse_shader = 'LAMBERT' 
matHbond.diffuse_intensity = 1.0 
matHbond.specular_color = (1, 1, 1)
matHbond.specular_shader = 'COOKTORR'
matHbond.specular_intensity = 0.5
matHbond.specular_hardness = 400
matHbond.emit = 0.2
matHbond.alpha = 1
matHbond.ambient = 1


def makeMat(name, diffuse):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT' 
    mat.diffuse_intensity = 1.0 
    mat.specular_color = (1, 1, 1)
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    mat.specular_hardness = 400
    mat.alpha = 1
    mat.ambient = 1
    return mat

def setMaterial(ob, mat):
    me = ob.data
    me.materials.append(mat)
       
# Global data for molecule visualization
isothreshold=0.10
spheresubdivisions=5
covalentradii={"B":0.77,"C":0.77,"H":0.37,"N":0.77,"O":0.77,"Zn":1.50,"S":1.50,"19":1.50,"13":1.50,"22":1.50,"21":1.50,"30":1.50/0.529,"14":1.50/0.529}
atomicradii={"H":0.7,"B":1.50,"C":1.50,"N":1.50,"Zn":2,"O":1.50,"79":2.00,"S":1.50,"19":2.00,"13":2.00,"22":2.00,"21":2.00,"14":2.00}
stickradius=0.25

atomicradii = atomicradii.fromkeys(atomicradii, stickradius)
 
materials={"H":makeMat("H", (0.7, 0.7, 0.7)),"B":makeMat("B", (0., 0.9, 0.)),
           "C":makeMat("C", (0.2, 0.2, 0.2)),"N":makeMat("N", (0., 0., 1.)), 
           "O":makeMat("O", (1., 0., 0.)),"Si":makeMat("Si", (238.0/256, 180.0/256, 34.0/256)),
           "S":makeMat("S", (228.0/255.0, 202.0/255.0, 66.0/255.0)),
           "Zn":makeMat("Zn", (0.4, 0.4, 0.4))}

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
    def __init__(self,structure):
        self.structure=structure
        self.scene = bpy.context.scene

    def blenderstructure(self):
        for i in range(len(self.structure.atomlist)): 
            me = bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4,size=atomicradii[self.structure.atomlist[i].symbol])
            setMaterial(bpy.context.object, materials[self.structure.atomlist[i].symbol])
            bpy.ops.object.shade_smooth()
            tmp = self.structure.atomlist[i].xyz.ang
            bpy.ops.transform.translate(value=(tmp[0],tmp[1],tmp[2]))
        for p in self.structure.graph.getPairs(1):
            vec1 = mathutils.Vector(self.structure.atomlist[p[0]].xyz.ang)
            vec2 = mathutils.Vector(self.structure.atomlist[p[1]].xyz.ang)
            vec = vec2-vec1

            me = bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=stickradius,depth=vec.length*0.5,end_fill_type="NOTHING")
            setMaterial(bpy.context.object, materials[self.structure.atomlist[p[0]].symbol])
            bpy.ops.object.shade_smooth()
            axis=mathutils.Vector([0,0,1]).cross(vec)
            angle=mathutils.Vector([0,0,1]).angle(vec)
            rot_mat=mathutils.Matrix.Rotation(angle,4,axis)
            obj = bpy.context.active_object
            orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
            orig_loc_mat = mathutils.Matrix.Translation(orig_loc)
            obj.matrix_world = orig_loc_mat * rot_mat 
            bpy.ops.transform.translate(value=(((vec1+vec2)*0.5+vec1)*0.5))
					
            me = bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=stickradius,depth=vec.length*0.5,end_fill_type="NOTHING")
            setMaterial(bpy.context.object, materials[self.structure.atomlist[p[1]].symbol])
            bpy.ops.object.shade_smooth()
            obj = bpy.context.active_object
            obj.matrix_world = orig_loc_mat * rot_mat 
            bpy.ops.transform.translate(value=(((vec1+vec2)*0.5+vec2)*0.5))
	
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


class VIEW3D_PT_custompathmenupanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "Animate a molecule"
    bl_category = 'Molecule'
    
    def draw(self, context):
        layout = self.layout
        

        #print(dir(context.scene)) # this will display the list that you should able to see
        #operator button
        #OBJECT_OT_CustomPath => object.custom_path
        layout.operator("object.custom_path")
        #prop is an variable to to set or get name of the variable.
        layout.prop(context.scene,"MyString")
        #layout.label(text="custom text")

        #print(dir(bpy.context.scene))
        #operator button
        #OBJECT_OT_CustomButton => object.CustomButton
        layout.operator("object.custombutton")
        
class OBJECT_OT_custombutton(bpy.types.Operator):
    bl_idname = "object.custombutton"
    bl_label = "Import structure"
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

class OBJECT_OT_custompath(bpy.types.Operator):
    bl_idname = "object.custom_path"
    bl_label = "Select xyz files"
    __doc__ = ""
    
    
    filename_ext = ".xyz"
    filter_glob = StringProperty(default="*.xyz", options={'HIDDEN'})    
        
    
    #this can be look into the one of the export or import python file.
    #need to set a path so so we can get the file name and path
    filepath = StringProperty(name="File Path", description="Filepath used for importing txt files", maxlen= 1024, default= "")
    files = CollectionProperty(
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
        
def register():
    bpy.utils.register_class(VIEW3D_PT_custompathmenupanel)
    bpy.utils.register_class(OBJECT_OT_custombutton)
    bpy.utils.register_class(OBJECT_OT_custompath)
    print("register")

def unregister():
    bpy.utils.register_class(VIEW3D_PT_custompathmenupanel)
    bpy.utils.register_class(OBJECT_OT_custombutton)
    bpy.utils.register_class(OBJECT_OT_custompath)
    print("unregister")

if __name__ == "__main__":
    register()