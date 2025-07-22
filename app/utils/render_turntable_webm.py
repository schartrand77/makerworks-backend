# /app/app/utils/render_turntable_webm.py

import subprocess
import tempfile
import pathlib
import uuid
import shutil


def generate_turntable_webm(model_path: str, output_dir: str) -> str:
    """
    Generate a turntable .webm animation of a 3D model using Blender.

    Args:
        model_path (str): Path to the input .stl or .glb file.
        output_dir (str): Directory where the output .webm will be saved.

    Returns:
        str: Path to the generated .webm file.

    Raises:
        RuntimeError: If rendering fails.
    """
    model_path = pathlib.Path(model_path).resolve()
    output_dir = pathlib.Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_filename = f"turntable_{uuid.uuid4().hex}.webm"
    output_path = output_dir / output_filename

    blender_script = _write_blender_script(model_path, output_path)

    try:
        result = subprocess.run(
            [
                "blender", "--background", "--python", str(blender_script)
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Blender rendering failed:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        ) from e
    finally:
        blender_script.unlink()

    if not output_path.exists():
        raise RuntimeError("Failed to generate .webm: output file not found.")

    return str(output_path)


def _write_blender_script(model_path: pathlib.Path, output_path: pathlib.Path) -> pathlib.Path:
    """
    Create a temporary Blender Python script that loads the model,
    sets up camera/lights, and renders a turntable animation to WebM.
    """
    script = f"""
import bpy
import sys

# clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# import model
ext = "{model_path.suffix.lower()}"
if ext == ".stl":
    bpy.ops.import_mesh.stl(filepath=r"{model_path}")
elif ext == ".glb":
    bpy.ops.import_scene.gltf(filepath=r"{model_path}")
else:
    print("Unsupported format:", ext)
    sys.exit(1)

obj = bpy.context.selected_objects[0]

# center and scale
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
obj.location = (0, 0, 0)
bpy.ops.transform.resize(value=(1, 1, 1))

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

# set render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.image_settings.codec = 'WEBM'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = r"{output_path}"
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 120

# animate turntable
obj.rotation_euler = (0, 0, 0)
obj.keyframe_insert(data_path="rotation_euler", frame=scene.frame_start)
obj.rotation_euler = (0, 0, 6.28319)  # 360 deg
obj.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)

bpy.ops.render.render(animation=True, write_still=False)
"""

    tmp_script = tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8")
    tmp_script.write(script)
    tmp_script.close()
    return pathlib.Path(tmp_script.name)
