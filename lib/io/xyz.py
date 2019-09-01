import numpy as np
from .molio import MoleculeFile, EOFError
from ..molecule import Molecule, Atom, Residue

from ..utils import from_angstrom, to_angstrom

class XyzFile(MoleculeFile):
    __slots__ = []
    FEATURES = {
        'trajectory': True,
        'volume': False,
        'basis': False,
        'loading': True,
        'saving': True,
        }

    def __init__(self, *args, **kw):
        super(XyzFile, self).__init__(*args, **kw)

    def _read(self, mol, **kw):
        assert self.loading
        assert mol != None and isinstance(mol, Molecule)

        new_mol = self.is_first
        natoms = 0
        iatom = 0

        try:
            natoms = int(self.readline())

            if natoms != self.natoms or natoms != len(mol):
                mol.clear()
                new_mol = True

            mol.title = self.readline()


            for _ in range(natoms):
                line = self.readline().split()
                if len(line) < 4:
                    raise IOError(line)
                sym, coords = line[0], line[1:4]
                atom = Atom(iatom, sym)
                coords = np.array(from_angstrom(coords))
                self.add_atom(new_mol, mol, atom, coords)
                iatom += 1


        except EOFError:
            pass
        except:
            print("ERROR LINE: %d" % self._iline)
            print(line)
            raise

        if iatom == 0:
            return None

        if iatom != natoms:
            raise IOError("Unexpected End of File")

        if self.connect_atoms:
            mol.generate_bonds()

        self.frame += 1
        return mol

    def _write(self, mol, **kw):
        assert self.saving
        assert mol != None and isinstance(mol, Molecule)

        self.writeline("%d\n%s" % (len(mol), mol.title[:mol.title.find('\n')]))
        for atom, coord in mol:
            if self.test(mol,atom,coord):
                self.writeline("%-2s %16.8f %16.8f %16.8f" % (atom.symbol, \
                    to_angstrom(coord[0]), to_angstrom(coord[1]), to_angstrom(coord[2])))
        self.frame += 1
        return True
