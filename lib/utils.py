import numpy as np
import time, os


DEBUG = bool(os.environ.get('PYLIB_DEBUG', ''))
DEBUG = True
def iterable(x):
    if isinstance(x, str): return False
    if hasattr(x, "__iter__"): return True
    try:
        _ = (e for e in x)
        return True
    except TypeError:
        return False

def is_numeric(x, recurse = 0):
    if recurse and iterable(x):
        for i in x:
            if not is_numeric(i, recurse-1): return False
        return True
    else:
        return isinstance(x, (int, float, complex, np.float64))

def is_integer(x, recurse = 0):
    if recurse and iterable(x):
        for i in x:
            if not is_integer(i, recurse-1): return False
        return True
    else:
        return isinstance(x, (int, np.int16, np.int32, np.int64))

def is_float(x, recurse = 0):
    if recurse and iterable(x):
        for i in x:
            if not is_float(i, recurse-1): return False
        return True
    else:
        return isinstance(x, (float, np.float16, np.float32, np.float64))

def is_string(x, recurse = 0):
    if recurse and iterable(x):
        for i in x:
            if not is_string(i, recurse-1): return False
        return True
    else:
        return isinstance(x, str)

def is_file(x):
	import io
	try:
		if isinstance(x, io.IOBase): return True
		elif isinstance(x, file): return True
		return False
	except:
		return False

def get_filemode(x):
	import io
	try:
		if isinstance(x, io.IOBase):
			return ("r" if x.readable() else "") + ("w" if x.writable() else "")
		elif isinstance(x, file):
			return ('r' if 'r' in x.mode else '') + ('w' if 'w' in x.mode else '')
		else:
			raise ValueError(f)
	except:
		raise
		#return "Unknown file object", f

def to_float(x, default = None):
    try:
        return float(x)
    except ValueError:
        if default == None: raise
        else: return default

def to_int(x, default = None):
    try:
        return int(x)
    except ValueError:
        if default == None: raise
        else: return default

def flatten(l):
    if not iterable(l):
        return l
    ll = []
    for x in l:
        if iterable(x):
            ll += flatten(x)
        else:
            ll.append(x)
    return ll

def get_file_ext(x):
    assert isinstance(x, str)
    ind = x.rfind(".")
    return "" if ind == -1 else x[ind+1:]

def unit_conversion(x, factor):
    if iterable(x):
        return [unit_conversion(v, factor) for v in x]
    elif isinstance(x, str):
        return unit_conversion(float(x), factor)
    else:
        assert isinstance(x, (float, int))
        return float(x)*factor
from_angstrom = lambda x: unit_conversion(x, 1.88972613)
to_angstrom = lambda x: unit_conversion(x, 0.529177208)

to_electronvolt = lambda x: unit_conversion(x, 27.211385)
from_electronvolt = lambda x: unit_conversion(x, 1./27.211385)

def normalized(x):
    x = np.array(x)
    return x/np.linalg.norm(x)

def depth_first(graph, start, goal, pathrange=(2, 7)):
    """Depth-first search to find all paths leading from start to goal"""
    stack = [(start, [start])]
    while stack:
        (vertex, path) = stack.pop()
        # any successes after this point will add one to current length of path
        if len(path) + 1 < pathrange[1]:
            for nextvert in graph[vertex] - set(path):
                if nextvert == goal:
                    if pathrange[0] <= len(path) + 1 < pathrange[1]:
                        yield path + [nextvert]
                else:
                    stack.append((nextvert, path + [nextvert]))

def find_specific_cycles(graph, vertex, pathrange=(2, 7)):
    """Finds all unique paths of a vertex back to itself"""
    cycles = []
    fixedcycles = []
    for goal in graph[vertex]:
        for path in depth_first(graph, vertex, goal, pathrange=pathrange):
            if set(path) not in cycles:
                cycles.append(set(path))
                fixedcycles.append(path)
    return cycles, fixedcycles

def find_unique_cycles(graph, pathrange=(2, 7)):
    """Finds all closed walks of with lengths bounded by path range. Defaults to paths
    of length > 2 and < 7"""
    cycles = []
    for i in range(len(graph)):
        possible_cycles, _extras = find_specific_cycles(graph, i, pathrange)
        for cycle in possible_cycles:
            if set(cycle) not in cycles and pathrange[0] < len(cycle) < pathrange[1]:
                cycles.append(set(cycle))
    return cycles

def ordered_cycle(cycle, graph):
    """Returns ordered cycle corresponding to input cycle (i.e., undoes set() build)"""
    pathrange = (len(cycle), len(cycle) + 1)
    _extras, fixedcycles = find_specific_cycles(graph, list(cycle)[0], pathrange)
    for fc in fixedcycles:
        if set(fc) == cycle:
            return fc

class Timer(object):
    def __init__(self):
        self.start = 0.
        self.value = 0.
        self.total = 0.
        self.average = 0.
        self.min, self.max = float("inf"), float("-inf")
        self.nruns = 0
        self.stopped = True

    def tick(self):
        self.value = time.time()
        self.stopped = False

    def tock(self):
        self.value = time.time() - self.value
        self.min = min(self.min, self.value)
        self.max = max(self.max, self.value)
        self.total += self.value
        self.average = self.total / float(self.nruns+1)
        self.nruns += 1
        self.stopped = True
        return self.value

    def reset(self):
        self.start = 0.
        self.value = 0.
        self.total = 0.
        self.average = 0.
        self.min, self.max = float("inf"), float("-inf")
        self.nruns = 0
        self.stopped = True

    def __str__(self):
        if not self.stopped: self.tock()
        return "%12.8f %12.8f (%d)" % (self.total, self.average, self.nruns)

class TimerCollection(object):
    def __init__(self):
        self.init_time = time.time()
        self.timers = {}

    def append(self, name):
        self.timers[name] = Timer()

    def __getitem__(self, name):
        if name not in self.timers:
            self.append(name)
        return self.timers[name]

    def tick(self, name):
        return self[name].tick()

    def tock(self, name):
        return self[name].tock()

    def reset(self, name):
        return self[name].reset()

    def total(self):
        return time.time()-self.init_time



    def __str__(self):
        lines = []
        for k, v in self.timers.items():
            lines.append("%-20s %s" % (k,v))
        return "\n".join(lines)

class SlotPickleMixin(object):
    """Top-class that allows mixing of classes with and without slots.
    Takes care that instances can still be pickled with the lowest
    protocol. Moreover, provides a generic `__dir__` method that
    lists all slots.

    SOURCE: https://github.com/limix/pickle-mixin/blob/master/pickle_mixin/_core.py
    """

    # We want to allow weak references to the objects
    __slots__ = ['__weakref__']

    def _get_all_slots(self):
        """Returns all slots as set"""
        all_slots = (getattr(cls, '__slots__', [])
                         for cls in self.__class__.__mro__)
        return set(slot for slots in all_slots for slot in slots)

    def __getstate__(self):
        if hasattr(self, '__dict__'):
            # We don't require that all sub-classes also define slots,
            # so they may provide a dictionary
            statedict = self.__dict__.copy()
        else:
            statedict = {}
        # Get all slots of potential parent classes
        for slot in self._get_all_slots():
            try:
                value = getattr(self, slot)
                statedict[slot] = value
            except AttributeError:
                pass
        # Pop slots that cannot or should not be pickled
        statedict.pop('__dict__', None)
        statedict.pop('__weakref__', None)
        return statedict

    def __setstate__(self, state):
        for key, value in state.items():
            setattr(self, key, value)

    def __dir__(self):
        result = dir(self.__class__)
        result.extend(self._get_all_slots())
        if hasattr(self, '__dict__'):
            result.extend(self.__dict__.keys())
        return result
