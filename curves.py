import bpy, mathutils
from . import Blender
from .base import Object

from mathutils import Vector
from math import radians, cos, sin



class Curve(Object):
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

    def create(self, verts, spline_order = -1, *args, **kw):
        if not self.created:
            name = 'Curve'

            if 'name' in kw:
                name = kw['name']
            elif 'name' in self.cache:
                name = self.cache['name']

            curve = bpy.data.curves.new(name=name, type='CURVE')
            curve.dimensions = '3D'

            spline = curve.splines.new('NURBS')
            spline.points.add(len(verts)-1)
            for i, p in enumerate(verts):
                (x,y,z), w = p, 1.
                spline.points[i].co = (x,y,z,w)

            spline.order_u = len(verts)-1 if spline_order == -1 else spline_order
            spline.use_endpoint_u = True
            spline.use_cyclic_u = False

            self._bpy = bpy.data.objects.new(name, curve)
            self.location = (0,0,0)

        return super().create(*args, **kw)


    def update(self, verts, *args, **kw):
        if self.created:
            spline = self._bpy.data.splines[0]
            if spline.type in ('NURBS', 'POLY'):
                for i, p in enumerate(verts):
                    (x,y,z), w = p, 1.
                    spline.points[i].co = (x,y,z,w)
                self.notify('data.splines.points.co')

            elif spline.type == 'BEZIER':
                for i, p in enumerate(verts):
                    (x,y,z), w = p, 1.
                    spline.bezier_points[i].co = (x,y,z,w)
                self.notify('data.splines.bezier_points.co')
            else:
                raise RuntimeError('Unsupported Curve type')

        return super().update(*args, **kw)



def NurbsPath(name, verts, spline_order = -1, *args, **kw):
    curve = bpy.data.curves.new(name=name, type='CURVE')
    curve.dimensions = '3D'

    spline = curve.splines.new('NURBS')
    spline.points.add(len(verts)-1)
    for i, p in enumerate(verts):
        (x,y,z), w = p, 1.
        spline.points[i].co = (x,y,z,w)

    spline.order_u = len(verts)-1 if spline_order == -1 else spline_order
    spline.use_endpoint_u = True
    spline.use_cyclic_u = False

    obj = bpy.data.objects.new(name, curve)
    obj.location = (0,0,0)

    return Curve(obj, *args, **kw).link()

def NurbsLine(name, p1, p2, *args, **kw):
    return NurbsPath(name, [p1, p2], *args, **kw)

def BezierPath(name, verts, spline_order = -1, *args, **kw):
    curve = bpy.data.curves.new(name=name, type='CURVE')
    curve.dimensions = '3D'


    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(verts)-1)

    for i, p in enumerate(verts):
        spline.bezier_points[i].co = p

    #spline.order_u = len(verts)-1 if spline_order == -1 else spline_order
    #spline.use_endpoint_u = True
    #spline.use_cyclic_u = False

    obj = bpy.data.objects.new(name, curve)
    obj.location = (0,0,0)

    return Curve(obj, *args, **kw).link()

def NurbsCircle(name='NurbsCircle', radius=1, \
                 location = (0., 0., 0.), \
                 *args, **kw):
    bpy.ops.curve.primitive_nurbs_circle_add(radius=float(radius), \
            location=Vector(location), \
            layers=[True]+[False]*19)
    obj = Blender.active_object
    obj.name = name
    return Curve(obj, *args, **kw)

def BezierCircle(name='BezierCircle', radius=1, \
                 location = (0., 0., 0.), \
                 *args, **kw):
    bpy.ops.curve.primitive_bezier_circle_add(radius=float(radius), \
            location=Vector(location), \
            layers=[True]+[False]*19)
    obj = Blender.active_object
    obj.name = name
    return Curve(obj, *args, **kw)

def NurbsSurface(name='NurbsSurface', type='SPHERE',
                 radius=1, \
                 location = (0., 0., 0.), \
                 rotation = (0., 0., 0.), \
                 *args, **kw):
    type = type.upper()
    f = None
    if type == 'SPHERE': f = bpy.ops.surface.primitive_nurbs_surface_sphere_add
    elif type == 'SURFACE': f = bpy.ops.surface.primitive_nurbs_surface_surface_add
    elif type == 'TORUS': f = bpy.ops.surface.primitive_nurbs_surface_torus_add
    elif type == 'CYLINDER': f = bpy.ops.surface.primitive_nurbs_surface_cylinder_add
    elif type == 'CURVE': f = bpy.ops.surface.primitive_nurbs_surface_curve_add
    elif type == 'CIRCLE': f = bpy.ops.surface.primitive_nurbs_surface_circle_add

    if f == None:
        raise ArgumentError('Invalid argument type: %s' % str(type))


    f(radius=float(radius), \
        location=Vector(location))
    #obj = Blender.active_object
    obj = bpy.context.active_object
    #obj.name = name
    return Curve(obj, *args, **kw)

##------------------------------------------------------------
# Point:
def PointVerts():
    newpoints = []

    newpoints.append([0.0, 0.0, 0.0])

    return newpoints

##------------------------------------------------------------
# Line:
def LineVerts(c1 = [0.0, 0.0, 0.0], c2 = [2.0, 2.0, 2.0]):
    newpoints = []

    c3 = Vector(c2) - Vector(c1)
    newpoints.append([0.0, 0.0, 0.0])
    newpoints.append([c3[0], c3[1], c3[2]])

    return newpoints

##------------------------------------------------------------
# Angle:
def AngleVerts(length = 1.0, angle = 45.0):
    newpoints = []

    angle = radians(angle)
    newpoints.append([length, 0.0, 0.0])
    newpoints.append([0.0, 0.0, 0.0])
    newpoints.append([length * cos(angle), length * sin(angle), 0.0])

    return newpoints

##------------------------------------------------------------
# Distance:
def DistanceVerts(length = 1.0, center = True):
    newpoints = []

    if center:
        newpoints.append([-length / 2, 0.0, 0.0])
        newpoints.append([length / 2, 0.0, 0.0])
    else:
        newpoints.append([0.0, 0.0, 0.0])
        newpoints.append([length, 0.0, 0.0])

    return newpoints

##------------------------------------------------------------
# Circle:
def CircleVerts(sides = 4, radius = 1.0):
    newpoints = []

    angle = radians(360)/sides
    newpoints.append([radius,0,0])
    j=1
    while j < sides:
        t = angle * j
        x = cos(t)*radius
        y = sin(t)*radius
        newpoints.append([x,y,0])
        j+=1

    return newpoints

##------------------------------------------------------------
# Ellipse:
def EllipseVerts(a = 2.0, b = 1.0):
    newpoints = []

    newpoints.append([a, 0.0, 0.0])
    newpoints.append([0.0, b, 0.0])
    newpoints.append([-a, 0.0, 0.0])
    newpoints.append([0.0, -b, 0.0])

    return newpoints

##------------------------------------------------------------
# Arc:
def ArcVerts(sides = 0, radius = 1.0, startangle = 0.0, endangle = 45.0):
    newpoints = []

    startangle = radians(startangle)
    endangle = radians(endangle)
    sides+=1

    angle = (endangle-startangle)/sides
    x = cos(startangle)*radius
    y = sin(startangle)*radius
    newpoints.append([x,y,0])
    j=1
    while j < sides:
        t = angle * j
        x = cos(t+startangle)*radius
        y = sin(t+startangle)*radius
        newpoints.append([x,y,0])
        j+=1
    x = cos(endangle)*radius
    y = sin(endangle)*radius
    newpoints.append([x,y,0])

    return newpoints

##------------------------------------------------------------
# Sector:
def SectorVerts(sides = 0, radius = 1.0, startangle = 0.0, endangle = 45.0):
    newpoints = []

    startangle = radians(startangle)
    endangle = radians(endangle)
    sides+=1

    newpoints.append([0,0,0])
    angle = (endangle-startangle)/sides
    x = cos(startangle)*radius
    y = sin(startangle)*radius
    newpoints.append([x,y,0])
    j=1
    while j < sides:
        t = angle * j
        x = cos(t+startangle)*radius
        y = sin(t+startangle)*radius
        newpoints.append([x,y,0])
        j+=1
    x = cos(endangle)*radius
    y = sin(endangle)*radius
    newpoints.append([x,y,0])

    return newpoints

##------------------------------------------------------------
# Segment:
def SegmentVerts(sides = 0, a = 2.0, b = 1.0, startangle = 0.0, endangle = 45.0):
    newpoints = []

    startangle = radians(startangle)
    endangle = radians(endangle)
    sides+=1

    angle = (endangle-startangle)/sides
    x = cos(startangle)*a
    y = sin(startangle)*a
    newpoints.append([x,y,0])
    j=1
    while j < sides:
        t = angle * j
        x = cos(t+startangle)*a
        y = sin(t+startangle)*a
        newpoints.append([x,y,0])
        j+=1
    x = cos(endangle)*a
    y = sin(endangle)*a
    newpoints.append([x,y,0])

    x = cos(endangle)*b
    y = sin(endangle)*b
    newpoints.append([x,y,0])
    j=sides
    while j > 0 :
        t = angle * j
        x = cos(t+startangle)*b
        y = sin(t+startangle)*b
        newpoints.append([x,y,0])
        j-=1
    x = cos(startangle)*b
    y = sin(startangle)*b
    newpoints.append([x,y,0])

    return newpoints

##------------------------------------------------------------
# Rectangle:
def RectangleVerts(width=2.0, length=2.0, rounded=0.0, center=True):
    newpoints = []

    r=rounded/2

    if center:
        x=width/2
        y=length/2
        if rounded != 0.0:
            newpoints.append([-x+r, y, 0.0])
            newpoints.append([x-r, y, 0.0])
            newpoints.append([x, y-r, 0.0])
            newpoints.append([x, -y+r, 0.0])
            newpoints.append([x-r, -y, 0.0])
            newpoints.append([-x+r, -y, 0.0])
            newpoints.append([-x, -y+r, 0.0])
            newpoints.append([-x, y-r, 0.0])
        else:
            newpoints.append([-x, y, 0.0])
            newpoints.append([x, y, 0.0])
            newpoints.append([x, -y, 0.0])
            newpoints.append([-x, -y, 0.0])

    else:
        x=width
        y=length
        if rounded != 0.0:
            newpoints.append([r, y, 0.0])
            newpoints.append([x-r, y, 0.0])
            newpoints.append([x, y-r, 0.0])
            newpoints.append([x, r, 0.0])
            newpoints.append([x-r, 0.0, 0.0])
            newpoints.append([r, 0.0, 0.0])
            newpoints.append([0.0, r, 0.0])
            newpoints.append([0.0, y-r, 0.0])
        else:
            newpoints.append([0.0, 0.0, 0.0])
            newpoints.append([0.0, y, 0.0])
            newpoints.append([x, y, 0.0])
            newpoints.append([x, 0.0, 0.0])

    return newpoints

##------------------------------------------------------------
# Rhomb:
def RhombVerts(width = 2.0, length = 2.0, center = True):
    newpoints = []
    x = width / 2
    y = length / 2

    if center:
        newpoints.append([-x, 0.0, 0.0])
        newpoints.append([0.0, y, 0.0])
        newpoints.append([x, 0.0, 0.0])
        newpoints.append([0.0, -y, 0.0])
    else:
        newpoints.append([x, 0.0, 0.0])
        newpoints.append([0.0, y, 0.0])
        newpoints.append([x, length, 0.0])
        newpoints.append([width, y, 0.0])

    return newpoints

##------------------------------------------------------------
# Polygon:
def PolygonVerts(sides = 3, radius = 1.0):
    newpoints = []
    angle = radians(360.0) / sides
    j = 0

    while j < sides:
        t = angle * j
        x = sin(t) * radius
        y = cos(t) * radius
        newpoints.append([x, y, 0.0])
        j += 1

    return newpoints

##------------------------------------------------------------
# Polygon_ab:
def Polygon_abVerts(sides = 3, a = 2.0, b = 1.0):
    newpoints = []
    angle = radians(360.0) / sides
    j = 0

    while j < sides:
        t = angle * j
        x = sin(t) * a
        y = cos(t) * b
        newpoints.append([x, y, 0.0])
        j += 1

    return newpoints

##------------------------------------------------------------
# Trapezoid:
def TrapezoidVerts(a = 2.0, b = 1.0, h = 1.0, center = True):
    newpoints = []
    x = a / 2
    y = b / 2
    r = h / 2

    if center:
        newpoints.append([-x, -r, 0.0])
        newpoints.append([-y, r, 0.0])
        newpoints.append([y, r, 0.0])
        newpoints.append([x, -r, 0.0])

    else:
        newpoints.append([0.0, 0.0, 0.0])
        newpoints.append([x - y, h, 0.0])
        newpoints.append([x + y, h, 0.0])
        newpoints.append([a, 0.0, 0.0])

    return newpoints
