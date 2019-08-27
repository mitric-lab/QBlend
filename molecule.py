import numpy as np
import itertools
from . import atom as at

class graph:
    def __init__(self, dim):
        self.dim = dim
        self.adj = np.zeros((dim, dim))
        self.nodes = range(dim)

    def __getitem__(self, idx):
        return list(np.nonzero(self.adj[idx])[0])

    def setPower(self, n):
        self.pow = []
        for i in range(n):
            self.pow.append(self.getPower(i))

    def setPairs(self, n):
        self.pairs = []
        for i in range(n):
            self.pairs.append(self.getPairs(i))

    def setReachability(self, n):
        self.reachable = []
        mat = np.zeros((self.dim, self.dim))
        for i in range(n):
            mat = np.copy(mat) + self.pow[i]
            mat[mat > 1] = 1
            self.reachable.append(mat)

    def getIsReachable(self, i, j, n):
        return bool(self.reachable[n][i, j])

    def getPairs(self, n):
        mat = np.triu(self.pow[n]) - np.diag(np.diag(self.pow[n]))
        mat = mat - (1000 * self.reachable[n-1])
        mat[mat < 0] = 0
        return np.transpose(mat.nonzero())

    def getPower(self, n):
        if n ==0:
            return np.identity(self.dim)
        if n == 1:
            return self.adj
        else:
            mat = np.copy(self.adj)
            for i in range(1, n):
                mat = np.dot((self.adj), mat)
            return mat

class structure:
    def __init__(self,filename):
        self.filename = filename
        self.atomlist = []
        self.coord = []
        self.atomtypes = []

    def readXYZ(self):
        with open(self.filename, "r") as f:
            for line in f:
                tmp = line.split()
                if len(tmp) == 4:
                    self.atomlist.append(at.atom(tmp[0], at.coord(np.array(tmp[1:], dtype=float),
                                                            unit="angs")))
        self.natoms = len(self.atomlist)

    def getAdjacency(self):
        self.graph = graph(self.natoms)
        for pair in itertools.combinations(range(self.natoms), 2):
            if self.atomlist[pair[0]].bonding(self.atomlist[pair[1]]):
                self.graph.adj[pair[0], pair[1]] = 1
                self.graph.adj[pair[1], pair[0]] = 1
        self.graph.setPower(3)
        self.graph.setReachability(3)
        for idx, atom in enumerate(self.atomlist):
            syms = [at.symbol for at in np.array(self.atomlist)[self.graph[idx]]]
            atom.setConnectivity(len(self.graph[idx]), self.graph[idx], syms)
