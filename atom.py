import numpy as np

bohrToAngs = 0.529

stickradius = 0.25

atomcolors = {"H":(0.7, 0.7, 0.7, 1),
              "B":(0., 0.9, 0., 1),
              "C":(0.2, 0.2, 0.2, 1),
              "N":(0., 0., 1., 1),
              "O":(1., 0., 0., 1),
              "Si":(238.0/256, 180.0/256, 34.0/256, 1),
              "S":(228.0/255.0, 202.0/255.0, 66.0/255.0, 1),
              "Zn":(0.4, 0.4, 0.4, 1)}

rcov = {"C": 0.77, "H": 0.37, "O":0.73, "N":0.71, "S":0.75}

vdw_radius = {"H": 3.,
              "B": 3.,
              "C": 3.,
              "N": 3.,
              "O": 3.,
              "Si":3.,
              "S": 3.,
              "Zn":3. }

class coord(object):
    def __init__(self, x, unit="ang"):
        x = np.array(x)
        if unit == "au":
            self.x = x
        if unit == "angs":
            self.x = x / bohrToAngs
        if unit == "pm":
            self.x = x / bohrToAngs / 100
        if unit == "nm":
            self.x = x / bohrToAngs * 10

    @property
    def au(self):
        return self.x

    @property
    def ang(self):
        return self.x * bohrToAngs

    @property
    def pm(self):
        return self.x * bohrToAngs * 100.

    @property
    def nm(self):
        return self.x * bohrToAngs * 0.1

    def __sub__(self, other):
        return coord(self.x - other.x, unit="au")


class atom(object):
    atomic_number = {"H": 1, "C": 6, "N": 7, "O": 8, "S":16}

    def __init__(self, s, c, charge=0):
        self.symbol = s
        self.xyz = c
        self.charge = charge
        self.isaromatic = False
        self.label = None
        self.group = None

    @property
    def isAromatic(self):
        self.isaromatic = True

    def getRcov(self):
        return coord(rcov[self.symbol], unit="angs").au

    @property
    def color(self):
        return self.atomcolor[self.symbol]

    def getDistance(self, other):
        d = self.xyz.au - other.xyz.au
        return np.sqrt(np.dot(d, d))

    def setConnectivity(self, conn, neighb, sym):
        self.conn = conn
        self.neighbors = neighb
        self.neigh_sym = sym

    def bonding(self, other):
        bondtreshold = 0.25
        dist = self.getDistance(other)
        sum_rcov = self.getRcov() + other.getRcov()
        if abs(dist - sum_rcov) <= bondtreshold * sum_rcov:
            return True
        else:
            return False

    @property
    def number(self):
        return self.atomic_number[self.symbol]

    def __lt__(self, other):
         return self.number < other.number

    def __str__(self):
        return self.symbol
