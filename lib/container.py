from .utils import iterable, flatten

def reduce_dict(inp, other = None):
    assert isinstance(inp, dict)
    assert other == None or isinstance(other, map)
    resmap = {} if not other else other

    for k, v in inp.items():
        if isinstance(v, dict):
            for k2, v2 in reduce_dict(v).items():
                resmap["%s.%s" % (k, k2)] = v2
        else:
            resmap[k] = v
    return resmap

def expand_dict(inp):
    resmap = {}
    for name, v in sorted(inp.items(), key=lambda x: x[0]):
        cur = resmap
        i = name.find('.')
        while i > 0:
            name, sub = name[:i], name[i+1:]
            if name not in cur or not isinstance(cur[name], dict):
                cur[name] = {}
            cur = cur[name]
            name = sub
            i = name.find('.')
        cur[name] = v
    return resmap



class AttrDict(dict):
    __slots__ = []
    def __init__(self, values = None):
        super(AttrDict, self).__init__()
        if isinstance(values, dict):
            self.from_dict(values)

    def __len__(self):
        n = 0
        for v in self.values():
            n += len(v) if isinstance(v, AttrDict) else 1
        return n

    def __getitem__(self, name):
        try:
            if isinstance(name, str):
                i = name.find('.')
                if i == -1:
                    return super(AttrDict, self).__getitem__(name)
                else:
                    first, sub = name[:i], name[i+1:]
                    if isinstance(super(AttrDict, self).__getitem__(first), AttrDict):
                        return super(AttrDict, self).__getitem__(first)[sub]
                    else:
                        raise KeyError(name)

            else:
                return super(AttrDict, self).__getitem__(name)
        except KeyError:
            raise KeyError(name)


    def __delitem__(self, name):
        if isinstance(name, str):
            i = name.find('.')
            if i == -1:
                return super(AttrDict, self).__delitem__(name)
            else:
                first, sub = name[:i], name[i+1:]
                try:
                    super(AttrDict, self).__delitem__(first)[sub]
                except KeyError:
                    raise KeyError(name)
        else:
            super(AttrDict, self).__delitem__(name)

    def __setitem__(self, name, value):
        if isinstance(name, str):
            i = name.find('.')
            if i == -1:
                if isinstance(value, dict) and not isinstance(value, AttrDict):
                    if name not in self or not isinstance(self[name], AttrDict):
                        super(AttrDict, self).__setitem__(name, AttrDict(None))
                    for k, v in value.items():
                        super(AttrDict, self).__getitem__(name)[k] = v
                else:
                    super(AttrDict, self).__setitem__(name, value)
            else:
                name, sub = name[:i], name[i+1:]
                if name not in self or not isinstance(self[name], AttrDict):
                    super(AttrDict, self).__setitem__(name, AttrDict(None))
                self[name][sub] = value
        else:
            super(AttrDict, self).__setitem__(name, value)


    def __getattr__(self, name):
        try:
            if name[0] == '_':
                return super(AttrDict, self).__getattr__(name)
            else:
                if name not in self:
                    super(AttrDict, self).__setitem__(name, AttrDict(None))
                return self.__getitem__(name)
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name[0] == '_':
            super(AttrDict, self).__setattr__(name, value)
        else:
            self.__setitem__(name, value)

    def __delattr__(self, name):
        if name[0] == '_':
            super(AttrDict, self).__delattr__(name)
        else:
            self.__delitem__(name)


    def from_dict(self, values):
        if isinstance(values, dict):
            for k, v in values.items():
                self.__setitem__(k, v)

    def reduce(self):
        return reduce_dict(self)

    def copy(self):
        return AttrDict(super().copy())

    def __contains__(self, name):
        if isinstance(name, str):
            i = name.find('.')
            if i == -1:
                return super(AttrDict, self).__contains__(name)
            else:
                name, sub = name[:i], name[i+1:]
                return super(AttrDict, self).__contains__(name) \
                    and isinstance(self[name], AttrDict) \
                    and self[name].__contains__(sub)
        else:
            return super(AttrDict, self).__contains__(name)

    def attr_items(self):
        def attriter(items):
            for k, v in items:
                if isinstance(v, AttrDict):
                    for k2, v2 in v.attr_items():
                        yield ("%s.%s" % (k, k2), v2)
                else:
                    yield k, v

        return attriter(self.items())

    def attr_keys(self):
        def attriter(items):
            for k, v in items:
                if isinstance(v, AttrDict):
                    for k2 in v.attr_keys():
                        yield "%s.%s" % (k, k2)
                else:
                    yield k

        return attriter(self.items())

    def attr_values(self):
        def attriter(items):
            for v in items:
                if isinstance(v, AttrDict):
                    for v2 in v.attr_values():
                        yield v2
                else:
                    yield v

        return attriter(self.values())


class RangeList:
    __slots__ = ['ind']
    def __init__(self, ind, unique = True):

        self.from_list(ind)

    def __iter__(self):
        def RangeIter(ind):
            for i in ind:
                if iterable(i):
                    for j in i: yield j
                else: yield i

        return RangeIter(self.ind)

    def __len__(self):
        n = 0
        for i in self.ind:
            if iterable(i): n += len(i)
            elif i == ind: n += 1
        return n


    def __contains__(self, ind):
        for i in self.ind:
            if iterable(i) and ind in i: return True
            elif i == ind: return True
        return False

    def __repr__(self):
        return "<RangeList(%d)>" % len(self)


    def to_list(self):
        return [i for i in self]

    def from_list(self, ind, unique = True):
        if len(ind) == 0: return
        ind = flatten(ind)
        if unique:
            ind = set(ind)
        ind = list(ind)
        self.ind = []
        start, stop = ind[0], ind[0]
        for i in ind[1:]:
            if i == stop+1:
                stop = i
            else:
                self.ind.append(range(start,stop+1))
                start, stop = i,i
        if start != stop+1:
            self.ind.append(range(start,stop+1))
