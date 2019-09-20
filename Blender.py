import bpy

_data_switch = {
		#'LAMP': bpy.data.lights,
		'MESH': bpy.data.meshes,
		'CAMERA': bpy.data.cameras,
		'CURVE': bpy.data.curves,
		'OBJECT': bpy.data.objects,
		'MATERIALS': bpy.data.materials,
		'FONT': bpy.data.fonts,
		#'SURFACE': bpy.data.surfaces
		}




resolution = 1
auto_animate = False
scene = bpy.context.scene
data = bpy.data
#objects = bpy.context.scene.objects
objects = bpy.context.collection.objects
materials = bpy.data.materials
window_manager = bpy.context.window_manager
context = bpy.context
active_object = bpy.context.active_object


def getFrame():
	return scene.frame_current

def setFrame(val):
	assert isinstance(val, int)
	scene.frame_set(val)

def nextFrame(off = 1):
	setFrame(getFrame() + off)

def prevFrame(off):
	setFrame(getFrame() - off)

def select_all(value = False):
	for obj in objects:
		obj.select = value

def clear_all(do_unlink=False):
	for bpy_data_iter in _data_switch.values():
		for id_data in bpy_data_iter:
			bpy_data_iter.remove(id_data, do_unlink=do_unlink)


def clear_data(data=None, do_unlink=False):
	if data == None:
		clear_all()
	elif isinstance(data, str):
		clear_data(_data_switch[data], do_unlink)
	else:
		for id_data in data:
			print("Remove", id_data, "from", data)
			data.remove(id_data, do_unlink=do_unlink)


def clear_objects(pattern = None, exclude_type = None):
	if not exclude_type:
		exclude_type = ('LAMP', 'CAMERA', 'MATERIALS')
	if pattern:
		import re
		prog = re.compile(pattern)

	for obj in scene.objects:
		if obj.type not in exclude_type:
			if not pattern or prog.match(obj.name):
				print("Remove ", obj.type, obj)
				#scene.objects.unlink(obj)
				if obj.data != None:
					_data_switch[obj.type].remove(obj.data, do_unlink=True)
				elif obj != None:
					try:
						scene.objects.unlink(obj)
					except: pass
				#del obj
				#bpy.data.objects.remove(obj.data, do_unlink=True)
				#bpy.data.objects.remove(obj.data)


	"""
	for k, v in _data_switch.items():
		if k not in exclude_type:
			clear_data(v, True)
	"""

def clear_materials(do_unlink=False):
	for mat in materials:
		try:
			bpy.data.materials.remove(mat, do_unlink=do_unlink)
		except:
			print("Can not clear material:", mat.name)
			pass

def save_blend(save_path):
	f = open(save_path, 'w')
	f.close()
	bpy.ops.wm.save_as_mainfile(filepath=save_path)


def render_image(save_path, resolution=None):
	scene.render.filepath = save_path
	if resolution is not None:
		x,y = resolution
		scene.render.resolution_x, scene.render.resolution_y = x, y
	bpy.ops.render.render( write_still=True )


def get_max_threads():
	""" Returns the number of available threads on a posix/win based system """
	import os, sys
	if sys.platform == 'win32':
		return (int)(os.environ['NUMBER_OF_PROCESSORS'])
	else:
		return (int)(os.popen('grep -c cores /proc/cpuinfo').read())


__lib_config = {
	'resolution': 1,
	'auto_animate': True,
	'auto_shade_smooth': True,
	'nthreads': 1,

	}


def get_lib_config(name = None):
	global __lib_config
	if name is None or not name: return __lib_config
	elif name not in __lib_config: return None
	else: return __lib_config[name]

def set_lib_config(name, value):
	global __lib_config
	__lib_config[name] = value

def set_nthreads(n):
	global __nthreads
	maxthreads = get_max_threads()
	if n > maxthreads:
		print("WARNING: setting %d threads exceeds number of available %d cores" % (n, maxthreads))

	set_lib_config('nthreads', int(n))

def get_nthreads():
	global __nthreads
	n = get_lib_config('nthreads')
	return n if n > 0 else get_max_threads()

def set_auto_shade_smooth(n):
	global __auto_shade_smooth
	set_lib_config('auto_shade_smooth', bool(n))

def auto_shade_smooth(value = None):
	if value is None: return bool(get_lib_config('auto_shade_smooth'))
	else: set_lib_config('auto_shade_smooth', bool(value))

def auto_animate(value = None):
	if value is None: return bool(get_lib_config('auto_animate'))
	else: set_lib_config('auto_animate', bool(value))

def nthreads(value = None):
	if value is None: return int(get_lib_config('nthreads'))
	else: set_nthreads(value)

def BlenderInit(frame=1, **kw):
	setFrame(frame)
	clear_objects()
	clear_materials()
	for k,v in kw.items():
		set_lib_config(k, v)

def recurLayerCollection(layerColl, collName):
	found = None
	if (layerColl.name == collName):
		return layerColl
	for layer in layerColl.children:
		found = recurLayerCollection(layer, collName)
		if found:
			return found


"""
@staticmethod
def getObjects():
	return Blender.scene.objects
objects = property(getObjects)

@staticmethod
def getData():
	return bpy.data
data = property(getData)

@staticmethod
def getMaterials(self):
	return bpy.data.materials
materials = property(getMaterials)
"""
