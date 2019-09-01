import copy

from . import elements



from .utils import SlotPickleMixin, is_integer

class Atom(SlotPickleMixin):
    __slots__ = '_element', '_name', '_mass', '_residue', \
                 '_index', '_formal_charge', '_partial_charge', \
                 'pdbrec', '_data'
    def __init__(self, index = None, init = None, name = None, *args, **kw):
        SlotPickleMixin.__init__(self)
        #print(index, init)
        self._index = int(index)
        self._element = 0
        self._name = None
        self._mass = None
        self._residue = None
        self._formal_charge = 0
        self._partial_charge = 0.0
        self.pdbrec = "ATOM"
        self._data = {}

        if name != None:
            self._name = name

        if init != None:
            self.element = init

    def __getattr__(self, name):
        if name in elements.Element.__slots__:
            return getattr(elements.by_index(self._element), name)
        elif name.lower() in self._data:
            return self._data[name]
        else: raise AttributeError(name)

    def __del__(self):
        if self._residue != None:
            self.residue.remove(self)

    def __eq__(self, other):
        return other != None \
            and self.index == other.index \
            and self.element == other.element

    def __lt__(self, other):
        if is_integer(other):
            return self.index < other
        elif isinstance(other, Atom):
            return self.index < other.index
        else: raise ValueError(other)

    @property
    def index(self): return self._index

    @index.setter
    def index(self, i): self._index = int(i)

    @property
    def formal_charge(self): return self._formal_charge

    @formal_charge.setter
    def formal_charge(self, i): self._formal_charge = int(i)

    @property
    def partial_charge(self): return self._partial_charge

    @partial_charge.setter
    def partial_charge(self, i): self._partial_charge = float(i)


    @property
    def element(self): return elements.by_index(self._element)

    @element.setter
    def element(self, init):
        if isinstance(init, Atom):
            self._element = init._element
        if isinstance(init, elements.Element):
            self.number = init.number
        elif is_integer(init):
            self.number = init
        elif isinstance(init, str):
            self.symbol = init
        else: raise ValueError(init)

    @property
    def symbol(self): return elements.symbol(self._element)
    @symbol.setter
    def symbol(self, symbol):
        self._element = elements.index_by_symbol(symbol)
        assert self._element > 0

    @property
    def name(self):
        return self.symbol if not self._name else self._name
    @name.setter
    def name(self, name):
        if self._element < 1:
            self._element = elements.index_by_name(name)
        self._name = name
        assert self._element > 0

    @property
    def number(self): return elements.number(self._element)
    @number.setter
    def number(self, number):
        self._element = elements.index_by_number(number)
        assert self._element > 0

    @property
    def mass(self):
        return self._mass if self._mass != None else self.atomic_mass

    @mass.setter
    def mass(self, mass): self._mass = mass

    @property
    def resnm(self):
        return self._residue.resnm if self._residue != None else "UNK"

    @property
    def resnr(self):
        return self._residue.resnr if self._residue != None else 0

    @property
    def chainid(self):
        return self._residue.chainid if self._residue != None else ' '

    @property
    def inscode(self):
        return self._residue.inscode if self._residue != None else ' '

    @property
    def altloc(self): return ' '

    @property
    def tempfactor(self): return 1.0

    @property
    def occup(self): return 0.0

    @property
    def residue(self):
        return self._residue


    @residue.setter
    def residue(self, res):
        if self.residue == res: return

        if self._residue != None:
            self._residue.remove(self)

        self._residue = res
        if res is not None:
            #assert isinstance(res, residue.Residue)
            res.append(self)


    def __copy__(self):
        return self.copy()
    def __deepcopy__(self, memo):
        return self.copy()


    def copy(self):
        clone = Atom(self.index)
        clone._element = self._element
        clone._name = copy.copy(self._name)
        clone._mass = self._mass
        clone._formal_charge = self._formal_charge
        clone._partial_charge = self._partial_charge
        clone._residue = None
        clone.pdbrec = self.pdbrec
        clone._data = copy.deepcopy(self._data)
        return clone

    def __str__(self):
        if self.residue == None:
            return "%4d Atom(%2d %-4s)" % (self.index, self.number, self.name)
        else:
            return "%4d Atom(%2d %-4s) %s" \
                % (self.index, self.number, self.name, \
                   str(self.residue))

    def __repr__(self):
        return "<Atom(%d, %s)>" % (self.index, self.symbol)
