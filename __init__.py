bl_info = {
    "name": "Molecule Addon",
    "author": "Joscha Hoche",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    "description": "In-filesystem Add-on Development Sandbox",
    "category": "Development",
}


# To support reload properly, try to access a package var,
# if it's there, reload everything
if "bpy" in locals():
    import importlib
    if "panel" in locals():
        importlib.reload(panel)

from . import panel
import bpy

classes = ( panel.ToggleButtons,
            panel.OBJECT_OT_import_structure_button,
            panel.OBJECT_OT_xyz_path,
            panel.PANEL_PT_molecule_panel,
          )

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
