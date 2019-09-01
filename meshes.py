import bpy, mathutils
from . import Blender
from .base import Object
from mathutils import Vector

class Mesh(Object):
    __slots__ = []
    __overwrites__ = ['name']
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    @property
    def name(self): return self.getobjattr('name')
    @name.setter
    def name(self, value):
        if self.created:
            self._bpy.data.name = value
        return self.setobjattr('name', value)

    def create(self, verts = None, edges = None, faces = None, *args, **kw):

        if not self.created:
            name = 'Mesh'
            if 'name' in kw:
                name = kw['name']
            elif 'name' in self.cache:
                name = self.cache['name']


            if edges == None: edges = []
            if faces == None: faces = []
            if verts == None: verts = []

            assert (len(edges) and len(faces)) or (len(faces) and len(verts)) or (len(edges) and len(verts))


            mesh = bpy.data.meshes.new(name)
            mesh.from_pydata(verts, edges, faces)
            mesh.use_auto_smooth = True


            if edges == []:
                mesh.update(calc_edges=True)

            obj =  bpy.data.objects.new(name, mesh)
            obj.name = name

            self.link(obj)
            self.remove_doubles()
            if Blender.auto_shade_smooth():
                self.shade_smooth();

        return super().create(*args, **kw)

    def update(self, *args, **kw):
        return super().update(*args, **kw)

    def remove_doubles(self):
        if self.linked:
            bpy.context.scene.objects.active = self.bpy
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.remove_doubles(threshold=0.0001)
            bpy.ops.object.editmode_toggle()
        else:
            print("Can not remove double verticies")
        return self

    def shade_smooth(self):
        if self.created:
            for f in self.bpy.data.polygons:
                f.use_smooth = True
            self.select_set(True)
            bpy.ops.object.shade_smooth()
            self.select_set(False)
        else:
            print("Can not set smooth shade")
        return self



def Icosphere(name = 'Icosphere',
              radius = 1.,
              subdivisions = 5,
              location = (0., 0., 0.),
              *args, **kw):

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=int(subdivisions), \
        radius=float(radius), location=Vector(location) ) #, layers=[True]+[False]*19)

    obj = Mesh(Blender.active_object)
    obj.name = name
    if Blender.auto_shade_smooth():
        obj.shade_smooth()

    return obj

def UVsphere(name = 'UVsphere',
             radius = 1.,
             subdivisions = 32,
             rings = None,
             location = (0., 0., 0.),
             *args, **kw):

    segments = subdivisions
    rings = segments/2 if not rings else rings

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=int(segments), ring_count=int(rings), \
        radius=float(radius), location=Vector(location) ) #, layers=[True]+[False]*19)

    obj = Blender.active_object
    obj.name = name
    return Mesh(obj, *args, **kw)

def Cylinder(name = 'Cylinder',
             vector = (0.,0.,1.),
             radius = 1.,
             subdivisions = 24,
             end_fill_type = 'NGON',
             location = (0., 0., 0.),
             *args, **kw):

    vector = Vector(vector)
    zaxis = Vector([0.,0.,1.])
    angle = zaxis.angle(vector)
    axis = zaxis.cross(vector)
    rotation = mathutils.Matrix.Rotation(angle, 4, axis).to_euler()


    bpy.ops.mesh.primitive_cylinder_add(
        vertices=int(subdivisions), radius=float(radius), \
        location=Vector(location), rotation=Vector(rotation), \
        end_fill_type=end_fill_type, \
        depth=float(vector.length) )#, layers=[True]+[False]*19)
    obj = Mesh(Blender.active_object)
    obj.name = name
    if Blender.auto_shade_smooth():
        obj.shade_smooth()

    return obj

def Cone(name = 'Cone',
         vector = (0.,0.,1.),
         radius1 = 1., radius2 = 0.,
         subdivisions = 32,
         end_fill_type = 'NGON',
         location = (0., 0., 0.),
         *args, **kw):

    vector = Vector(vector)
    zaxis = Vector([0.,0.,1.])
    angle = zaxis.angle(vector)
    axis = zaxis.cross(vector)
    rotation = mathutils.Matrix.Rotation(angle, 4, axis).to_euler()

    bpy.ops.mesh.primitive_cone_add(
        vertices=int(subdivisions),
        radius1=float(radius1), radius2=float(radius2), \
        location=Vector(location), rotation=Vector(rotation), \
        end_fill_type=end_fill_type, \
        depth=float(vector.length) )#, layers=[True]+[False]*19)
    obj = Mesh(Blender.active_object)
    obj.name = name
    if Blender.auto_shade_smooth():
        obj.shade_smooth()

    return obj

def Cube(name = 'Cube',
         size = (1.,1.,1.),
         location = (0., 0., 0.),
         rotation = (0., 0., 0.),
         *args, **kw):

    if size == None:
        scale = (1., 1., 1.)
    elif isinstance(size, (float, int)):
        scale = (size, size, 1.)
    elif hasattr(size, "__iter__"):
        scale = (size[0], size[1], size[2])

    bpy.ops.mesh.primitive_cube_add(
        location=Vector(location), rotation=Vector(rotation)) #,\
        #layers=[True]+[False]*19)
    obj = Mesh(Blender.active_object)
    obj.name = name
    if Blender.auto_shade_smooth():
        pass
        #obj.shade_smooth()

    return obj

def Grid(name = 'Grid',
         size = (1., 1.),
         normal = None,
         subdivisions = 32, subdivisions2 = None,
         location = (0., 0., 0.),
         rotation = (0., 0., 0.),
         *args, **kw):

    subdivisions2 = subdivisions if not subdivisions2 else subdivisions2

    if size == None:
        scale = (1., 1., 1.)
    elif isinstance(size, (float, int)):
        scale = (size, size, 1.)
    elif hasattr(size, "__iter__"):
        scale = (size[0], size[1], 1.)

    if normal:
        vector = Vector(normal)
        zaxis = Vector([0.,0.,1.])
        angle = zaxis.angle(vector)
        axis = zaxis.cross(vector)
        rotation = mathutils.Matrix.Rotation(angle, 4, axis).to_euler()



    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions = int(subdivisions), y_subdivisions = int(subdivisions2), \
        radius = float(1.), \
        location=Vector(location), rotation=Vector(rotation) ) #, \
        #layers=[True]+[False]*19)
    obj = Mesh(Blender.active_object)
    obj.name = name
    if Blender.auto_shade_smooth():
        obj.shade_smooth()

    return obj

def Plane(name = 'Plane',
         size = (1., 1.),
         normal = None,
         location = (0., 0., 0.),
         rotation = (0., 0., 0.),
         *args, **kw):

    if size == None:
        scale = (1., 1., 1.)
    elif isinstance(size, (float, int)):
        scale = (size, size, 1.)
    elif hasattr(size, "__iter__"):
        scale = (size[0], size[1], 1.)

    if normal:
        vector = Vector(normal)
        zaxis = Vector([0.,0.,1.])
        angle = zaxis.angle(vector)
        axis = zaxis.cross(vector)
        rotation = mathutils.Matrix.Rotation(angle, 4, axis).to_euler()


    bpy.ops.mesh.primitive_plane_add(
        location=Vector(location), rotation=Vector(rotation) ) #, \
        #layers=[True]+[False]*19)
    obj = Mesh(Blender.active_object)
    obj.name = name
    if Blender.auto_shade_smooth():
        obj.shade_smooth()

    return obj

def Circle(name = 'Circle',
         size = (1., 1.),
         subdivisions = 32,
         normal = None,
         fill_type = 'NOTHING',
         location = (0., 0., 0.),
         rotation = (0., 0., 0.),
         *args, **kw):

    if size == None:
        scale = (1., 1., 1.)
    elif isinstance(size, (float, int)):
        scale = (size, size, 1.)
    elif hasattr(size, "__iter__"):
        scale = (size[0], size[1], 1.)


    if normal:
        vector = Vector(normal)
        zaxis = Vector([0.,0.,1.])
        angle = zaxis.angle(vector)
        axis = zaxis.cross(vector)
        rotation = mathutils.Matrix.Rotation(angle, 4, axis).to_euler()


    bpy.ops.mesh.primitive_circle_add(
        vertices=int(subdivisions), radius=1.,
        location=Vector(location), rotation=Vector(rotation) ) #, \
        #layers=[True]+[False]*19)
    obj = Mesh(Blender.active_object)
    obj.name = name
    if Blender.auto_shade_smooth():
        obj.shade_smooth()

    return obj

"""
type = [‘BALL’, ‘CAPSULE’, ‘PLANE’, ‘ELLIPSOID’, ‘CUBE’]
"""
def Metaball(name = 'Metaball',
             type='BALL',
             size = (1., 1., 1.),
             location=(0.0, 0.0, 0.0),
             rotation=(0.0, 0.0, 0.0),
            *args, **kw):

    if size == None:
        scale = (1., 1., 1.)
    elif isinstance(size, (float, int)):
        scale = (size, size, 1.)
    elif hasattr(size, "__iter__"):
        scale = (size[0], size[1], size[2])

    bpy.ops.object.metaball_add(
        type = type,
        location = Vector(location), rotation = Vector(rotation))

    obj = Blender.active_object
    obj.name = name
    obj.scale = scale
    return Object(obj, *args, **kw)

def ZSurface(name, z,
             xaxis = None, yaxis = None,
             location = (0., 0., 0.),
             rotation = (0., 0., 0.),
             *args, **kw):
    import numpy as np
    z = np.array(z)
    if xaxis == None:
        xaxis = range(z.shape[0])
    if yaxis == None:
        yaxis = range(z.shape[1])

    assert xaxis == None or (len(xaxis) == z.shape[0])
    assert yaxis == None or (len(yaxis) == z.shape[1])

    nx, ny = z.shape
    verts = [(xaxis[i], yaxis[j], z[i,j]) for i in range(nx) for j in range(ny)]

    count = 0
    faces = []
    for i in range (0, ny *(nx-1)):
        if count < ny-1:
            faces.append((i, i+1, i+ny+1, i+ny))
            count = count + 1
        else:
            count = 0

    """
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.use_auto_smooth = True
    mesh.update(calc_edges=True)

    obj = bpy.data.objects.new(name, mesh)
    obj.name = name
    if location != None:
        obj.location = Vector(location)
    if rotation != None:
        obj.rotation_euler = Vector(rotation)
    """

    obj = Mesh(name).create(verts, [], faces)
    if location != None:
        obj.location = Vector(location)
    if rotation != None:
        obj.rotation_euler = Vector(rotation)
    return obj



def Isosurface(name, triangles,
               location = (0., 0., 0.),
               rotation = (0., 0., 0.),
               *args, **kw):

    verts, faces = [], []
    for i,tri in enumerate(triangles):
        assert(len(tri) == 3)
        for v in tri:
            verts.append(list(v))
        faces.append((3*i, 3*i+1, 3*i+2))

    """
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.use_auto_smooth = True

    mesh.update(calc_edges=True)



    obj = bpy.data.objects.new(name, mesh)
    obj.name = name
    if location != None:
        obj.location = Vector(location)
    if rotation != None:
        obj.rotation_euler = Vector(rotation)

    for f in obj.data.polygons:
        f.use_smooth = True


    return Mesh(name, *args, **kw).link().remove_doubles().shade_smooth()
    """

    obj = Mesh(name).create(verts, [], faces)
    if location != None:
        obj.location = Vector(location)
    if rotation != None:
        obj.rotation_euler = Vector(rotation)
    return obj
