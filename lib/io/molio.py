from ..filter import Filter, UnaryFilter, BinaryFilter, \
                     AtomFilter, ResidueFilter, CoordFilter

from ..molecule import Molecule, Atom, Residue
from ..utils import is_file, get_filemode

def name2sym(self,name):
    sym = ""
    name = name.lower().capitalize()
    for s in name:
        if s.isalpha():
            sym += s
            if elements.by_symbol(sym) != 0:
                break
    return sym


class MoleculeFilter(UnaryFilter):
    __slots__ = []
    def __init__(self, f):
        if f == None: return True
        elif isinstance(f, AtomFilter):
            pass
        elif isinstance(f, ResidueFilter):
            pass
        elif isinstance(f, CoordFilter):
            pass
        elif isinstance(f, UnaryFilter):
            f = MoleculeFilter(f)
        elif isinstance(f, BinaryFilter):
            f = f.__class__(MoleculeFilter(f.lhs), MoleculeFilter(f.rhs))

        super(MoleculeFilter, self).__init__(f)

    def __call__(self, mol, atom, coord):
        if isinstance(self.func, AtomFilter):
            return super(MoleculeFilter, self).__call__(mol, atom)
        elif isinstance(self.func, ResidueFilter):
            return super(MoleculeFilter, self).__call__(mol, atom.residue)
        elif isinstance(self.func, CoordFilter):
            return super(MoleculeFilter, self).__call__(mol, coord)
        else:
            return super(MoleculeFilter, self).__call__(mol, atom, coord)

    def __repr__(self):
        return super(MoleculeFilter, self).__repr__()

class EOFError(IOError):
    pass

class MoleculeFile(object):
    FEATURES = {}
    __slots__ = ['_fp', 'mol', 'filename', 'mode', 'frame', 'natoms', \
                 '_filter', '_ignore_empty', 'connect_atoms', '_lastpos', '_labels',
                 '_iline']
    def __init__(self, source = None, mode = 'r', mol = None, atom_filter = None, *args, **kw):
        super(MoleculeFile, self).__init__()
        self._fp = None
        self._ignore_empty = False
        self._lastpos = 0
        self._labels = {}
        self._iline = 0

        self.mol = None
        self.frame = 0
        self.natoms = 0
        self.connect_atoms = 'connect_atoms' in kw and kw['connect_atoms']

        if isinstance(source, MoleculeFile):
            self._fp = source._fp
            self.filter = source.filter
            self.mol = source.mol
            self.mode = source.mode
            self.natoms = source.natoms


        elif isinstance(source, str):
            self.open(source, mode)
        elif is_file(source):
            self.mode = get_filemode(source)
            self._fp = source

        self.filter = atom_filter
        self.mol = mol


    def __del__(self):
        if self.is_open: self.close()

    def __enter__(self):
        return self

    def __exit__(self):
        if self.is_open: self.close()

    def open(self, filename, mode='r'):
        if self.is_open: self.close()

        if 'r' in mode and not self.has_feature('loading'):
            raise Exception('Can not read such file format')
        if 'w' in mode and not self.has_feature('saving'):
            raise Exception('Can not write such file format')
        self.mode = mode
        self.filename = filename
        self._fp = open(filename, mode)
        self._lastpos = self._fp.tell()
        self._iline = 0

        self.frame = 0
        self.natoms = 0
        return self

    @property
    def is_first(self):
        return self.frame == 0

    @property
    def filter(self):
        return self._filter
    @filter.setter
    def filter(self, value):
        if value == None: self._filter = None
        elif callable(value):

            self._filter = value if isinstance(value, MoleculeFilter) else MoleculeFilter(value)
        else:
            raise ValueError(filter)

    def test(self, mol, atom = None, coord = None):
        return self.filter == None or self.filter(mol, atom, coord)

    def add_atom(self, new_mol, mol, atom, coords):
        if self.test(mol,atom,coords):
            if new_mol:
                mol.append(atom, coords)
            else:
                if atom.index < len(mol):
                    mol.coords[atom.index] = coords
                else:
                    raise IndexError(atom.index)
            return True
        else: return False

    def close(self):
        if self.is_open:
            self._fp.close()
            self._fp = None

    @property
    def is_open(self):
        return self._fp != None

    def __bool__(self):
        return self._fp != None

    @property
    def fp(self): return self._fp

    @property
    def loading(self): return self.is_open and 'r' in self.mode and self.has_feature('loading')

    @property
    def saving(self): return self.is_open and 'w' in self.mode and self.has_feature('saving')


    def has_feature(self, feature):
        return str(feature) in self.FEATURES and self.FEATURES[feature]

    def tell(self): return self._fp.tell()

    def seek(self, pos):
        self._lastpos = self.tell()
        self._fp.seek(pos)

    def goto_last(self):
        self.seek(self._lastpos)

    def set_label(self, name):
        self._labels[name] = self._lastpos

    def goto_label(self, name):
        self.seek(self._labels[name])

    def has_label(self, name):
        return name in self._labels

    def readline(self, ignore_empty = None):
        assert self.loading

        ignore_empty = ignore_empty if ignore_empty != None else self._ignore_empty

        self._lastpos = self.tell()
        line = self._fp.readline()
        self._iline += 1

        if not line:
            raise EOFError
        elif ignore_empty and len(line) == 1 and line[0] == '\n':
            return self.readline(ignore_empty)

        return line.strip()


    def skiplines(self, n = 1, ignore_empty = None):
        assert self.loading

        ignore_empty = ignore_empty if ignore_empty != None else self._ignore_empty
        n = max(n, 0)
        while n > 0:
            self._lastpos = self.tell()
            line = self._fp.readline()
            self._iline += 1
            if not line:
                raise EOFError
            elif ignore_empty and len(line) == 1 and line[0] == '\n':
                pass
            else: n -= 1

        return line.strip()

    def readlines(self, ignore_empty = None):
        try:
            while True:
                yield self.readline(ignore_empty)
        except EOFError:
            raise StopIteration



    def scan(self, labels, allow_mult = False, use_match = False):
        lastpos = self.tell()

        try:
            for line in self.readlines():
                which = None
                for key, regex in labels.items():
                    if use_match:
                        match = regex.match(line)
                    else:
                        match = regex.search(line)
                    if match:
                            which = key, match
                            break

                if which and ( not self.has_label(which[0]) or (allow_mult and self.has_label(which[0]))):
                    x, match = which
                    #if not allow_mult and self.has_label(x):
                    #    raise RuntimeError("Double label '%s' found in line %d" % (x, self._iline))

                    self.set_label(x)
                    yield x, match

        except StopIteration:
            self.seek(lastpos)
            raise




    def writeline(self, line, *args):
        assert self.saving
        if len(args): line = line % args
        self.fp.write(line +"\n")

    def writeword(self, line, *args):
        assert self.saving
        if len(args): line = line % args
        self.fp.write(line)

    def read(self, mol = None, *args, **kw):
        if isinstance(mol, MoleculeFile):
            mol = mol.mol
        elif isinstance(mol, Molecule):
            pass
        elif mol == None:
            if self.mol == None:
                self.mol = Molecule()
            mol = self.mol
        else:
            raise ValueError(mol)


        if 'clear' in kw and kw['clear']:
            mol.clear()

        return self._read(mol, *args, **kw)

    def write(self, mol = None, *args, **kw):
        assert self.saving
        try:
            if isinstance(mol, MoleculeFile) and mol.loading:
                mol = mol.read()
                return self._write(mol, *args, **kw)
            elif isinstance(mol, Molecule):
                return self._write(mol, *args, **kw)
            elif mol == None:
                return self._write(self.mol, *args, **kw)
            else:
                raise ValueError(mol)
        except:
            raise
            return False
        return True

    def _write(self, mol):
        raise NotImplemented()

    def _read(self, mol):
        raise NotImplemented()
