#!/usr/bin/env python3
import bpy
import sys
import os
import math
import json
import traceback

# ✅ Debug logger
def debug(msg: str):
    print(f"[DEBUG] {msg}", flush=True)

# ✅ Ensure STL importer is loaded
def ensure_stl_addon():
    try:
        import io_mesh_stl
        debug("✅ io_mesh_stl loaded from addons_core")
    except ImportError:
        debug("⚠️ io_mesh_stl not found, trying to enable addon")
        bpy.ops.preferences.addon_enable(module="io_mesh_stl")

# ✅ Import model
def import_model(filepath: str):
    ext = os.path.splitext(filepath)[1].lower()
    debug(f"Detected extension: {ext}")
    if ext == ".stl":
        ensure_stl_addon()
        bpy.ops.import_mesh.stl(filepath=filepath)
    elif ext == ".obj":
        bpy.ops.import_scene.obj(filepath=filepath)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=filepath)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

# ✅ Compute metadata
def compute_metadata(obj):
    volume = 0.0
    if obj.type == 'MESH':
        mesh = obj.data
        mesh.calc_volume()
        volume = mesh.volume

    bbox = [abs(obj.dimensions.x), abs(obj.dimensions.y), abs(obj.dimensions.z)]
    return {
        "name": obj.name,
        "volume": volume,
        "bbox": bbox,
        "faces": len(obj.data.polygons) if obj.type == 'MESH' else 0,
        "vertices": len(obj.data.vertices) if obj.type == 'MESH' else 0
    }

# ✅ Safe render engine detection for Blender 4.5+
def set_render_engine(scene):
    available_engines = [
        getattr(e, "bl_idname", None)
        for e in bpy.types.RenderEngine.__subclasses__()
        if hasattr(e, "bl_idname")
    ]
    available_engines = [e for e in available_engines if e is not None]
    debug(f"Available render engines: {available_engines}")

    if "BLENDER_EEVEE" in available_engines:
        scene.render.engine = "BLENDER_EEVEE"
    elif "BLENDER_EEVEE_NEXT" in available_engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "CYCLES" in available_engines:
        scene.render.engine = "CYCLES"
    else:
        debug("⚠️ No known engine found, falling back to WORKBENCH")
        scene.render.engine = "BLENDER_WORKBENCH"

# ✅ Main pipeline
def main():
    try:
        model_path = sys.argv[-2]
        output_dir = sys.argv[-1]
        debug(f"Starting Blender pipeline...")
        debug(f"Model path: {model_path}")
        debug(f"Output dir: {output_dir}")

        bpy.ops.wm.read_factory_settings(use_empty=True)
        import_model(model_path)

        obj = bpy.context.selected_objects[0]
        debug(f"Imported object: {obj.name}")

        meta = compute_metadata(obj)
        debug(f"Volume: {meta['volume']}, BBox: {meta['bbox']}, Faces: {meta['faces']}, Vertices: {meta['vertices']}")

        scene = bpy.context.scene
        set_render_engine(scene)

        # ✅ Render thumbnail
        cam = bpy.data.cameras.new("RenderCam")
        cam_obj = bpy.data.objects.new("RenderCam", cam)
        bpy.context.collection.objects.link(cam_obj)

        bpy.context.scene.camera = cam_obj
        cam_obj.location = (obj.location.x + 2, obj.location.y + 2, obj.location.z + 2)
        cam_obj.rotation_euler = (math.radians(60), 0, math.radians(45))

        bpy.context.view_layer.update()

        thumb_path = os.path.join(output_dir, "thumbnail.png")
        bpy.context.scene.render.filepath = thumb_path
        bpy.context.scene.render.resolution_x = 512
        bpy.context.scene.render.resolution_y = 512
        bpy.ops.render.render(write_still=True)

        debug(f"✅ Rendered thumbnail to {thumb_path}")

        result = {
            "status": "ok",
            "metadata": meta,
            "thumbnail": thumb_path
        }
        print(json.dumps(result))
    except Exception as e:
        debug("Pipeline failed with exception:")
        debug(traceback.format_exc())
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
