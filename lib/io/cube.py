import numpy as np
from .molio import MoleculeFile, EOFError
from ..molecule import Molecule, Atom, Residue
from ..volume import VolumeData
from ..utils import from_angstrom, to_angstrom, iterable

class CubeFile(MoleculeFile):
    __slots__ = []
    FEATURES = {
        'trajectory': False,
        'volume': True,
        'basis': False,
        'loading': True,
        'saving': True,
        }

    def __init__(self, *args, **kw):
        super(CubeFile, self).__init__(*args, **kw)


    def _read(self, mol, volind = 0):
        assert self.loading
        assert mol != None and isinstance(mol, Molecule)

        natoms = 0
        iatom = 0
        lconv = 1.

        mol.clear()

        try:
            mol.title = self.readline().strip()
            mol.title += "\n"+self.readline().strip()

            line = self.readline().split()
            natoms, origin = int(line[0]), np.array(line[1:4], dtype=float)

            if natoms > 0:
                lconv = 1.#from_angstrom(1.0)
            natoms = abs(natoms)

            origin *= lconv

            nvol = 1 if len(line) == 4 else int(line[4])
            hasnvol = len(line) > 4
            shape = np.zeros(3, dtype=int)
            dx = np.zeros((3,3), dtype=float)
            for i in range(3):
                line = self.readline().split()
                shape[i] = int(line[0])
                dx[i] = np.array(line[i+1], dtype=float)*lconv

            for i in range(natoms):
                line = self.readline().split()
                Z, q, coords = int(line[0]), float(line[1]), np.array(list(map(float, line[2:5])))
                atom = Atom(iatom, Z)
                atom.partial_charge = q
                self.add_atom(True, mol, atom, coords*lconv)
                iatom += 1

            if iatom != natoms:
                raise StopIteration("Too few atoms")

            labels = []
            if hasnvol:
                line = self.readline().split()
                line[0] = int(line[0])
                if line[0] != nvol or line[0]+1 != len(line):
                    raise RuntimeError("Unknown volume declaration")
                for l in line[1:]:
                    labels.append("%s" % l)
            else:
                labels = ['CubeData']


            data = [VolumeData(origin, shape, dx) for _ in range(nvol)]
            line = []
            nl = 0
            ndata = 0
            for i,j,k in data[0].indices():
                for l in range(nvol):
                    if nl == len(line):
                        line = self.readline().split()
                        nl = 0
                    data[l][i,j,k] = float(line[nl])
                    nl += 1
                    ndata += 1

            if ndata != shape[0]*shape[1]*shape[2]*nvol:
                raise StopIteration("Too few points")

            for name, vol in zip(labels, data):
                mol.add_volume(name, vol)

        except EOFError:
            return None

        if self.connect_atoms:
            mol.generate_bonds()

        self.frame += 1
        return mol


    def select_volumes(self, mol, *args):
        volumes, volnames = [], []
        for v in args:
            if isinstance(v, str):
                if v not in mol.volumes:
                    raise RuntimeError("Volume "+ v +" not available")
                volumes.append(mol.volumes[v])
                volnames.append(v)
            elif isinstance(v, VolumeData):
                volumes.append(v)

        return volumes, volnames


    def _write(self, mol, *args, **kw):
        assert self.saving
        assert mol != None and isinstance(mol, Molecule)

        volumes, volnames = [], []
        if 'volume' in kw:
            volumes, volnames = self.select_volumes(mol, kw['volume'])
        elif len(args) > 0:
            volumes, volnames = self.select_volumes(mol, *args)
        else:
            volumes, volnames = self.select_volumes(mol, * tuple(mol.volumes.keys()))

        if len(volumes) == 0:
            print("No volumetric data available.")
            volumes.append(VolumeData())

        nvol = len(volumes)
        angstrom = ('anstrom' in kw and kw['angstrom']) or nvol > 1
        lconv = to_angstrom(1.) if angstrom else 1.
        natoms = len(mol)
        vol0 = volumes[0]

        eol = mol.title.find("\n")
        self.writeline("%s", mol.title[:eol] if len(mol.title) > 0 else "Generated cube file")
        self.writeline("%s", ", ".join(volnames) if len(volnames) else "X-Y-Z Loop")

        ox, oy, oz = vol0.origin
        if nvol > 1:
            self.writeline("%5d %11.6f %11.6f %11.6f%5d" \
                    % (-natoms if angstrom else natoms, \
                       ox*lconv, oy*lconv, oz*lconv, nvol))
        else:
            self.writeline("%5d %11.6f %11.6f %11.6f" \
                    % (-natoms if angstrom else natoms, \
                       ox*lconv, oy*lconv, oz*lconv))


        for i in range(3):
            line = "%5d %11.6f %11.6f %11.6f" \
                % (vol0.shape[i], \
                   vol0.step[i]*lconv if i == 0 else 0.0, \
                   vol0.step[i]*lconv if i == 1 else 0.0, \
                   vol0.step[i]*lconv if i == 2 else 0.0)
            self.writeline(line)

        for atom, coord in mol:
            line = "%5d %11.6f %11.6f %11.6f %11.6f" \
                % (atom.number, atom.partial_charge, coord[0]*lconv, coord[1]*lconv, coord[2]*lconv)
            self.writeline(line)

        if nvol > 1:
            line = ("%5d") % nvol
            i = 1
            for n in range(nvol):
                if i%10 == 0: line+='\n'
                line += ("%5d") % (n+1)
                i += 1

            self.writeline(line)

        n = 0
        zdim = vol0.shape[2]
        for i,j,k in vol0.indices():
            for v in range(nvol):
                if n > 0 and ((n%6) == 0 or (n%(zdim*nvol)) == 0):
                    self.writeword('\n')
                    n = 0
                ijkval = volumes[v][i,j,k]
                #self.writeword(" %12.5E" % (ijkval if abs(ijkval) > 1E-8 else 0.0))
                self.writeword(" %12.5E" % ijkval)
                n += 1
