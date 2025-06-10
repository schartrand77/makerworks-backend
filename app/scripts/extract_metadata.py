import bpy
import sys
import json
import os
import mathutils

def extract_metadata(filepath, output_json_path, preview_path):
    bpy.ops.import_mesh.stl(filepath=filepath) if filepath.endswith('.stl') else bpy.ops.import_scene.gltf(filepath=filepath)

    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    dimensions = obj.dimensions
    volume = obj.dimensions.x * obj.dimensions.y * obj.dimensions.z  # rough volume

    # Generate preview image
    bpy.ops.view3d.camera_to_view_selected()
    bpy.ops.render.render(write_still=True)
    bpy.data.images['Render Result'].save_render(filepath=preview_path)

    metadata = {
        "volume_mm3": volume,
        "dimensions_mm": {"x": dimensions.x, "y": dimensions.y, "z": dimensions.z},
        "face_count": len(obj.data.polygons),
    }

    with open(output_json_path, 'w') as f:
        json.dump(metadata, f)

# CLI entrypoint
if __name__ == "__main__":
    filepath = sys.argv[-3]
    json_out = sys.argv[-2]
    preview_out = sys.argv[-1]
    extract_metadata(filepath, json_out, preview_out)