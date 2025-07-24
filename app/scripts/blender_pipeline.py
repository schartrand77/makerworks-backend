"""
Run with Blender:
blender --background --python blender_pipeline.py -- <model_path> <output_dir>
"""

import bpy
import sys
import json
import pathlib

def main(model_path: str, output_dir: str):
    model_path = pathlib.Path(model_path).resolve()
    output_dir = pathlib.Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # clear scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # import model
    ext = model_path.suffix.lower()
    if ext == ".stl":
        bpy.ops.import_mesh.stl(filepath=str(model_path))
    elif ext == ".3mf":
        # Blender's default distribution lacks a native 3MF importer.  When
        # a 3MF import add-on is installed it typically exposes an X3D style
        # operator.  Use that operator so the pipeline can handle .3mf files
        # if the add-on is available.
        bpy.ops.import_scene.x3d(filepath=str(model_path))
    else:
        print(json.dumps({"error": "Unsupported format"}))
        sys.exit(1)

    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj

    # center and scale
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.location = (0, 0, 0)
    bpy.ops.transform.resize(value=(1, 1, 1))

    mesh = obj.data
    volume = obj.dimensions.x * obj.dimensions.y * obj.dimensions.z
    bbox = [round(c, 3) for c in obj.dimensions]
    faces = len(mesh.polygons)
    vertices = len(mesh.vertices)

    # set camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    cam_obj.location = (0, -3, 1.5)
    cam_obj.rotation_euler = (1.2, 0, 0)

    # light
    light_data = bpy.data.lights.new(name="Light", type='SUN')
    light_obj = bpy.data.objects.new(name="Light", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = (5, -5, 5)

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.fps = 24

    # thumbnail
    thumb_path = output_dir / f"{model_path.stem}_thumb.png"
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(thumb_path)
    bpy.ops.render.render(write_still=True)

    # turntable webm
    scene.frame_start = 1
    scene.frame_end = 120
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", frame=scene.frame_start)
    obj.rotation_euler = (0, 0, 6.28319)
    obj.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)

    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'WEBM'
    webm_path = output_dir / f"{model_path.stem}_turntable.webm"
    scene.render.filepath = str(webm_path)
    bpy.ops.render.render(animation=True, write_still=False)

    result = {
        "thumbnail": str(thumb_path.relative_to(output_dir.parent)),
        "webm": str(webm_path.relative_to(output_dir.parent)),
        "metadata": {
            "volume": round(volume, 3),
            "bbox": bbox,
            "faces": faces,
            "vertices": vertices
        }
    }

    print(json.dumps(result))


if __name__ == "__main__":
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]
    if len(argv) != 2:
        print(json.dumps({"error": "Usage: blender --background --python blender_pipeline.py -- <model_path> <output_dir>"}))
        sys.exit(1)
    main(argv[0], argv[1])
