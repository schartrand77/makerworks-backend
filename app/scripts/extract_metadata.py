import bpy
import sys
import json
import os
import math
import mathutils


def ensure_single_mesh_object():
    """
    Ensures there's exactly one mesh object in the scene.
    Returns the mesh object or raises an error.
    """
    objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not objects:
        raise RuntimeError("No mesh objects found in the scene.")
    return objects[0]


def calculate_mesh_volume(obj):
    """
    Calculates the approximate volume of a mesh object.
    Assumes scale is applied.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()

    volume = 0.0
    for face in mesh.polygons:
        volume += face.area * face.center.dot(face.normal)
    volume = abs(volume / 3.0)

    obj_eval.to_mesh_clear()
    return volume


def setup_camera(obj, dimensions):
    """
    Adds a camera if one doesn't exist and orients it to view the model.
    """
    if not bpy.data.cameras:
        cam_data = bpy.data.cameras.new("AutoCam")
        cam_obj = bpy.data.objects.new("AutoCam", cam_data)
        bpy.context.collection.objects.link(cam_obj)
        bpy.context.scene.camera = cam_obj
    else:
        cam_obj = bpy.data.objects.get("AutoCam") or bpy.data.objects.get("Camera")
        if not cam_obj:
            cam_data = bpy.data.cameras.new("FallbackCam")
            cam_obj = bpy.data.objects.new("FallbackCam", cam_data)
            bpy.context.collection.objects.link(cam_obj)
            bpy.context.scene.camera = cam_obj

    cam_obj.location = (
        dimensions.x * 1.8,
        dimensions.y * 1.8,
        dimensions.z * 1.2,
    )
    cam_obj.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam_obj


def extract_metadata(filepath, output_json_path, preview_path):
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Import model
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.stl':
        bpy.ops.import_mesh.stl(filepath=filepath)
    elif ext in ['.gltf', '.glb']:
        bpy.ops.import_scene.gltf(filepath=filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    obj = ensure_single_mesh_object()

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    bpy.ops.object.transform_apply(scale=True)

    dimensions = obj.dimensions
    volume_mm3 = calculate_mesh_volume(obj)

    setup_camera(obj, dimensions)

    # Render preview
    bpy.context.scene.render.filepath = preview_path
    bpy.context.scene.render.resolution_x = 512
    bpy.context.scene.render.resolution_y = 512
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)

    metadata = {
        "volume_mm3": round(volume_mm3, 2),
        "dimensions_mm": {
            "x": round(dimensions.x, 2),
            "y": round(dimensions.y, 2),
            "z": round(dimensions.z, 2)
        },
        "face_count": len(obj.data.polygons),
    }

    with open(output_json_path, 'w') as f:
        json.dump(metadata, f, indent=2)


# ---------- CLI Entry Point ----------

if __name__ == "__main__":
    try:
        filepath = sys.argv[-3]
        json_out = sys.argv[-2]
        preview_out = sys.argv[-1]

        extract_metadata(filepath, json_out, preview_out)
    except Exception as e:
        error = {"error": str(e)}
        print(json.dumps(error))
        sys.exit(1)