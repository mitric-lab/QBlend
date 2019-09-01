from .utils import flatten, iterable, is_integer
from .container import RangeList

from .atom import Atom
from .residue import Residue
from .molecule import Molecule
from . import elements

import numpy as np

class Filter(object):
    pass

class UnaryFilter(object):
    __slots__ = ['func']
    def __init__(self, f = None):
        self.func = f

    def __call__(self, *args, **kw):
        if self.func == None: return True
        elif isinstance(self.func, bool): return self.func
        elif callable(self.func): return self.func(*args, **kw)
        elif hasattr(self.func, '__contains__'): return args in self.func
        else: raise ValueError(self.func)

    def __and__(self, other):
        return AndFilter(self, other)

    def __or__(self, other):
        return OrFilter(self, other)

    def __invert__(self):
        return NegateFilter(self)

    def __repr__(self):
        return "<%s(%s)>" % (self.__class__.__name__, repr(self.func))

class NegateFilter(UnaryFilter):
    def __call__(self, *args, **kw):
        return not super(NegateFilter, self).__call__(*args, **kw)

    def __invert__(self):
        return self.func

    def __repr__(self):
        return "(not %s)" % (super(NegateFilter, self).__repr__())

class BinaryFilter(object):
    __slots__ = ['rhs', 'lhs']

    def __init__(self, lhs = None, rhs = None):
            self.rhs = rhs
            self.lhs = lhs

    def eval_rhs(self, *args, **kw):
        if self.rhs == None: return True
        elif isinstance(self.rhs, bool): return self.rhs
        elif callable(self.rhs): return self.rhs(*args, **kw)
        else: raise ValueError(self.rhs)

    def eval_lhs(self, *args, **kw):
        if self.lhs == None: return True
        elif isinstance(self.lhs, bool): return self.lhs
        elif callable(self.lhs): return self.lhs(*args, **kw)
        else: raise ValueError(self.lhs)

    def __call__(self, *args, **kw):
        raise ValueError("Unknown binary operation")

    def __and__(self, other):
        return AndFilter(self, other)

    def __or__(self, other):
        return OrFilter(self, other)

    def __invert__(self):
        return NegateFilter(self)

    def __repr__(self):
        return "(%s and %s)" % (repr(self.rhs), repr(self.lhs))


class AndFilter(BinaryFilter):
    def __call__(self, *args, **kw):
        return self.eval_lhs(*args, **kw) and self.eval_rhs(*args, **kw)

class OrFilter(BinaryFilter):
    def __call__(self, *args, **kw):
        return self.eval_lhs(*args, **kw) or self.eval_rhs(*args, **kw)


class AtomFilter(UnaryFilter):
    def __init__(self, f = None):
        super(AtomFilter, self).__init__(f)

    def __call__(self, mol, atom):
        if not isinstance(mol, Molecule):
            raise ValueError(type(mol))

        if is_integer(atom):
            return super(AtomFilter, self).__call__(mol, mol.atoms[atom])
        elif isinstance(atom, Atom):
            return super(AtomFilter, self).__call__(mol, atom)
        else:
            raise ValueError(type(atom))


class ResidueFilter(UnaryFilter):
    def __init__(self, f):
        super(ResidueFilter, self).__init__(f)
    def __call__(self, mol, res):
        if not isinstance(mol, Molecule):
            raise ValueError(type(mol))


        if is_integer(res):
            return super(ResidueFilter, self).__call__(mol, mol.residues[res])
        elif isinstance(res, Atom):
            if res.residue == None: return False
            else:
                #print("ResidueFilter", res, super(ResidueFilter, self).__call__(mol, res.residue))
                return super(ResidueFilter, self).__call__(mol, res.residue)
        elif isinstance(res, Residue):
            return super(ResidueFilter, self).__call__(mol, res)
        else:
            raise ValueError(type(res))

class CoordFilter(UnaryFilter):
    def __init__(self, f):
        super(CoordFilter, self).__init__(f)
    def __call__(self, mol, coord):
        if not isinstance(mol, Molecule):
            raise ValueError(type(mol))

        if is_integer(coord):
            return super(CoordFilter, self).__call__(mol, mol.coords[coord])
        elif isinstance(coord, Atom):
            return super(CoordFilter, self).__call__(mol, mol.coords[coord.index])
        elif isinstance(coord, np.ndarray):
            return super(CoordFilter, self).__call__(mol, coord)
        else:
            raise ValueError(type(coord))

def AtomIndexFilter(ind):
    def f(_, atom):
        return atom.index in ind

    if is_integer(ind): ind = [ind]
    ind = RangeList(ind, unique= True)
    return AtomFilter(f)

def AtomElementFilter(element):
    if not iterable(element): element = [element]
    element = flatten(element)

    nrs = []

    for i,e in enumerate(element):
        if is_integer(e): nrs.append(e)
        elif isinstance(e, str): nrs.append(elements.by_symbol(e).number)
        else: nrs.append(e.number)


    return AtomFilter(lambda _, atom: atom.element.number in nrs)

def AtomSymbolFilter(sym):
    return AtomElementFilter(elements.by_symbol(sym))

def AtomNameFilter(nm):
    if isinstance(nm, tuple):
        nm = tuple(map(lambda x: x.upper(), nm))
        f = lambda _, atom: atom.name.upper() in nm
        #def f(_, res): return res.resnm in nm
    else:
        nm = nm.upper()
        f = lambda _, atom: nm == atom.name.upper()
        #def f(_, res):
        #    print(nm, res.resnm)
        #    return nm == res.resnm

    return AtomFilter(f)

def AtomResidueFilter(resfilter):
    return AtomFilter(lambda mol, atom: atom.residue != None and resfilter(mol, atom.residue))

def ResidueNameFilter(nm):
    if isinstance(nm, tuple):
        nm = tuple(map(lambda x: x.upper(), nm))
        f = lambda _, res: res.resnm in nm
        #def f(_, res): return res.resnm in nm
    else:
        nm = nm.upper()
        f = lambda _, res: nm == res.resnm
        #def f(_, res):
        #    print(nm, res.resnm)
        #    return nm == res.resnm

    return ResidueFilter(f)

def ResidueTypeFilter(nm):
    if isinstance(nm, tuple):
        nm = tuple(map(lambda x: x.upper(), nm))
        f = lambda _, res: res.restype in nm
    else:
        nm = nm.upper()
        f = lambda _, res: nm == res.restype
    return ResidueFilter(f)

def ResidueChainFilter(ch):
    if isinstance(ch, tuple):
        f = lambda _, res: res.chainid in ch
    else:
        f = lambda _, res: ch == res.chainid
    return ResidueFilter(f)

def ResidueNumberFilter(ind):
    if is_integer(ind): ind = [ind]
    ind = flatten(ind)
    return ResidueFilter(lambda _, res: res.resnr in ind)
