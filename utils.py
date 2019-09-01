import bpy

def set_blender_object_property(obj, path, value):

    if value == None: return
    elif hasattr(obj, "__iter__"):
        res = True
        for item in obj: 
            res = res and set_blender_object_property(item, path, value)
        return res
    else:
        i = path.find('.')
        if i == -1: 
            if hasattr(obj, path):
                setattr(obj, path, value)
                return True
            else:
                print("WARNING:", obj, 'has no property ', path)
                return False
        else: 
            return set_blender_object_property(getattr(obj, path[:i]), path[i+1:], value)
def get_blender_object_property(obj, path):
    if hasattr(obj, "__iter__"):
        return [get_blender_object_property(item, path) for item in obj]
    else:
        i = path.find('.')
        if i == -1: 
            if hasattr(obj, path):
                return getattr(obj, path)
            else:
                print("WARNING:", obj, 'has no property ', path)
                return None
        else: 
            return get_blender_object_property(getattr(obj, path[:i]), path[i+1:])
        
def has_blender_object_property(obj, path):
    if hasattr(obj, "__iter__"):
        return [get_blender_object_property(item, path) for item in obj]
    else:
        i = path.find('.')
        if i == -1: 
            return hasattr(obj, path)
        else: 
            return has_blender_object_property(getattr(obj, path[:i]), path[i+1:])
        

def insert_blender_keyframe(obj, data_path, index=-1, frame=bpy.context.scene.frame_current, group=""):
    if isinstance(data_path, list):
        for p in data_path: insert_blender_keyframe(obj, p, index, frame, group)
    elif hasattr(obj, "__iter__"):
        for item in obj: insert_blender_keyframe(item, data_path, index, frame, group)
    else:
        i = data_path.find('.')
        if i == -1:
            obj.keyframe_insert(data_path, frame = frame)
        else: 
            insert_blender_keyframe(getattr(obj, data_path[:i]), data_path[i+1:], index, frame, group)