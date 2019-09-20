import bpy, mathutils, copy
from . import Blender
from .utils import *

import sys,os
sys.path.append("/Applications/blender.app/Contents/Resources/2.80/scripts/addons/qblend/lib/")
from lib import AttrDict
from _ctypes import ArgumentError


class Base(object):
    __slots__ = ['_cache', '_bpy', '_ipokeys']
    __overwrites__ = ['copy']
    def __init__(self, init = None, *args, **kw):
        self._cache = AttrDict()
        self._bpy = None
        self._ipokeys = []

        if isinstance(init, Base):
            self._bpy = init._bpy
            self._cache = init._cache
            self._ipokeys = init._ipokeys
        elif isinstance(init, AttrDict):
            self._cache = init.copy()
        elif isinstance(init, bpy.types.ID):
            self._bpy = init
        elif isinstance(init, str):
            self.name = init



        #if self.created:
        for k,v in AttrDict(kw).attr_items():
            if k not in ('ipokeys'):
                #print("BASE SETATTR", self, self.created, k, v)
                setattr(self, k, v)
        if 'ipokeys' in kw:
            self.addAutoKey(kw['ipokeys'])

    @property
    def created(self): return self._bpy != None

    @property
    def cache(self): return self._cache

    @property
    def bpy(self): return self._bpy

    @property
    def _obj(self):
        if self.created: return self._bpy
        else: return self._cache

    @_obj.deleter
    def _obj(self):
        if self.created:
            del self._bpy
            self._bpy = None

    @_obj.setter
    def _obj(self, value):
        if not self.created and value != None:
            self._bpy = value
            for k, v in self.cache.attr_items():
                #set_blender_object_property()
                setattr(self._bpy, k, v)
            del self._cache
            self._cache = AttrDict()
        else:
            del self._obj



    @classmethod
    def _get_slots(cls):
        slots = cls.__overwrites__[:] + cls.__slots__[:]
        for b in cls.__bases__:
            if issubclass(b, Base):
                slots += b._get_slots()
        return slots

    def __repr__(self):
        return repr(self._bpy) if self.created else ("<Base(%s)>" (repr(self.cache)) )

    def __getattr__(self, name):
        try:
            #print("NULL")
            if name[0] != '_' and name not in self._get_slots():
                #print("EINS", name)
                return self.getobjattr(name)
            else:
                #print("ZWEI", name, type(self).__name__)
                return super().__getattr__(self, name)
        except:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        #print("NAMENAME", name, value)
        try:
            if name[0] != '_' and name not in self._get_slots():
                #print("EINS")
                self.setobjattr(name, value)
            else:
                #print("ZWEI")
                super().__setattr__(name, value)
        except:
            pass
            #raise AttributeError(name)

    def setobjattr(self, name, value):

        if self._bpy != None:
            old = self.getobjattr(name)
            if not isinstance(old, Base):
                #print(name, self.getobjattr(name))
                oldvalue = copy.deepcopy(self.getobjattr(name))
            else:
                oldvalue = None

            if isinstance(value, Base):
                if not value.created: value.create()

                value = value._bpy

            #print("BPYSET ", name, value, oldvalue)
            set_blender_object_property(self._bpy, name, value)
            if oldvalue != None and oldvalue != value:
                self.notify(name)
        else:
            setattr(self.cache, name, value)

    def getobjattr(self, name, default = None):
        try:
            if self._bpy != None:
                val = get_blender_object_property(self._bpy,name)
            else:
                val = self.cache[name]
        except (KeyError, ArgumentError):
            val = default

        #print("BPYGET", name, val)

        if isinstance(val, bpy.types.Object):
            val = Object(val)
        elif isinstance(val, bpy.types.Material):
            val = Material(val)
        elif isinstance(val, bpy.types.ID):
            val = Base(val)

        return val

    def addAutoKey(self, *args):
        for a in args:
            if a not in self._ipokeys:
                if isinstance(a, (tuple, list)):
                    self.addAutoKey(*tuple(a))
                elif isinstance(a, str):
                    self._ipokeys.append(a)
                    self.notify(a)
        return self

    def notify(self, *args, **kw):
        if len(args) == 0:
            self.notify(*self._ipokeys, **kw)
        else:
            for name in args:
                if Blender.auto_animate() and name in self._ipokeys:
                    self.keyframe_insert(name, **kw)


    def create(self, *args, **kw):
        for k,v in AttrDict(kw).attr_items():
            try:
                #print("set onCreate", k, v)
                setattr(self, k, v)
            except: raise

        return self

    def update(self, *args, **kw):
        for k,v in AttrDict(kw).attr_items():
            try:
                setattr(self, k, v)
            except: pass

        return self

    def copy(self, *args, **kw):
        clone = self.__class__(None, *args, **kw)

        if self._bpy != None:
            clone._bpy = self._bpy.copy()
        else:
            clone._cache = copy.copy(self.cache)

        clone._ipokeys = copy.copy(self._ipokeys)
        return clone

    def keyframe_insert(self, data_path, index=-1, frame=None, group=""):
        if self.created:
            frame = Blender.getFrame() if frame == None or frame == 'CURRENT' or frame == -1 else frame
            if data_path == None or data_path == 'ALL':
                for p in data_path:
                    self.keyframe_insert(p, index, frame, group)
            elif isinstance(data_path, str):
                #print("KEYFRAME", data_path, frame)
                insert_blender_keyframe(self._bpy, data_path, index, frame, group)
        return self


class LazyBase(Base):
    __slots__ = []
    __overwrites__ = []

    def __init__(self, init, *args, **kw):
        super().__init__(init, *args, **kw)

    @property
    def _obj(self): return super()._obj

    @_obj.deleter
    def _obj(self): del super()._obj

    @_obj.setter
    def _obj(self, value):
        if not self.created and value != None:
            self._bpy = value
            for k, v in self.cache.attr_items():
                self.setobjattr(k, v)
        else:
            del self._obj

    def __getattr__(self, name):
        try:
            if name[0] != '_' and name not in self._get_slots():
                return self.cache[name]
            else:
                return super().__getattr__(name)
        except (KeyError, AttributeError):
            print(self.cache, name in self.cache)
            raise AttributeError(name)

    def __setattr__(self, name, value):
        try:
            if name[0] != '_' and name not in self._get_slots():
                self.cache[name] = value
            else:
                super().__setattr__(name, value)
        except (KeyError, AttributeError):
            raise AttributeError(name)

    def __repr__(self):
        return "<LazyBase(%s)>" % (str(super().cache)) \
            if self.created else "<LazyBase(%s), %s>" % (str(super().cache), self._bpy)


    def copy(self, *args, **kw):
        return super().copy(*args, **kw)

    def remove(self, *args, **kw):
        return super().remove(*args, **kw)

    def create(self, *args, **kw):
        super().create(*args, **kw)

        for k, v in self.cache.attr_items():
            self.setobjattr(k, v)

        return self

    def update(self, *args, **kw):
        super().update(*args, **kw)

        for k, v in self.cache.attr_items():
            self.setobjattr(k, v)

        return self

class Material(Base):
    __slots__ = []
    __overwrites__ = ['alpha']
    def __init__(self, init, *args, **kw):
        super().__init__(init, *args, **kw)

    def __repr__(self):
        return repr(self._obj) if self.created else ("<Material(%s)>" % (self.cache))

    def remove(self):
        if self.created:
            self.data.user_clear()
            bpy.data.materials.remove(self._obj.data)
            self._bpy = None
        return self

    def __getitem__(self, name):
        return get_blender_object_property(self._obj, name)

    def __setitem__(self, name, value):
        return set_blender_object_property(self._obj, name, value)

    @property
    def alpha(self): return super().getobjattr('alpha')
    @alpha.setter
    def alpha(self, value):
        self.setobjattr('alpha', float(value))
        if value < 1. and not self.getobjattr('use_transparency'):
            self.setobjattr('use_transparency', True)
            self.setobjattr('transparency_method', 'Z_TRANSPARENCY')

class LazyMaterial(LazyBase):
    __slots__ = []
    __overwrites__ = ['alpha']

    def __init__(self, init = None, *args, **kw):
        if isinstance(init, str):
            kw['name'] = init

        super().__init__(None, *args, **kw)

    def __repr__(self):
        return "<LazyMaterial(%s)>" % (self.cache) \
            if self.created else "<LazyMaterial(%s), %s>" % (self.cache, self._bpy)

    def create(self, *args, **kw):
        kw = {"diffuse_color": (.2, .5, .2)}
        print("KWLM", kw)
        self.cache.update(**kw)
        if not self.created:
            name = 'LazyMaterial' if 'name' not in self.cache else self.name
            self._obj = bpy.data.materials.new(name)

        return super().create(*args, **kw)

    def update(self, *args, **kw):
        self._obj.update(*args, **kw)
        return self


    @property
    def alpha(self): return super().getobjattr('alpha')
    @alpha.setter
    def alpha(self, value):
        self.setobjattr('alpha', float(value))
        if value < 1. and not self.getobjattr('use_transparency'):
            self.setobjattr('use_transparency', True)
            self.setobjattr('transparency_method', 'Z_TRANSPARENCY')


class Object(Base):
    __slots__ = []
    __overwrites__ = ['parent', 'children', 'hide', 'location', 'scale', 'rotation_euler', 'material']
    def __init__(self, init = None, *args, **kw):
        super().__init__(init, *args, **kw)

    def __repr__(self):
        return repr(self._obj) if self.created else "<Object()>"

    def remove(self, remove_data = True, remove_material = False, do_unlink = True):
        _data_switch = {
        'LAMP': bpy.data.lights,
        'MESH': bpy.data.meshes,
        'CAMERA': bpy.data.cameras,
        'CURVE': bpy.data.curves,
        'OBJECT': bpy.data.objects,
        'MATERIALS': bpy.data.materials,
        'FONT': bpy.data.fonts,
        #'SURFACE': bpy.data.surfaces
        }
        if self.created:
            if self._obj.data and remove_data:
                self.data.user_clear()
                if self.type in _data_switch:
                    _data_switch[self.type].remove(self._bpy.data)

            if do_unlink:
                try:
                    Blender.objects.unlink(self._bpy)
                except:
                    print ("Can not unlink ", self._bpy.name)
            del self._obj
        return self

    @property
    def linked(self):
        #print(self.name)
        return self.created and self.name in Blender.context.collection.objects

    def link(self, obj = None):
        if self.created and obj:
            raise RuntimeError("Object %s is already created" % self.name)

        if obj != None:
            self._obj = obj

        if self.created and not self.linked:
            #bpy.context.collection.objects.link(self._bpy)
            Blender.context.collection.objects.link(self._bpy)
        return self

    def copy(self, do_link = True, *args, **kw):
        copy_data = 'copy_data' in kw and kw['copy_data']
        copy_mat = 'copy_material' in kw and kw['copy_material']
        clear_anim = 'clear_anim' not in kw or kw['clear_anim']
        clone = super().copy(*args, **kw)
        if self._bpy:
            if copy_data and self.data:
                clone._bpy.data = self._bpy.data.copy()
            elif copy_mat and self.material:
                clone.material = self.material.copy()

            if clear_anim:
                clone._bpy.animation_data_clear()
            if do_link:
                clone.link()

            #clone.parent = self.parent
        return clone

    @property
    def material(self):
        return self.getobjattr('active_material')


    @material.setter
    def material(self, value):
        if isinstance(value, LazyMaterial):
            if not value.created: value.create()
            self.setobjattr('active_material', value._obj)
        elif isinstance(value, Material):
            self.setobjattr('active_material', value._obj)
        elif isinstance(value, bpy.types.Material):
            self.setobjattr('active_material', value)
        else:
            raise ValueError(repr(value))



    @property
    def children(self):
        objs = []
        for c in self.getobjattr('children'):
            objs.append(Object(c))
        return tuple(objs)

    @property
    def parent(self): return self.getobjattr('parent')

    @parent.setter
    def parent(self, value):
        if isinstance(value, Object):
            self.setobjattr('parent', value._obj)
        elif isinstance(value, bpy.types.Object):
            self.setobjattr('parent', value)
        else:
            raise ValueError(repr(value))

    @property
    def scale(self): return self.getobjattr('scale')
    @scale.setter
    def scale(self, value):
        if isinstance(value, (int,float)):
            value = float(value)
            value = (value, value, value)
        self.setobjattr('scale', mathutils.Vector(value))

    @property
    def location(self): return self.getobjattr('location')
    @location.setter
    def location(self, value):
        if isinstance(value, (int,float)):
            value = float(value)
            value = (value, value, value)
        self.setobjattr('location', mathutils.Vector(value))

    @property
    def rotation_euler(self): return self.getobjattr('rotation_euler')
    @rotation_euler.setter
    def rotation_euler(self, value):
        if isinstance(value, (int,float)):
            value = float(value)
            value = (value, value, value)
        self.setobjattr('rotation_euler', value)

    @property
    def hide(self): return self.getobjattr('hide_viewport') and self.getobjattr('hide_render')
    @hide.setter
    def hide(self, value):
        self.setobjattr('hide_viewport', value)
        self.setobjattr('hide_render', value)

    def setActive(self):
        bpy.context.scene.objects.active = self._obj

class LazyObject(LazyBase):
    __slots__ = ['_generator']

    def __init__(self, init = None, *args, **kw):
        super().__init__(init, *args, **kw)
        self._generator = init

    def create(self, *args, **kw):
        if not self.created and self._generator:
            name = 'LazyObject' if 'name' not in self else self.name
            self._obj = self._generator(name, **self)
            self.update(*args, **kw)

        return self

    def update(self, *args, **kw):
        self._obj.update(*args, **kw)
        return self

class DummyObject(Object):
    __slots__ = []
    __overwrites__ = []

    def __init__(self, init = None, *args, **kw):
        super().__init__(None, *args, **kw)
        if init != None:
            self.name = str(init)

    @property
    def created(self): return True

    @property
    def _obj(self): return self

    @_obj.setter
    def _obj(self, _): pass

    def __repr__(self):
        return "<DummyObject(%s)>" % self.cache

    def remove(self):
        self.cache.clear()

    def create(self, *args, **kw):
        return super().update(*args, **kw)

    def update(self, *args, **kw):
        return super().update(*args, **kw)

    def keyframe_insert(self, *args, **kw):
        pass


def Empty(name = 'Empty', type = 'PLAIN_AXES', location = (0., 0., 0.), **kw):
    bpy.ops.object.empty_add(type=type, \
        radius=1., location=location)
    obj = Blender.active_object
    obj.name = name
    return Object(obj, **kw)
