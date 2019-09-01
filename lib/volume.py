import numpy as np
from .utils import iterable, SlotPickleMixin, is_integer

class Volume(object):
	__slots__ = ['_origin', '_shape', '_step',  'origin_type']
	def __init__(self, origin = None, shape = None, step = None):
		SlotPickleMixin.__init__(self)
		self._origin = np.zeros(3, dtype=float)
		self._shape = np.zeros(3, dtype=int)
		self._step = np.zeros(3, dtype=float)

		self.origin_type = 'CORNER'

		self.origin = origin
		self.shape = shape
		self.step = step

	def __len__(self):
		return self.shape[0]*self.shape[1]*self.shape[2]

	@property
	def origin(self): return self._origin
	@origin.setter
	def origin(self, value):
		if value is None:
			self._origin = np.zeros(3, dtype=float)
		elif isinstance(value, float):
			self._origin = np.full(3, value, dtype=float)
		elif iterable(value) and len(value) == 3:
			self._origin = np.array(value, dtype=float).reshape((3,))
		else:
			raise ValueError(value)

	@property
	def shape(self): return self._shape
	@shape.setter
	def shape(self, value):
		if value is None:
			self._shape = np.zeros(3, dtype=int)
		elif is_integer(value):
			self._shape = np.full(3, value, dtype=int)
		elif iterable(value) and len(value) == 3:
			self._shape = np.array(value, dtype=int).reshape((3,))
		else:
			raise ValueError(value)
		if hasattr(self, 'resize_data'):
			self.resize_data()

	@property
	def step(self): return self._step
	@step.setter
	def step(self, value):
		self._step = np.zeros(3, dtype=float)
		if value is None:
			self._step = np.zeros(3, dtype=float)
		elif isinstance(value, float):
			self._step = np.full(3, value, dtype=float)
		elif iterable(value):
			value = np.array(value, dtype=float)
			if value.shape == (3,3):
				self._step = np.diag(value)
			elif value.size == 3:
				value = value.flatten()
				for i in range(3): self._step[i] = value[i]
			else:
				raise ValueError(value)
		else:
			raise ValueError(value)

	def indices(self, start = 0, step = 1, stop = 0, x=0,y=1,z=2):
		for i in range(start, self.shape[x]-stop, step):
			for j in range(start, self.shape[y]-stop, step):
				for k in range(start, self.shape[z]-stop, step):
					yield (i,j,k)

	def value(self, *args):
		if len(args) == 3:
			ind = args
		elif len(args) == 1:
			ind = args[0]

		return self.origin + np.multiply(self.step, ind)

	def values(self, start = 0, step = 1, stop = 0, x=0,y=1,z=2):
		for i in range(start, self.shape[x]-stop, step):
			for j in range(start, self.shape[y]-stop, step):
				for k in range(start, self.shape[z]-stop, step):
					yield (i*self.step[x], j*self.step[y], k*self.step[z])

	def indices_values(self, start = 0, step = 1, stop = 0, x=0,y=1,z=2):
		for i in range(start, self.shape[x]-stop, step):
			for j in range(start, self.shape[y]-stop, step):
				for k in range(start, self.shape[z]-stop, step):
					yield (i,j,k), (i*self.step[x], j*self.step[y], k*self.step[z])

	@property
	def axes(self):
		return np.multiply(self.step, self.shape[:, None])

	@property
	def max(self):
		return self.origin + np.multiply(self.step, self.shape)




	@property
	def min_bound(self):
		return self.origin

	@property
	def max_bound(self):
		v = self.origin + np.multiply(self.step, self.shape)
		return v

	@property
	def grid(self):
		ox, oy, oz = self.min_bound
		sx, sy, sz = self.max_bound
		nx, ny, nz = self.shape
		return np.mgrid[ox:sx:nx*1.0j,oy:sy:ny*1.0j,oz:sz:nz*1.0j]

	def __repr__(self):
		return "<Volume(%d,%d,%d)>" % tuple(self.shape)

class VolumeData(Volume):
	__slots__ = ['_data']
	def __init__(self, origin = None, shape = None, step = None):
		self._data = None
		super(VolumeData, self).__init__(origin, shape, step)

	@property
	def data(self): return self._data

	@data.setter
	def data(self, value):
		assert((value.shape == self.shape).all())
		self._data = value

	def clear(self):
		self._data.fill(0.0)

	def resize_data(self):
		self._data = np.zeros(self.shape, dtype=float)

	def __getitem__(self, ind): return self._data[ind]
	def __setitem__(self, ind, value): self._data[ind] = value
	def __iter__(self): return iter(self._data)
	def __len__(self): return self._data.size

	def eval(self, func, use_grid = True, clear_data = True):
		if clear_data:
			self._data.fill(0.0)

		if use_grid:
			grid = self.grid
			self._data += func(grid[0], grid[1], grid[2])
			assert self._data.shape == grid[0].shape
		else:
			for i,j,k in self.points():
				x,y,z = self.value(i,j,k)
				self._data[i,j,k] = func(x,y,z)

	def copy(self):
		c = VolumeData()
		c._origin = self._origin.copy()
		c._shape = self._shape.copy()
		c._step = self._step.copy()
		c._data = self._data.copy()
		return c

class VolumeFunction(Volume):
	__slots__ = ['_func']
	def __init__(self, func, origin = None, shape = None, step = None):
		self._func = func
		super(VolumeData, self).__init__(origin, shape, step)


	@property
	def func(self): return self._func

	@func.setter
	def func(self, value): self._func = value

	def __iter__(self):
		for ind in self.points():
			yield self[ind]

	def __getitem__(self, ind):
		i,j,k = ind
		x,y,z = self.value(i,j,k)
		return self.func(x,y,z)

def BoundaryVolumeData(p0, p1, resolution = 4, rel_scale = False):
	"""
	if is_integer(shape):
		shape = np.full(3, shape, dtype=int)
	elif iterable(shape) and len(shape) == 3:
		shape = np.array(shape, dtype=int).reshape((3,))
	else:
		raise ValueError(shape)

	p0 = np.minimum(p0,p1)
	p1 = np.maximum(p0,p1)
	vec = p1-p0
	if rel_scale:
		imin, imax = np.argmin(vec), np.argmax(vec)
		imid = [i for i in range(3) if i not in(imin,imax)][0]
		rel = vec[imin]/vec[imax]

		shape[imin] = int((rel)*shape[imid])
		shape[imax] = int((2-rel)*shape[imid])
		#print shape
	"""
	p0 = np.minimum(p0,p1)
	p1 = np.maximum(p0,p1)
	vec = p1-p0
	shape = (np.absolute(vec)*resolution).astype(int)
	#shape = [int(abs(v)*resolution) for v in vec]
	step = np.divide(vec, shape)
	return VolumeData(p0, shape, step)


def getIsoFromVolume(data, npnt, thrs = 0.999, mindens = None, maxdens = None, density=True):
	if mindens is None: mindens = round(np.min(data),8)
	if maxdens is None: maxdens = round(np.max(data),8)

	hist, edges = np.histogram(data, npnt, range=(mindens, maxdens), density=density)
	hist = hist/np.sum(hist)

	amax0 = amax = ramax = lamax = np.argmax(hist)

	maxval = hist[amax]
	lvals, rvals = [maxval], [maxval]

	#for h, e in zip(hist, edges):
	#	print("%15.9f %.3f" % (e, h*100.))

	#print(amax, maxval, edges[amax])

	while sum(lvals) < thrs and sum(rvals) < thrs:
		ramax = min(ramax+1, len(hist)-1)
		lamax = max(lamax-1, 0)

		if lamax != 0:
			lvals.append(hist[lamax])
		if ramax != len(hist)-1:
			rvals.append(hist[ramax])
		print((lamax, sum(lvals), edges[lamax]), (ramax, sum(rvals), edges[ramax]))

		if(ramax == len(hist)-1 and lamax == 0):
			break

	if (sum(lvals) >= thrs and sum(rvals) >= thrs) or (sum(lvals) < thrs and sum(rvals) < thrs):
		if abs(sum(lvals)-thrs) < abs(sum(rvals)-thrs):
			amax,vals = lamax, lvals
		else:
			amax,vals = ramax, rvals
	elif sum(lvals) >= thrs: amax, vals = lamax, lvals
	elif sum(rvals) >= thrs: amax, vals = ramax, rvals


	if amax == 0: amax = amax+1
	elif amax+1 == len(hist): amax = amax-1

	x0,y0 = sum(vals),edges[amax]
	x1, y1 = sum(vals[:-1]), edges[amax+1] if amax < amax0 else edges[amax-1]

	#print(y0,'+(',thrs,'-', x0, ')*(', y1,'-',y0,')/(',x1,'-',x0,')')
	val = y0 + (thrs-x0)*(y1-y0)/(x1-x0)

	#print(amax, sum(vals), edges[amax], val)
	return val
