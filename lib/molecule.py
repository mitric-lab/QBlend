
#import sys
#sys.path.append("/Users/hochej/.local/lib/python2.7/site-packages/")
import numpy as np
import abc, copy
from .utils import is_numeric, is_string, is_integer, iterable, normalized
from .utils import SlotPickleMixin, to_angstrom


from .residue import Residue
from .atom import Atom
from .bonds import Bonds
from .volume import VolumeData

class Molecule(SlotPickleMixin):
    '''
    molecule representation
    '''
    __metaclass__ = abc.ABCMeta
    __slots__ = ['_atoms', '_coords', '_bonds', '_com', '_coc', 'title', '_electronic_state',
                 '_residues', '_basis', '_volumes', '_modata', '_cidata', '_data']
    def __init__(self, init = None, *args, **kw):
        SlotPickleMixin.__init__(self)
        self._atoms = []
        self._coords = np.array([])
        self._bonds = Bonds()
        self._com = None
        self._coc = None
        self._residues = []
        self._basis = None
        self._volumes = {}
        self._modata = None
        self._cidata = None
        self._data = {}
        self._electronic_state = 0
        self.title = ""
        if isinstance(init, Molecule):
            self._atoms = copy.deepcopy(init._atoms)
            self._coords = init._coords.copy()
            self._residues = init._residues.copy()
            self._bonds = copy.deepcopy(init._bonds)
            self._com = init._com.copy()
            self._coc = init._coc.copy()
            self._volumes = init._volumes.copy()
            self._basis = init._basis.copy()
            self._modata = init._modata.copy()
            self._cidata = init._cidata.copy()
            self._electronic_state = init._electronic_state
            self.title = init.title
        elif init is not None:
            raise ValueError("Invalid molecule initialization")

    def __len__(self):
        return len(self._atoms)

    def __getitem__(self, i):
        if is_integer(i):
            assert i < len(self)
            return self._atoms[i], self._coords[i]
        if isinstance(i, slice):
            return zip(self._atoms[i], self._coords[i])

    def __setitem__(self, i, v):
        assert is_integer(i) and i < len(self)

        if isinstance(v, Atom): self._atoms[i] = v;
        elif isinstance(v, (int, str)): self._atoms[i] = Atom(v);
        elif iterable(v):
            assert len(v) in (2,3,4)
            try:
                if len(v) == 2:
                    self.__setitem__(i, v[0])
                    self.__setitem__(i, v[1])
                elif len(v) == 3:
                    self._coords[i] = np.array(v, dtype='float64')
                elif len(v) == 4:
                    self.__setitem__(i, v[0])
                    self.__setitem__(i, v[1:])
                else: raise ValueError()
            except ValueError:
                raise ValueError("Invalid value: %s" % str(v))
        else:
            raise ValueError("Invalid value: %s" % str(v))

    def __iter__(self):
        return iter(zip(self._atoms, self._coords))



    def __contains__(self, other):
        if isinstance(other, Atom):
            return other in self._atoms
        elif isinstance(other, Residue):
            return other in self._residues
        else:
            raise ValueError(other)



    def clear(self):
        self._atoms = []
        self._coords = np.array([])
        self._bonds = Bonds()
        self._residues = []
        self._com = None
        self._coc = None
        self._basis = None
        self._volumes = {}
        self._modata = None
        self._cidata = None
        self._data = {}

    def reset_bonds(self):
        self._bonds = Bonds()

    def resize(self, n):
        self._atoms = [Atom(i, None) for i in range(n)]
        self._coords = np.zeros((n, 3))


    @property
    def electronic_state(self): return self._electronic_state

    @electronic_state.setter
    def electronic_state(self, v): self._electronic_state = int(v)

    @property
    def basis(self): return self._basis


    @basis.setter
    def basis(self, value):
        if isinstance(value, Basisset) or value == None:
            self._basis = value
        else: raise ValueError(value)

    @property
    def volumes(self): return self._volumes

    @property
    def residues(self): return self._residues

    @property
    def modata(self): return self._modata

    @modata.setter
    def modata(self, value):
        if isinstance(value, MOData) or value == None:
            self._modata = value
        else: raise ValueError(value)

    @property
    def cidata(self): return self._cidata

    @cidata.setter
    def cidata(self, value):
        if isinstance(value, CIData) or value == None:
            self._cidata = value
        else: raise ValueError(value)

    @property
    def data(self): return self._data

    @property
    def atoms(self): return self._atoms

    @property
    def coords(self): return self._coords

    @property
    def vector(self):
        return np.reshape(self._coords, (-1))

    @property
    def connectivity(self): return self._bonds.connectivity

    @property
    def bonds(self): return self._bonds

    @bonds.setter
    def bonds(self, value):
        if isinstance(value, Bonds):
            self._bonds = value
        elif isinstance(value, list):
            self._bonds = Bonds()
            self._bonds.append(value)

    @property
    def angles(self): return self._bonds.angles

    @property
    def dihedrals(self): return self._bonds.dihedrals

    @property
    def bidihedrals(self): return self._bonds.bidihedrals


    def rings(self, planar = True, reduce = True):
        def is_reducible(c, other):
            for o in other:
                if len(o) < len(c) and set(o).issubset(c):
                    return True
            return False

        cycles = self._bonds.rings
        if planar:
            cycles = [cyc for cyc in cycles if self.is_planar(cyc)]

        if reduce:
            for i,ring in enumerate(cycles):
                if is_reducible(ring, cycles):
                    del cycles[i:]
        return cycles

    def bonded(self, i, j): return (i,j) in self._bonds



    def is_planar(self, ind = None, thrs = 0.1):
        """Returns whether list of atoms are coplanar"""

        if not ind:
            ind = range(len(self))
        ind = set([i for i in ind if is_integer(i)])
        if len(ind) == 3: return True

        ind = list(ind)
        for x in range(3, len(ind)):
            c1, c2, c3, c4 = [
                self.coords[ind[x - i]] for i in range(4)]
            v21 = normalized(c2 - c1)
            v43 = normalized(c4 - c3)
            v31 = normalized(c3 - c1)

            threshold = v31.dot(np.cross(v21,v43))
            if abs(threshold) > thrs:
                return False
        return True


    @property
    def com(self):
        if self._com is not None:
            return self._com

        M = 0.
        self._com = np.zeros(3)
        for atom, coord in self:
            M += atom.mass
            self._com += atom.mass * coord
        self._com /= M
        return self._com

    @property
    def coc(self):
        if self._coc is not None:
            return self._coc

        self._coc = np.zeros(3)
        for _, coord in self:
            self._coc += coord

        self._coc /= float(len(self))
        return self._coc

    def changed(self):
        self._com = None
        self._coc = None
        if self.basis is not None:
            for s in self.basis.shells:
                s.center = self.coords[s.icenter]



    def translate(self, vec):
        for _, coord in self:
            coord += vec

        for n, V in self.volumes.items():
            if V is not None:
                V.origin += vec
        self.changed()

        return self

    def distances(self, metric='sqeuclidean', **kw):
        dist = lambda p1, p2: ((p1-p2)**2).sum()
        dm = np.asarray([[dist(p1, p2) for p2 in self.coords] for p1 in self.coords])
        return dm

    def generate_bonds(self, tol=1.2, use_chain = True):
        if len(self._bonds) > 0:
            print("SKIPPED BONDS")
            return

        dcov = [a.covalent_radius for a in self.atoms]
        conn = [[] for i in range(len(self))]
        nbonds = 0
        natoms = len(self)
        chains = []
        if use_chain:
            lastchain = self.atoms[0].chainid
            chainstart = 0
            for i,atom in enumerate(self.atoms):
                if atom.chainid != lastchain or i+1 == len(self.atoms):
                    chains.append((chainstart, i+1))
                    chainstart = i
                    lastchain = atom.chainid
        else:
            chains.append((0, len(self)))



        for chstart, chstop in chains:
            #print(chstart, chstop)
            chainlen = chstop - chstart
            dist = lambda p1, p2: ((p1-p2)**2).sum()
            dists = np.asarray([[dist(p1, p2) for p2 in self.coords[chstart:chstop,:]] for p1 in self.coords[chstart:chstop,:]])
            #print(chstart, chstop, len(self.atoms))
            for i in range(chainlen):
                for j in range(i, chainlen):
                    ii, jj = chstart + i, chstart + j

                    if dists[i,j] > 0.01 and dists[i,j] <= ((dcov[ii]+dcov[jj])*tol)**2:
                        conn[ii].append(jj)
                        conn[jj].append(ii)
                        nbonds += 1
        print("BOONDS", conn, nbonds, len(self))
        self._bonds = Bonds(conn, nbonds, len(self))


    def append(self, other, *args):
        if isinstance(other, Atom):
            assert len(*args) > 0
            self.add_atom(other, *args)
        elif isinstance(other, Residue):
            self.add_residue(other)
        elif isinstance(other, Molecule):
            self.append_molecule(other)
        elif is_integer(other, (str)):
            assert len(*args) > 0
            self.add_atom(Atom(other), *args)
        else:
            raise ValueError(other)


    def find_residue(self, nm, nr = None, ic = None, chid = None):
        if isinstance(nm, Residue):
            res = nm
            nm = res.resnm
            nr = res.resnr
            ic = res.inscode
            chid = res.chainid

        assert is_string(nm)
        nm = Residue.convert_resnm(nm)

        for res in self.residues:
            if (not nm or nm == res.resnm) \
                and (not nr or int(nr) == res.resnr) \
                and (not ic or str(ic)[0] == res.inscode) \
                and (not chid or str(chid)[0] == res.chainid):
                return res
        return None

    def add_atom(self, atom, xyz, *args, **kw):
        assert iterable(xyz) and len(xyz) == 3 and is_numeric(xyz, 1)
        if is_integer(atom) or is_string(atom):
            atom = Atom(len(self), atom, *args, **kw)

        if not isinstance(atom, Atom):
            raise ValueError(atom)

        self._atoms.append(atom)

        if atom.residue is not None:
            atom.residue = self.add_residue(atom.residue)

        if self._coords.shape == (0,):
            self._coords = np.array([xyz], dtype='float64')
        else:
            self._coords = np.append(self._coords, [xyz], axis=0)



    def add_bond(self, *args):
        self._bonds.append(*args)

    def add_residue(self, other, *args):
        if not isinstance(other, Residue):
            other = Residue(other, *args)

        res = self.find_residue(other)
        if isinstance(res, Residue):
            return res
        else:
            self.residues.append(other)
            return other


    def add_volume(self, name, other, *args):
        if other is not None and not isinstance(other, VolumeData):
            other = VolumeData(other, *args)

        self._volumes[name] = other

    def add_data(self, name, other, *args):
        self._data[name] = other



    def append_molecule(self, other):
        atomoff = len(self)

        for atom, coord in other:
            self.add_atom(atom, coord)

        bfoff,shoff,mooff = 0, 0, 0
        if other.basis is not None:

            if not self.basis:
                self.basis = other.basis
            else:
                bfoff = len(self.basis)
                shoff = self.basis.nshells
                for s in other.basis.shells:
                    self.basis.append(s)

            for s in range(shoff, self.basis.nshells):
                icenter = self.basis.shells[s].icenter + atomoff
                self.basis.shells[s].icenter = icenter
                self.basis.shells[s].center = self.coords[icenter]
        if other.modata is not None:
            if self.modata is None:
                self.modata = other.modata
            else:
                mooff = self.modata.nmo
                self.modata.extend(other.modata)

        if other.cidata is not None:
            pass


        for name, vol in other.volumes.items():
            self.add_volume(name, vol)




    def reindex_atoms(self):
        oldind = {}
        for i,atom in enumerate(self.atoms):
            if i != atom.index:
                temp = self.coords[atom.index].copy()
                self.coords[atom.index] = self.coords[i]
                self.coords[i] = temp
                atom.index = i
                oldind[i] = atom.index


        self._bonds.replace_indices(oldind)
        for shell in self._basis.shells:
            ni = oldind[i] if shell.icenter in oldind else i
            shell.icenter = ni


    def sort_atoms(self):
        self._atoms.sort()
        self.reindex_atoms()

    def sort_residues(self):
        self._residues.sort()

    def sort_by_residue(self):
        self._atoms.sort(key=lambda x: (x.chainid, x.resnr, x.index))
        self.reindex_atoms()

    def atoms2orbs(self, atomind = None):
        if self.basis is None:
            raise Exception("No basis set available")

        if atomind is None:
            atomind = range(len(self))
        elif not iterable(atomind):
            atomind = [atomind]

        return [i for i,c in enumerate(self.basis.icenter_list()) if c in atomind]


    def natural_transition_orbitals(self, state = None, **kw):
        if state is None:
            state = self.electronic_state

        istate, fstate = self.cidata[0], self.cidata[state]
        return natural_transition_orbitals(self.modata, istate, fstate, **kw)

    def density_matrix(self):
        return self.modata.density_matrix()

    def transition_density_matrix(self, state = None):
        if state is None:
            state = self.electronic_state

        istate, fstate = self.cidata[0], self.cidata[state]
        return transition_density_matrix(self.modata, istate, fstate)

    """
    def orbital(self, mo):
        if self.modata is None:
            raise Exception("No molecular orbitals available")
        if self.basis is None:
            raise Exception("No basis set available")

        if isinstance(mo, str):

            if mo[0:4] == 'homo': f = self.modata.homo
            elif mo[0:4] == 'lumo': f = self.modata.lumo
            else: raise ValueError(mo)

            offset = 0
            if len(mo) > 4 and mo[4] in ('+', '-'):
                offset = int(mo[5:])
            mocoeffs = f(offset)
        else:
            mocoeffs = self.modata[mo]

        def func(x,y,z):
            return self.basis.value(x,y,z, mocoeffs)
        return func




    def density(self, state = 0):
        if not self.modata:
            raise Exception("No molecular orbitals available")
        if not self.basis:
            raise Exception("No basis set available")


        P = self.density_matrix() if state == 0 else self.transition_density_matrix(state)

        def func(x,y,z):
            bfvals = []
            for i in range(P.shape[0]):
                #print ("Orbital %d") % (i+1)
                bfvals.append(self.basis.bfvalue(i, x, y, z))

            val = P[0,0]*bfvals[0]**2
            for i in range(1, P.shape[0]):
                for j in range(1, P.shape[1]):
                    val += P[i,j]*bfvals[i]*bfvals[j]
            return val

        return func



    def tdensity(self, state = 0):
        if self.modata is None:
            raise Exception("No molecular orbitals available")
        if self.basis  is None:
            raise Exception("No basis set available")
        if self.cidata is None:
            raise Exception("No CI Data available")

        istate, fstate = self.cidata[0], self.cidata[state]
        hp = istate.hole_particle(fstate)
        orbitals = {}
        for (c, o, v) in hp:
            orbitals[o] = self.orbital(o)
            orbitals[v] = self.orbital(v)

        def func(x,y,z):
            bfvals = {}
            for o,f in orbitals.items():
                print ("Orbital %d" % (o))
                bfvals[o] = f(x, y, z)

            (c, o, v) = hp[0]
            val = c * bfvals[o] * bfvals[v]
            for i in range(1, len(hp)):
                (c, o, v) = hp[i]
                print ("%3d -> %3d (%f)" % (o, v, c))
                val += c * bfvals[o] * bfvals[v]

            return val

        return func

    """



    def boundary_box(self, rel_thr = 0.0, abs_thrs = 0.0, min_size = 1.0):
        a = self.coords.min(axis=0)
        b = self.coords.max(axis=0)


        for i in range(3):
            d = b[i]-a[i]
            if d < min_size:
                a[i] -= (min_size-d)/2.

        diff = b-a
        off = np.maximum(diff*rel_thr, np.full(3, abs_thrs))

        return a-off,b+off


    def __str__(self):
        s = "Atoms: %d\n" % len(self);
        for atom, coord in zip(self.atoms, self.coords):
            s += "    %s  %12.8f %12.8f %12.8f\n" % (str(atom), coord[0], coord[1], coord[2])

        if len(self.residues):
            s += "Residues: %d\n" % len(self.residues)
            for res in self.residues:
                s += "Residue  %-3.3s%-2d %1.1s (%d)\n" % (res.resnm, res.resnr, res.chainid, len(res))

        if self.basis:
            s += "Basis: %d\n" % len(self.basis)
            s += str(self.basis) + "\n"

        if self.modata:
            s += "MO: %d\n" % len(self.modata)
            s += str(self.modata)+ "\n"
        if self.cidata:
            s += "CI: %d\n" % len(self.cidata)
            s += str(self.cidata)+ "\n"

        if len(self.volumes):
            s += "Volumes: %d\n" % len(self.volumes)
            for name, vol in self.volumes.items():
                s += "    %-10s  %s\n" % (name, vol)
        return s

    def __repr__(self):
        return "<Molecule(A=%d, R=%d, V=%d)>" % (len(self), len(self.residues), len(self.volumes))
