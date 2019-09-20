import bpy
from .base import DummyObject, Material, LazyMaterial
from .collections import ObjectCollection, MaterialCollection
from . import meshes, curves
from . import Blender
from .marching_cube import triangulate, triangulate_par
from .materials import getColor, make_lazy_material, make_glas_material
import numpy as np
import sys,os
sys.path.append(os.getcwd())

from lib import AttrDict, Filter, utils as pyutils, VolumeData
import lib.molecule as pymol
from lib.utils import TimerCollection as Timer
from lib.volume import BoundaryVolumeData


atom_radii_period = {1: 0.4, 2: 0.7, 3: 1.0, 4: 1.3, 5: 1.7}

def make_atom_material(name):#, color=(0., 0., 1., 1), shader="Glossy", roughness=0.0):
	mat = bpy.data.materials.new(name) # create new material
	mat.use_nodes = True # use nodes
	return mat

"""
def make_atom_material(name, **kw):
	print("KWWW", kw)
	mat = {
		'diffuse_color': (.2, .5, .2)
		}
	for k, v in mat.items():
		kw[k] = v if k not in kw else kw[k]
	return make_lazy_material(name, **kw)
"""

def make_lobe_material(name, **kw):
	mat = bpy.data.materials.new(name) # create new material
	mat.use_nodes = True # use nodes
	return mat


Materials = {
	None:   make_atom_material('DefaultMaterial'),
	'Atom': make_atom_material('AtomMaterial'),
	'Path': make_glas_material('PathMaterial'),
	'Lobe': make_lobe_material('Lobe'),
	'Bond': make_lazy_material('Bond'),
	'Ring': make_lazy_material('Ring', alpha=0.5),
	}

Colors = {
	None:	   getColor('grey'),
	'Element': {None: getColor('grey'),
				1: getColor('lightgrey'),
				6: getColor('darkgrey'),
				7: getColor('blue'),
				8: getColor('red'),
				13: getColor('tan'),
				15: getColor('tan'),
				17: getColor('lightgreen'),
				47: getColor('silver'),
				79: getColor('gold'),
			   },
	'Residue': {'ALA': getColor('grey'),
			   },
	'Path': getColor('red'),
	'Ring': { 3: getColor('orange'),
			  4: getColor('red'),
			  5: getColor('blue'),
			  6: getColor('lightgreen'),
		},
	'IsoSign': { +1: getColor('red'), -1: getColor('blue') },
	}

default_options = AttrDict({
	'colors': Colors,
	'materials': Materials,

	'carbon_color': getColor('darkgrey'),

	'shader': "Diffuse",
	'roughness': 0.5,

	'atom_scale': 1.,
	'stick_size': 0.2,
	'line_size':  0.05,

	'stick_resolution': 2,
	'ball_resolution': 6,

	'atom_size':	 'period',
	'atom_style':	'Nurbs',
	'atom_color':	'Element',
	'atom_material': 'Atom',

	'bond_twocolor': True,
	'bond_style': 'Nurbs',
	''

	'auto_bonds': False,
	'bond_tolerance': 1.2,
	'align_com': False,

	'path_material': 'Path',
	'path_color': 'Path',
	'path_size': 0.8,
	'path_resolution': 16,

	'surface_material': 'Lobe',
	'surface_color': getColor('red'),

	'ring_material': 'Ring',
	'ring_color': 'Ring',
	'ring_edge_bevel': 0.02,

	'triangulation_method': 'cube',
	'volume_material': 'Lobe',
	'volume_color': 'IsoSign',
	'volume_resolution': 4,
	})

def make_options(options, **kw):
	kw = AttrDict(kw)
	options = AttrDict(options.copy())
	rest = AttrDict()
	for opt, optval in kw.items():
		if opt in options:
			options[opt] = optval
		else:
			rest[opt] = optval

	return options, rest


def make_default_options(**kw):
	return make_options(default_options, **kw)




def get_option(name, **kw):
	return kw[name] if name in kw else (default_options[name] if name in default_options else None)

def make_atom_object(radius, style, resolution):
	if style == None or style.lower() == 'dummy' or radius == 0 or radius == None:
		obj = DummyObject()
	elif style.lower() == 'uvsphere':
		obj = meshes.UVsphere(size = radius, subdivisions = resolution**3/2)
		obj.addAutoKey('location')
	elif style.lower() == 'icosphere':
		obj = meshes.Icosphere(size = radius, subdivisions = resolution)
	elif style.lower() == 'nurbs':
		obj = curves.NurbsSurface(type = 'SPHERE', radius = radius)
	elif style.lower() == 'metaball':
		obj = meshes.Metaball(type = 'BALL', size = radius)
	else:
		raise ValueError(style)

	obj.addAutoKey('location')
	return obj


def make_bond(iobj, jobj, size, style, twocolor, resolution):
	if style == None or size == 0 or size == None or style.lower() == 'dummy':
		obj = DummyBond(iobj, jobj)
	elif twocolor:
		obj = TwoColorBond(style, size, resolution, iobj, jobj)
	elif style.lower() == 'nurbs':
		obj = NurbsBond(size, resolution, iobj, jobj)
	else:
		raise ValueError(style)
	return obj


class TwoColorBond(ObjectCollection):
	__slots__ = ['_atom1', '_atom2', '_style']
	__overwrites__ = ['name', 'location','atom1','atom2']
	def __init__(self, style, size, resolution, atom1, atom2, material = None):
		super().__init__("BOND")

		self._atom1 = atom1
		self._atom2 = atom2

		self._style = style.lower()

		if style.lower() == 'nurbs':
			c1 = curves.NurbsLine("BOND-1", self.atom1.location, self.location)
			c2 = curves.NurbsLine("BOND-2", self.atom2.location, self.location)
			c2.data.bevel_depth = c1.data.bevel_depth = size
			c2.data.bevel_resolution = c1.data.bevel_resolution = resolution
			c2.data.fill_mode = c1.data.fill_mode = 'FULL'
			c1.addAutoKey('data.splines.points.co', 'hide_viewport', 'hide_render')
			c2.addAutoKey('data.splines.points.co', 'hide_viewport', 'hide_render')
		else:
			raise ValueError(style)

		if not material:
			c1.material = self.atom1.material
			c2.material = self.atom2.material
		else:
			c1.material = self._material.copy()
			#c2.material.diffuse_color = self.atom1.diffuse_color
			c1.material = self._material.copy()
			#c2.material.diffuse_color = self.atom2.diffuse_color

		self.append(c1)
		self.append(c2)


	@property
	def atom1(self): return self._atom1
	@atom1.setter
	def atom1(self, value): self._atom1 = value

	@property
	def atom2(self): return self._atom2
	@atom2.setter
	def atom2(self, value): self._atom2 = value

	@property
	def location(self):
		return (self.atom1.location + self.atom2.location)/2.

	@property
	def vector(self):
		return (self.atom1.location - self.atom2.location)

	@property
	def length(self):
		return self.vector.length

	@location.setter
	def location(self, _):
		raise RuntimeError("Can not set location of nurbs")


	@property
	def name(self): return self.getobjattr('name')

	@name.setter
	def name(self, value):
		self.setobjattr('name', value)

		for i,o in enumerate(self):
			o.setobjattr('name', "%s-%d" % (value, i+1))
			o.name = "%s-%d" % (value, i+1)


	def update(self):

		if self._style == 'nurbs':
			self[0].update([self.atom1.location, self.location])
			self[1].update([self.atom2.location, self.location])
		else:
			raise ValueError(self._style)

		return self

class NurbsBond(curves.Curve):
	__slots__ = ['_atom1', '_atom2', '_style']
	__overwrites__ = ['name', 'location','atom1','atom2']
	def __init__(self, size, resolution, atom1, atom2, material = None):
		super().__init__(curves.NurbsLine("BOND", atom1.location, atom2.location))

		self.data.bevel_depth = size
		self.data.bevel_resolution = resolution
		self.data.fill_mode = 'FULL'
		self.addAutoKey('data.splines.points.co', 'hide_viewport', 'hide_render')

		if material:
			self.material = material
		else:
			self.material = Materials['Bond']

		self._atom1 = atom1
		self._atom2 = atom2



	@property
	def atom1(self): return self._atom1
	@atom1.setter
	def atom1(self, value): self._atom1 = value

	@property
	def atom2(self): return self._atom2
	@atom2.setter
	def atom2(self, value): self._atom2 = value

	@property
	def location(self):
		return (self.atom1.location + self.atom2.location)/2.

	@property
	def vector(self):
		return (self.atom1.location - self.atom2.location)

	@property
	def length(self):
		return self.vector.length

	def update(self):
		super().update([self.atom1.location, self.atom2.location])
		return self

class DummyBond(DummyObject):
	__slots__ = ['_atom1', '_atom2']
	__overwrites__ = ['atom1','atom2']
	def __init__(self, atom1, atom2):
		super().__init__()
		self._atom1 = atom1
		self._atom2 = atom2



	@property
	def atom1(self): return self._atom1
	@atom1.setter
	def atom1(self, value): self._atom1 = value

	@property
	def atom2(self): return self._atom2
	@atom2.setter
	def atom2(self, value): self._atom2 = value

	@property
	def location(self):
		return (self.atom1.location + self.atom2.location)/2.

	@property
	def vector(self):
		return (self.atom1.location - self.atom2.location)

	@property
	def length(self):
		return self.vector.length

	def update(self):
		super().update([self.atom1.location, self.atom2.location])
		return self

class ReprBase(ObjectCollection):
	__slots__ = ['options', 'filter', '_materials', 'timer','_matoptions']
	kind = None
	order_id = 0
	def __init__(self, name, *args, **kw):
		super().__init__(name)
		self.options, kw = make_default_options(**kw)
		self.filter = None if 'filter' not in kw else kw['filter']
		self._materials = {}
		self._matoptions = kw['matoptions'] if 'matoptions' in kw else {}
		self.timer = Timer()

	def __lt__(self, other):
		if other == None: return False
		else:
			return self.order_id < other.order_id

	def __gt__(self, other):
		if other == None: return False
		else:
			return self.order_id > other.order_id

	def __contains__(self, item):
		if self.filter == None: return True
		elif isinstance(self.filter, bool): return self.filter
		elif callable(self.filter):
			return self.filter(*item)
		else:
			print("Invalid filter", self.filter)
			return False

	def option(self, name):
		return get_option(name, **self.options)


	def color(self, col_type, *args):
		colors = self.options.colors
		if callable(col_type):
			col = col_type(*args)
			col_id = "-".join(args)
			col_id, col
		elif isinstance(col_type, str) and col_type in colors:
			colors = colors[col_type]
			col_id = col_type
			for arg in args:
				if isinstance(colors, (str,tuple)):
					break
				if isinstance(colors, dict) and arg in colors:
					if arg == 6:
						colors = self.options.carbon_color
					else:
						colors = colors[arg]
					col_id += '-'+ str(arg)
				elif None in colors:
					colors = colors[None]
				else:
					colors = self.options.colors[None]
					break
			if isinstance(colors, tuple) or len(colors) == 4:
				col = colors
			elif isinstance(colors, str):
				col = getColor(col_type)
			return col_id, col
		elif isinstance(col_type, tuple):
			col = col_type
		else:
			col = getColor(col_type)

		return col_type, col

	def material(self, mat_type, *args):
		materials = self.options.materials
		print("MATTYPE", mat_type)
		print("MATERIALSS", materials)
		if callable(mat_type):
			mat = mat_type(*args)
		elif isinstance(mat_type, str) and mat_type in materials:
			materials = materials[mat_type]
			for arg in args:
				if isinstance(materials, (Material, LazyMaterial)):
					break
				elif isinstance(materials, (dict, list, tuple)) and arg in materials:
					materials = materials[arg]
				else:
					materials = self.options.materials[None]
					break

			if isinstance(materials, (Material, LazyMaterial)):
				mat = materials
			elif isinstance(materials, str) or callable(materials):
				mat = bpy.data.materials[name]
			else:
				return materials
				#raise ValueError(mat_type)
		elif isinstance(mat_type, (Material, LazyMaterial)):
			mat = mat_type
		else:
			raise ValueError(mat_type)

		return mat

	def make_material(self, mat, col, *args):
		mat = self.material(mat, *args)
		col_id, col = self.color(col, *args)
		if len(args) == 1 and type(args[0]) == int and type(col) == dict:
			iso = args[0]
			col = col[iso]
		name = mat.name + "-"+ str(col_id)
		shader = self.options.shader
		roughness = self.options.roughness
		if name not in self._materials:
			mat = mat.copy()
			mat.node_tree.nodes.remove(mat.node_tree.nodes[1])
			shader = mat.node_tree.nodes.new(type="ShaderNodeBsdf"+shader) # create new node
			shader.inputs['Roughness'].default_value = roughness
			print("INPUT", mat.node_tree.nodes.get("Material Output").inputs)
			mat_input = mat.node_tree.nodes.get("Material Output").inputs[0]
			mat.node_tree.links.new(shader.outputs["BSDF"], mat_input)
			mat.name = name
			if col != None:
				print("COLOR", mat)#, mat.diffuse_color)
				mat.diffuse_color = [col[0], col[1], col[2], 1.] #col
				mat.node_tree.nodes[1].inputs[0].default_value = [col[0], col[1], col[2], 1.]

			for k, w in self._matoptions:
				mat['k'] = w
			self._materials[name] = mat
		else:
			mat = self._materials[name]

		return mat

	def create(self, *args, **kw):
		return self

	def update(self, *args, **kw):
		return self


class MoleculeRepr(ReprBase):
	__slots__ = ['atom_objects', 'bond_objects', 'ref_atom']
	kind = 'MOL'

	def __init__(self, name, *args, **kw):
		super().__init__(name, *args, **kw)

		self.ref_atom = {}
		self.atom_objects = {}
		self.bond_objects = {}

	def key(self, molecule, atom):
		key = self.options.atom_color.lower()
		if key == 'element':
			return atom.number
		if key == 'symbol':
			return atom.symbol
		elif key == 'name':
			return atom.name
		elif key == 'resnm':
			return atom.residue.resnm if atom.residue != None else 'UNK'
		else:
			return atom.index

	def atom_size(self, molecule, atom):
		if isinstance(self, StickRepr):
			return self.options.stick_size
		else:
			type = self.options.atom_size
			if isinstance(type, (float, int)):
				res = float(type)
			elif isinstance(type, str):
				type = type.lower()
				if type == 'period':
					res = atom_radii_period[atom.period]
				elif type == 'atomic_radius':
					res = atom.atomic_radius
				elif type == 'vdw_radius':
					res = atom.vdw_radius
			else:
				res = 1.
			return max(res * self.options.atom_scale, self.options.stick_size)

	def bond_size(self, molecule, iatom, jatom):
		if isinstance(self, LineRepr):
			return self.options.line_size
		else:
			return self.options.stick_size


	def create(self, molecule, *args, **kw):
		print("  Generate Atoms")
		atom_mat = self.options.atom_material
		atom_col = self.options.atom_color

		self.timer.reset('atoms')
		wm = Blender.window_manager
		wm.progress_begin(0, len(molecule))

		for i, (atom, coords) in enumerate(molecule):
			if (molecule, atom) in self:
				self.timer.tick('atoms')
				key = self.key(molecule, atom)
				atom_size = self.atom_size(molecule, atom)
				name = 'Atom-%04d' % i

				if key not in self.ref_atom:
					obj = make_atom_object(1, self.options.atom_style, self.options.ball_resolution)
					obj.name = name
					obj.scale = atom_size
					obj.material = self.make_material(atom_mat, atom_col, key)
					print(obj.name)
					self.ref_atom[key] = obj
				else:
					obj = self.ref_atom[key].copy()
					obj.name = name
					obj.scale = atom_size

				obj.location = coords
				self.append(obj)
				self.atom_objects[i] = obj
				self.timer.tock('atoms')
			wm.progress_update(i)

		wm.progress_end()

		print("  Generate Bonds")
		self.timer.reset('bonds')
		nbonds = len(molecule.bonds)
		wm.progress_begin(0, nbonds)
		bonds = [b for b in molecule.bonds \
				 if (molecule, molecule.atoms[b[0]]) in self \
				 or (molecule, molecule.atoms[b[1]]) in self]
		nbonds = len(bonds)
		for n, (i,j) in enumerate(bonds):


			iatom, jatom = molecule.atoms[i], molecule.atoms[j]
			irep = (molecule, iatom) in self
			jrep = (molecule, jatom) in self

			if irep or jrep:
				self.timer.tick('bonds')
				self.create_bond(molecule, i,j, irep, jrep)
				self.timer.tock('bonds')

			if  (n % int(0.1*nbonds)) == 0:
				print("	%3.0f%% %4d/%d bonds processed (t = %.3f)" \
					  % (n/float(nbonds)*100, n, nbonds, self.timer['bonds'].total))

			wm.progress_update(n)
		wm.progress_end()


		print("  Added %d atoms and %d bonds" \
			  % (len(self.atom_objects), len(self.bond_objects)))

		print(self.timer)
		return super().create(molecule, *args, **kw)


	def create_bond(self, molecule, i, j, irep, jrep):
		if not irep and not jrep: return None
		elif irep and jrep:
			ir = jr = self
		else:
			ir = jr = self
			if not irep:
				ir = molecule.find_atom_repr(molecule.atoms[i])
				if not ir or ir > self: return None
			elif not jrep:
				jr = molecule.find_atom_repr(molecule.atoms[j])
				if not jr or jr > self: return None

		iobj = ir.atom_objects[i]
		jobj = jr.atom_objects[j]

		bond_style = self.options.bond_style
		bond_reso = 0 if isinstance(self, LineRepr) else self.options.stick_resolution
		twocolor = self.options.bond_twocolor
		size = self.bond_size(molecule, i, j)
		name = 'Bond-%04d-%04d' % (i,j)
		#print(i,j,bond_style, twocolor, bond_reso)

		obj = make_bond(iobj, jobj, size, bond_style, twocolor, bond_reso)
		obj.name = name
		obj.hide = True
		#obj.notify('hide_viewport', 'hide_render', frame=0)
		obj.hide = False

		self.bond_objects[(i,j)] = obj
		self.append(obj)
		return obj


	def update(self, molecule, *args, **kw):
		print("  Update positions of %d atoms and %d bonds" \
			  % (len(self.atom_objects), len(self.bond_objects)))
		for i, obj in self.atom_objects.items():
			obj.location = molecule.coords[i]

		if molecule.options.auto_bonds:
			bonds = list(molecule.bonds)
			hidebonds, unhidebonds,addbonds = 0, 0, 0
			for i,j in bonds:
				if (i,j) not in self.bond_objects:
					iatom, jatom = molecule.atoms[i], molecule.atoms[j]
					irep = (molecule, iatom) in self
					jrep = (molecule, jatom) in self
					obj = self.create_bond(molecule, i, j, irep, jrep)
					addbonds += 1

			for (i,j), obj in self.bond_objects.items():
				if (i,j) not in bonds and not obj.hide:
					obj.hide = True
					hidebonds += 1
				elif (i,j) in bonds and obj.hide:
					obj.hide = False
					unhidebonds += 1
				if not obj.hide:
					obj.update()

			print("  Created %d bonds, %d bonds hidden and %d bonds unhidden" \
			  % (addbonds, hidebonds, unhidebonds))
		else:
			for (i,j), obj in self.bond_objects.items():
				obj.update()
		return super().update(molecule, *args, **kw)



class StickAndBallRepr(MoleculeRepr):
	order_id = 0
	def __init__(self, name = 'StickAndBall', *args, **kw):
		super().__init__(name, *args, **kw)

class StickRepr(MoleculeRepr):
	order_id = 1

	def __init__(self, name = 'Stick', *args, **kw):
		super().__init__(name, *args, **kw)

class LineRepr(MoleculeRepr):
	order_id = 2

	def __init__(self, name = 'Line', *args, **kw):
		super().__init__(name, *args, **kw)
		self.options.atom_style = None

class VdwRepr(MoleculeRepr):
	order_id = 2

	def __init__(self, name = 'Vdw', *args, **kw):
		super().__init__(name, *args, **kw)
		if 'atom_size' not in kw:
			self.options.atom_size = 'vdw_radius'
		if 'atom_scale' not in kw:
			self.options.atom_scale = self.options.atom_scale * 0.6
		if 'atom_style' not in kw:
			self.options.atom_style = 'metaball'
		self.options.bond_style = None



class WireframeRepr(MoleculeRepr):
	order_id = 2

	def __init__(self, name = 'Wireframe', *args, **kw):
		super().__init__(name, *args, **kw)
		self.options.bond_style = None
		self.options.atom_style = None

	def create(self, molecule, *args, **kw):
		if len(molecule.bonds) == 0:
			print("No bonds available for wireframe representation")
			return self

		context = bpy.context
		verts = [x for i, x in enumerate(molecule.coords) if (molecule, i) in self]
		edges = [(i,j) for i,j in molecule.bonds  if (molecule, i) in self and (molecule, j) in self]

		mesh = bpy.data.meshes.new(self.name)
		mesh.from_pydata(verts, edges, [])
		mesh.update()

		obj = bpy.data.objects.new(self.name, mesh)
		bpy.context.scene.objects.link(obj)

		Blender.select_all(False)

		obj.select = True

		bpy.context.scene.objects.active = obj
		bpy.ops.object.convert(target='CURVE')
		obj = context.object
		obj.data.fill_mode = 'FULL'
		obj.data.render_resolution_u = self.options.stick_size
		obj.data.bevel_depth = self.options.line_size
		obj.data.bevel_resolution = self.options.stick_size
		bpy.ops.object.shade_smooth()

		self.append(obj)
		return super().update(molecule, *args, **kw)

	def update(self, *args, **kw):
		return super().update(*args, **kw)


class RingsRepr(ReprBase):
	order_id = 2

	def __init__(self, name = 'Rings', *args, **kw):
		super().__init__(name, *args, **kw)
		self._rings = {}

	def key(self, molecule, ring):
		key = self.options.ring_color
		if key == 'Ring':
			return len(ring)

	def create_ring(self, molecule, ring):
		ring_mat = self.options.ring_material
		ring_col = self.options.ring_color
		edge_bevel = self.options.ring_edge_bevel
		ring = tuple(ring)

		key = self.key(molecule, ring)
		verts = [molecule.coords[i] for i in ring]
		edges = [[i, (i + 1) % len(ring)] for i,_ in enumerate(ring)]
		mat = self.make_material(ring_mat, ring_col, key)

		obj = meshes.Mesh("Ring")
		obj.create(verts, edges, [range(len(ring))])
		obj.material = mat
		obj.addAutoKey('data.vertices.co')#, 'hide_viewport', 'hide_render')

		self.append(obj)
		self._rings[tuple(ring)] = obj
		return obj

	def create(self, molecule, *args, **kw):
		rings = molecule.rings()

		for i,ring in enumerate(rings):
			if ring in self:
				name = "%s%d-%02d" % (self.name, len(ring), i)
				obj = self.create_ring(molecule, ring)
				obj.name = name


		return super().create(molecule, *args, **kw)

	def update(self, molecule, **kw):
		newrings = molecule.rings()
		oldrings = self._rings.keys()

		for i,ring in enumerate(newrings):
			ring = tuple(ring)
			if ring not in oldrings and ring in self:
				name = "%s%d-%02d" % (self.name, len(ring), i)
				obj = self.create_ring(molecule, ring)
				obj.name = name
				obj.hide = True
				obj.notify(frame = 0)
				obj.hide = False
				obj.notify()

		for i,ring in enumerate(oldrings):
			obj = self._rings[ring]
			if ring not in newrings and not obj.hide:
				obj.hide = True
			elif ring in newrings and obj.hide:
				obj.hide = False

			verts = [molecule.coords[i] for i in ring]
			for x,v in zip(verts, obj.data.vertices):
				v.co = x
			obj.notify('data.vertices.co')

		return super().create(molecule, *args, **kw)




class PathRepr(ReprBase):
	__slots__ = ['_paths']
	kind = 'PATH'
	def __init__(self, name = 'Path', *args, **kw):
		super().__init__(name, *args, **kw)
		self._paths = []

	def vertices(self, molecule, path):
		if callable(path):
			return path(molecule)
		elif hasattr(path, "__iter__"):
			return path
		else:
			return None

	def append(self, path):
		self._paths.append(path)
		return self

	def create(self, molecule, *args, **kw):
		size = self.options.path_size
		reso = self.options.path_resolution
		mat = self.make_material(self.options.path_material, self.options.path_color)

		for p in self._paths:
			verts = self.vertices(molecule, p)
			if verts != None and hasattr(verts, "__iter__"):
				obj = curves.NurbsPath(self.name, verts)

				obj.data.bevel_depth = size
				obj.data.bevel_resolution = reso
				obj.data.fill_mode = 'FULL'
				obj.material = mat

				super().append(obj)

		return super().create(molecule, *args, **kw)

	def update(self, molecule, *args, **kw):
		off = 0
		for i, p in enumerate(self._paths):
			verts = self.vertices(molecule, p)
			if verts and hasattr(verts, "__iter__"):
				self[i-off].update(verts)
			else:
				off += 1
		return super().update(molecule, *args, **kw)




class Isosurface(ReprBase):
	__slots__ = ['_isovals', 'on_update','draw_box', '_lastvol']
	kind = 'VOLUME'
	def __init__(self, name, isovals, *args, **kw):
		super().__init__(name, *args, **kw)
		self.on_update = kw['on_update'] if 'on_update' in kw else 'hide'
		self.draw_box = 'draw_box' in kw and bool(kw['draw_box'])
		if isinstance(isovals, float):
			isovals = [isovals]
		self._isovals = isovals
		self._lastvol = None

	def set_iso(self,isovals):
		if isinstance(isovals, float):
			isovals = [isovals]
		self._isovals = isovals

	def key(self, molecule, iso):
		if self.options.volume_color == 'IsoSign':
			return int(iso/abs(iso))
		else:
			return None

	def create_box(self, mol, V):
		context = bpy.context
		ox, oy, oz = V.origin
		mx, my, mz = V.max
		verts = [[ ox, oy, oz ], # 0 0
				 [ mx, oy, oz ], # 1 x
				 [ ox, my, oz ], # 2 y
				 [ ox, oy, mz ], # 3 z
				 [ mx, my, oz ], # 4 xy
				 [ ox, my, mz ], # 5 yz
				 [ mx, oy, mz ], # 6 xz
				 [ mx, my, mz ]] # 7 xyz

		edges = [[0,1], [0,2], [0,3],
				 [1,4], [1,6],
				 [2,4], [2,5],
				 [3,5], [3,6],
				 [4,7], [5,7],[6,7]
				 ]

		mesh = bpy.data.meshes.new(self.name +"-Box")
		mesh.from_pydata(verts, edges, [])
		mesh.update()
		obj = bpy.data.objects.new(self.name, mesh)
		bpy.context.scene.objects.link(obj)
		bpy.ops.object.shade_smooth()

		self.append(obj)

	def create_volume(self, mol, V):
		import time
		nthreads = Blender.get_nthreads()
		print("  Triangulate surface of %d points using %d threads" % (len(V), nthreads))

		#t = time.time()
		#triList = triangulate(V, self._isovals, Blender.window_manager)
		#print("Serial = %lf, %d" % (time.time()-t, len(triList[0])))

		#t = time.time()
		#triList = triangulate_par(nthreads, V, self._isovals, Blender.window_manager)
		#print("Parallel = %lf, %d" % (time.time()-t, len(triList[0])))


		if nthreads == 1:
			triList = triangulate(V, self._isovals, Blender.window_manager)
		else:
			triList = triangulate_par(nthreads, V, self._isovals, Blender.window_manager)

		self._lastvol = [len(self)]
		for iso, triangles in zip(self._isovals, triList):
			print("  Render surface of %d triangles with iso-value %f" % (len(triangles), iso))
			if len(triangles) == 0: continue
			key = self.key(mol, iso)
			name = "%s-%s" % (self.name, str(key))


			mat = self.make_material(self.options.volume_material, self.options.volume_color, key)

			obj = meshes.Isosurface(self.name, triangles)
			obj.material = mat
			super().append(obj)
		if self.draw_box:
			self.create_box(molecule, V)

		self._lastvol.append(len(self))

	def create(self, molecule, *args, **kw):
		V = self.get_volume(molecule, **kw)
		if V is not None:
			self.create_volume(molecule, V)

		return super().create(molecule, *args, **kw)

	def update(self, molecule, *args, **kw):
		if self._lastvol:
			for i in range(self._lastvol[0], self._lastvol[1]):
				if self.on_update == 'hide':
					print("  Hide volume %d" % i)
					self[i].hide = True
				elif self.on_update == 'remove':
					print("  Remove volume %d" % i)
					self[i].remove()

		V = self.get_volume(molecule, **kw)
		if V is not None:
			self.create_volume(molecule, V)

		return super().update(molecule, *args, **kw)

class VolumeIsosurfaceRepr(Isosurface):
	__slots__ = ['_volume']

	def __init__(self, name, V, isovals, *args, **kw):
		super().__init__(name, isovals, *args, **kw)
		self._volume = V

	def get_volume(self, molecule, **kw):

		if isinstance(self._volume, str):
			return molecule.volumes[self._volume] if self._volume in molecule.volumes else None
		elif isinstance(self._volume, VolumeData):
			return self._volume
		else:
			raise ValueError(self._volume)


class OrbitalIsosurfaceRepr(Isosurface):
	__slots__ = ['_orbital', '_boundary']

	def __init__(self, orb, isoval, boundary = None, *args, **kw):
		name = "%s-%03d" % ("Orbital", int(orb))
		absiso = abs(float(isoval))
		super().__init__(name, [absiso, -absiso], *args, **kw)

		self._orbital = int(orb)
		self._boundary = boundary

	def get_volume(self, molecule, **kw):
		assert molecule.basis is not None
		assert molecule.modata is not None

		basis = molecule.basis
		modata = molecule.modata

		bmin, bmax = basis.boundary_box(min([abs(x) for x in self._isovals]) * 0.1) \
						if self._boundary is None else self._boundary
		res = self.options.volume_resolution
		V = BoundaryVolumeData(bmin, bmax, res)

		print ("  Compute orbital %03d on %2dx%2dx%2d grid" % (self._orbital, V.npnt[0], V.npnt[1], V.npnt[2]))
		orbital = molecule.orbital(self._orbital)
		V.eval(orbital)
		return V



class ReprSelect(object):
	__reprs = {
		'path': PathRepr,
		'wireframe': WireframeRepr,
		'stickandball': StickAndBallRepr,
		'stick': StickRepr,
		'cpk': StickAndBallRepr,
		'lines': LineRepr,
		'vdw': VdwRepr,
		'rings': RingsRepr,
		'orbital': OrbitalIsosurfaceRepr,
		'isosurface': VolumeIsosurfaceRepr
		}
	def __init__(self, parent, which = None, **kw):
		self.parent = parent
		self.options, self.repr_options = make_options(parent.options, **kw)

		self.which = which.lower() if isinstance(which, str) else which

	def __call__(self, *args, **kw):
		if self.which in ReprSelect.__reprs:
			options = self.parent.options

			overwrite = make_options(self.options, **kw)
			options.update(overwrite[0])
			options.update(self.repr_options)
			options.update(overwrite[1])

			r = ReprSelect.__reprs[self.which](*args, **options)
			self.parent.add_repr(r)
			return r
		else:
			raise AttributeError('Unknown representation:' + str(self.which))

	def __getattr__(self, name):
		if name in ReprSelect.__reprs__:
			return ReprSelect(self.parent, name)
		else:
			raise AttributeError(name)


class Molecule(pymol.Molecule):
	__slots__ = ['repr', 'options', 'collection']

	def __init__(self, name = 'Molecule', *args, **kw):
		super().__init__(*args, **kw)
		self.options,_ = make_default_options(**kw)
		self.repr = ObjectCollection(name)
		self.collection = Blender.data.collections.new(name)
		Blender.scene.collection.children.link(self.collection)
		layer_collection = Blender.context.view_layer.layer_collection
		layerColl = Blender.recurLayerCollection(layer_collection, self.collection.name)
		Blender.context.view_layer.active_layer_collection = layerColl

	def new_repr(self, **kw):
		return ReprSelect(self, None, **kw)


	def add_repr(self, representation = None, *args, **kw):
		print("ADDREPR")
		if isinstance(representation, str):
			print("ADDR1")
			return ReprSelect(self, representation)(*args, **kw)
		elif isinstance(representation, ReprBase):
			print("ADDR2", representation.atom_objects)#, self.repr.created == True)
			self.repr.append(representation)
			print("ADDR2.1")
			return representation
		else:
			print("ADDR3")
			return ReprSelect(self, None, **kw)

	def find_atom_repr(self, iatom):

		for r in sorted(self.repr, key=lambda x: x.order_id):
			if r.kind == 'MOL' and (self, iatom) in r:
				return r
		return None

	def create(self, *args, **kw):
		print("CREATE")
		if len(self.atoms) and self.options.auto_bonds:
			print("Compute Bonds (tol=%f)" % self.options.bond_tolerance)
			self.generate_bonds(self.options.bond_tolerance)
		if len(self.atoms) and self.options.align_com:
			print("Align COM")
			self.translate(-self.com)

		for r in sorted(self.repr, key=lambda x: x.order_id):
			print("Create Representation:", r.name)
			if len(r) == 0:
				r.create(self, *args, **kw)



	def update(self, *args, **kw):
		if len(self.atoms) and self.options.auto_bonds:
			print("Compute Bonds (tol=%f)" % self.options.bond_tolerance)
			self.generate_bonds()

		if len(self.atoms) and self.options.align_com:
			print("Align COM")
			self.translate(-self.com)

		if Blender.auto_animate():
			Blender.nextFrame()

		for r in self.repr:

			print("Update Representation:", r.name)
			r.update(self, *args, **kw)
