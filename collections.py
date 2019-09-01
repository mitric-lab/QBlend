import bpy
from . import Blender
from .base import Object, Empty, Material, LazyMaterial


class ObjectCollection(Object):
    __slots__ = ['_objects']
    __overwrites__ = ['hide', 'select']
    def __init__(self, init = None, *args, **kw):
        if not init:
            init = 'ObjectCollection'
        if isinstance(init, str):
            if init == "BOND":
                self._objects = []
                super().__init__(init, **kw)
            print("NAME", init)
            # We need to initialize the base to set _bpy
            super().__init__(init, **kw)
            pass
            #super().__init__(Empty(init), **kw)
        else:
            super().__init__(init, **kw)

        self._objects = []

        for a in args:
            self.append(a)


    @property
    def back(self):
        print("OBJECTS",self.objects)
        return self._objects[-1]

    @property
    def front(self): return self._objects[0]

    def append(self, obj):
        print("APPEND")
        if isinstance(obj, Object):
            self._objects.append(obj)
        else:
            self._objects.append(Object(obj))

        if self.created and self.back.created:
            print("SELF_BACK_PARENT")
            self.back.parent = self._bpy
            print("SELF_BACK_PARENT_END")

    def __len__(self):
        return len(self._objects)

    def __iter__(self):
        return iter(self._objects)

    def __delitem__(self, i):
        self._objects[i].remove()
        del self._objects[i]

    def __getitem__(self, i):
        return self._objects[i]

    def __setitem__(self, i, v):
        self._objects[i].parent = None
        self._objects[i] = v
        if self.created:
            self._objects[i].parent = self._bpy


    @property
    def hide(self):
        value = self.getobjattr('hide') and self.getobjattr('hide_render')
        for o in self:
            value = value and o.hide
        return value
    @hide.setter
    def hide(self, value):
        for o in self:
            o.hide = bool(value)
        self.setobjattr('hide', bool(value))
        self.setobjattr('hide_render', bool(value))

    @property
    def select(self):
        value = self.getobjattr('select')
        for o in self:
            value = value and o.select
        return value
    @select.setter
    def select(self, value):
        for o in self:
            o.select= bool(value)
        self.setobjattr('select', bool(value))
        self.setActive()


    def copy(self, **kw):
        clone = super().copy(**kw)
        for c in self:
            clone.append(c.copy(**kw))

        return clone

    def create(self, *args, **kargs):
        super().create(*args, **kargs)
        for c in self:
            c.create(*args, **kargs)
            if self.created and c.created:
                c.parent = self._bpy

        return self

    def update(self, *args, **kargs):
        super().update(*args, **kargs)
        for c in self:
            c.update(*args, **kargs)

        return self


class MaterialCollection(object):
    default_props = {
            'diffuse_color': (.2, .2, .2)
            }


    def __init__(self, **kw):
        self.__materials = {}
        self.lazy = 'lazy' in kw and kw['lazy']
        self.always_clone = 'always_clone' in kw and kw['always_clone']
        for k, v in kw.items():
            if k not in ('always_clone', 'lazy'):
                self.default_props[k] = v

    def setDefault(self, name, value):
        self.default_props[name] = value


    def __getitem__(self, name):
        if name not in self.__materials:
            if self.lazy:
                self.new(name)
            else: raise KeyError(name)

        if not self.__materials[name].created:
            self.__materials[name].create(**self.default_props)
        return self.__materials[name]


    def __setitem__(self, name, value):
        if name in self.__materials:
            self.remove(name)

        if isinstance(value, Material):
            self.__materials[name] = value.copy() if self.always_clone else value
        elif isinstance(value, bpy.types.Material):
            self.__materials[name] = Material(name)
            self.__materials[name]._obj = value.copy() if self.always_clone else value
        #self.__materials[name].update(**self.default_props)


    def new(self, key, name = None, **kargs):
        if name == None: name = str(key)

        if self.lazy:
            self.__materials[key] = LazyMaterial(name, **self.default_props)
        else:
            self.__materials[key] = Material(name, **self.default_props)

        self.__materials[key].update(**kargs)
        return self.__materials[key]

    def remove(self, name, do_unlink = True):
        if name in self.__materials:
            self.__materials[name].remove(do_unlink = do_unlink)

        return self

    def update(self):
        for mat in self.__materials.values():
            mat.update(**self.default_props)

    def copy(self, **kw):
        clone = self.__class__()
        for k,v in self.__materials.items():
            clone[k] = v.copy(**kw)

        return clone
