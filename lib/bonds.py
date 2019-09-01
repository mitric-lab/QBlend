from .utils import is_numeric, iterable, get_file_ext, is_integer, \
    find_unique_cycles, normalized, ordered_cycle, SlotPickleMixin

class Bonds(SlotPickleMixin):
    __slots__ = ['__conn', '__nmax', '__size']

    @staticmethod
    def traverseSub(conn, i):
        if is_integer(i):
            if i not in conn:
                raise StopIteration
            for j in conn[i]:
                if i < j: yield (i, j)
        if iterable(i):
            for ii in i:
                if ii in conn:
                    for j in conn[ii]:
                        if ii < j and j in i:
                            yield (ii, j)

    @staticmethod
    def traverse(conn):
        for i, c in conn.items():
            for j in c:
                if i < j: yield (i,j)

    def __init__(self, conn = None, nconn = None, nmax = None):
        SlotPickleMixin.__init__(self)
        self.__conn = dict()
        if isinstance(conn, dict):
            self.__conn = {x: set(y) for x, y in conn.items()}
        if isinstance(conn, list):
            self.__conn = {x: set(y) for x, y in enumerate(conn)}
        self.__nmax = nmax if nmax else (max(self.__conn.keys()) if len(self.__conn) else 0)
        self.__size = nconn if conn and nconn else sum([len(c) for c in self.__conn])/2

    def __len__(self):
        return int(self.__size)
    def __iter__(self):
       return Bonds.traverse(self.__conn)

    def __getitem__(self,i):
        if isinstance(i, slice):
            start, stop, step = i.indices(self.__nmax)
            return Bonds.traverseSub(self.__conn, range(start, stop, step))
        else:
            return Bonds.traverseSub(self.__conn, i)

    def __contains__(self, ind):
        assert isinstance(ind, tuple) and len(ind)==2
        return ind[0] in self.__conn and ind[1] in self.__conn[ind[0]]

    def connectivity_of(self, i):
        return self.__conn[i]

    def clear(self):
        self.__conn = {}

    def append(self, i, j = None):
        if isinstance(i, tuple) and j == None:
            return self.append(*i)
        elif iterable(i):
            for ii in i:
                self.append(ii, j)
            return
        elif iterable(j):
            for jj in j:
                self.append(i, jj)
            return
        else:
            nadd = 0
            if i not in self.__conn: self.__conn[i] = set()
            if j not in self.__conn: self.__conn[j] = set()

            #nadd += len(self.__conn[i]) + len(self.__conn[j])
            self.__conn[i].add(j)
            self.__conn[j].add(i)
            #nadd -= len(self.__conn[i]) + len(self.__conn[j])
            self.__size += 1
            self.__nmax = max(max(i,j),self.__nmax)

    @property
    def connectivity(self): return self.__conn

    @property
    def graph(self, nat = None):
        if not nat: nat = self.__nmax
        graph = [set() for _ in range(nat)]
        for x, y in self:
            graph[x].update([y])
            graph[y].update([x])
        return graph

    @property
    def angles(self):
        ang = []

        for j in range(len(self)):
            conn = self.connectivity_of(j)
            for it, i in enumerate(conn):
                for k in conn[it+1:]:
                    ang.append((i,j,k))

        return ang

    @property
    def dihedrals(self):
        dih = []
        for ib, ic in self:
            for ia in self.connectivity_of(ib):
                if ia != ic:
                    for id in self.connectivity_of(ib):
                        if ib != id and ia != id:
                            dih.append((ia,ib,ic,id))
        return dih

    @property
    def bidihedrals(self):
        angles = self.angles

        dih = []
        for ib, ic, id in angles:
            for ia in self.connectivity_of(ib):
                if ia != ic and ia != id:
                    for ie in self.connectivity_of(id):
                        if ie != ic and ie != ib and ie != ia:
                            dih.append((ia, ib, ic, id, ie))
        return dih

    @property
    def rings(self):
        graph = self.bonds.graph
        cycles = find_unique_cycles(graph)
        cycles = [tuple(ordered_cycle(x, graph)) for x in cycles]

        return cycles

    def __str__(self):
        lines = []
        for ind in self:
            lines.append(ind)
        return str(lines)

    def replace_indices(self, newind):
        newconn = {}
        for i, conn in self.connectivity.items():
            ni = newind[i] if i in newind else i
            newconn[ni] = set()

            for j in conn:
                nj = newind[j] if j in newind else j
                newconn[ni].add(nj)

        self.__conn =   newconn
