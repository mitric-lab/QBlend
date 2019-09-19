
bl_info = {
    "name": "QBlend Addon",
    "author": "AG Mitric",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    "description": "In-filesystem Add-on Development Sandbox",
    "category": "Development",
}

if "bpy" in locals():
    import importlib
    if "panel" in locals():
        importlib.reload(panel)

from . import panel
import bpy

classes = ( panel.ToggleButtons,
            panel.OBJECT_OT_import_structure_button,
            panel.OBJECT_OT_import_cube_button,
            panel.OBJECT_OT_xyz_path,
            panel.OBJECT_OT_cube_path,
            panel.PANEL_PT_molecule_panel,
            panel.OBJECT_OT_automatic_ligthning_button,
            panel.OBJECT_OT_lookdev_button,
            panel.OBJECT_OT_rendered_button
          )
"""
from . import Blender
from . import materials, meshes, curves, collections
from .base import Object, Material, LazyMaterial, Empty

from .molecule import Molecule
from .marching_cube import triangulate
"""

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    #bpy.utils.register_module(__panel__)
    bpy.types.WindowManager.toggle_buttons = bpy.props.PointerProperty(type=panel.ToggleButtons)

def unregister():
    del bpy.types.WindowManager.toggle_buttons
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    #bpy.utils.unregister_module(__panel__)

if __name__ == "main":
    register()
