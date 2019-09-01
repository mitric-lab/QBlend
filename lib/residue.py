import copy
from .atom import Atom
from .utils import SlotPickleMixin

class Residue(SlotPickleMixin):
    __slots__ = ['resnm', 'resnr', 'inscode', 'chainid', '_atoms']
    def __init__(self, name, nr = 0, inscode = ' ', chid = ' '):
        SlotPickleMixin.__init__(self)
        self.resnm = Residue.convert_resnm(name)
        self.resnr = int(nr)
        self.inscode = ' ' if not inscode else str(inscode[0])
        self.chainid = ' ' if not chid else str(chid[0])
        self._atoms = []


    @staticmethod
    def convert_resnm(nm):
        nm = str(nm).upper()
        return ResidueNames.get(nm, nm)

    @property
    def restype(self):
        return ResidueTypes.get(self.resnm, "OTHER")

    def __len__(self): return len(self.atoms)

    def __eq__(self, other):
        if other == None: return False
        elif isinstance(other, str): return self.resnm == other.resnm
        elif isinstance(other, Residue):
            return self.resnm == other.resnm \
                and self.resnr == other.resnr \
                and self.inscode == other.inscode \
                and self.chainid == other.chainid
        elif isinstance(other, tuple):
            if len(other) == 1: return self.__eq__(tuple[1])
            if len(other) == 2: return (self.resnm, self.resnr) == other
            if len(other) == 3: return (self.resnm, self.resnr, self.chainid) == other
        else: raise ValueError(other)

    def __lt__(self, other):
        if isinstance(other, int):
            return self.resnr < other
        elif isinstance(other, Residue):
            return self.chainid < other.chainid and self.resnr < other.resnr
        else: raise ValueError(other)

    def __contains__(self, other):
        if isinstance(other, Atom):
            return other in self._atoms
        else:
            return ValueError(other)

    def __del__(self):
        for atom in self.atoms:
            if atom._residue == self:
                atom._residue = None

    @property
    def atoms(self): return self._atoms

    def append(self, atom):
        if atom._residue != self:
            atom.residue = self

        self._atoms.append(atom)

    def remove(self, atom):
        assert isinstance(atom, Atom)
        if atom._residue != None:
            atom._residue = None

        if atom in self._atoms:
            self._atoms.remove(atom)

    def __copy__(self): return self.copy()
    def __deepcopy__(self, memo): return self.copy()
    def copy(self):
        clone = Residue(self.resnm, self.resnr, self.inscode, self.chainid)
        return clone
    """
    def __copy__(self):
        clone = Residue(self.resnm, self.resnr, self.inscode, self.chainid)
        return clone
    def __deepcopy__(self): return self.__copy__()

    def copy(self):
        clone = Residue(self.resnm, self.resnr, self.inscode, self.chainid)
        return clone
    """
    def __str__(self):
        return "Res(%-3s%2d %1.1s)" % (self.resnm, self.resnr, self.chainid)

    def __repr__(self):
        return "Res(%-3s%2d %1.1s)" % (self.resnm, self.resnr, self.chainid)

    def sort_atoms(self):
        self._atoms.sort()


ResidueNames = {
    "DA": "DA",
    "DA5": "DA",
    "DA3": "DA",
    "DAN": "DA",

    "DG": "DG",
    "DG5": "DG",
    "DG3": "DG",
    "DGN": "DG",

    "DC": "DC",
    "DC5": "DC",
    "DC3": "DC",
    "DCN": "DC",

    "DT": "DT",
    "DT5": "DT",
    "DT3": "DT",
    "DTN": "DT",

    "DU": "DU",
    "DU5": "DU",
    "DU3": "DU",
    "DUN": "DU",

    # Nucleobases
    "A": "A",
    "G": "G",
    "C": "C",
    "T": "T",

    "RU": "U",
    "RA": "A",
    "RG": "G",
    "RC": "C",
    "RT": "T",

    "RU5": "U",
    "RA5": "A",
    "RG5": "G",
    "RC5": "C",
    "RT5": "T",

    "RU3": "U",
    "RA3": "A",
    "RG3": "G",
    "RC3": "C",
    "RT3": "T",

    "RUN": "U",
    "RAN": "A",
    "RGN": "G",
    "RCN": "C",
    "RTN": "T",

    # Nucleobase Cap
    "MP": "MP",
    "DP": "DP",
    "TP": "TP",

    # Aminoacids
    "ALA": "ALA",
    "ARG": "ARG",
    "ASN": "ASN",
    "ASP": "ASP",
    "CYS": "CYS",
    "GLN": "GLN",
    "GLU": "GLU",
    "GLY": "GLY",
    "HIS": "HIS",
    "ILE": "ILE",
    "LEU": "LEU",
    "LYS": "LYS",
    "MET": "MET",
    "PHE": "PHE",
    "PRO": "PRO",
    "SER": "SER",
    "THR": "THR",
    "TRP": "TRP",
    "TYR": "TYR",
    "VAL": "VAL",
    "PYL": "PYL",
    "SEC": "SEC",

    # Aminoacid Terminals
    "ACE": "ACE",
    "NH2": "NH2",
    "NHE": "NH2",
    "NME": "NME",
    "URE": "URE",

    # Solvents
    "H2O": "WAT",
    "WAT": "WAT",
    "HOH": "WAT",
    "OHH": "WAT",
    "T3P": "WAT",
    "T4P": "WAT",
    "T5P": "WAT",
    "T3H": "WAT",
    "SOL": "SOL",

    # Ions
    "CL": "CL",
    "CL-": "CL",
    "NA": "NA",
    "NA+": "NA",
    "MG": "MG",
    "K": "K",
    "RB": "RB",
    "CS": "CS",
    "LI": "LI",
    "ZN": "ZN",
    "CU": "CU",
    # Unknown
    "UNK": "UNK"
    }

ResidueTypes = {
    "DA": "DNA",
    "DG": "DNA",
    "DC": "DNA",
    "DT": "DNA",
    "DU": "DNA",

    "A": "RNA",
    "G": "RNA",
    "C": "RNA",
    "T": "RNA",
    "U": "RNA",

    "MP": "RNA",
    "DP": "RNA",
    "TP": "RNA",

    "ALA": "PROTEIN",
    "ARG": "PROTEIN",
    "ASN": "PROTEIN",
    "ASP": "PROTEIN",
    "CYS": "PROTEIN",
    "GLN": "PROTEIN",
    "GLU": "PROTEIN",
    "GLY": "PROTEIN",
    "HIS": "PROTEIN",
    "ILE": "PROTEIN",
    "LEU": "PROTEIN",
    "LYS": "PROTEIN",
    "MET": "PROTEIN",
    "PHE": "PROTEIN",
    "PRO": "PROTEIN",
    "SER": "PROTEIN",
    "THR": "PROTEIN",
    "TRP": "PROTEIN",
    "TYR": "PROTEIN",
    "VAL": "PROTEIN",
    "PYL": "PROTEIN",
    "SEC": "PROTEIN",

    "ACE": "PROTEIN",
    "NH2": "PROTEIN",
    "NME": "PROTEIN",
    "URE": "PROTEIN",

    "WAT": "WATER",
    "SOL": "SOLVENT",

    "CL": "ION",
    "NA": "ION",
    "MG": "ION",
    "K": "ION",
    "RB": "ION",
    "CS": "ION",
    "LI": "ION",
    "ZN": "ION",

    "UNK": "OTHER",
    }
