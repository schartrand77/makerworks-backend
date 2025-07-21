# render_turntable_webm.py

import bpy
import sys
import os

model_path = sys.argv[-2]
output_webm = sys.argv[-1]

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import STL/OBJ/3MF
ext = os.path.splitext(model_path)[1].lower()
if ext == ".stl":
    bpy.ops.import_mesh.stl(filepath=model_path)
elif ext == ".obj":
    bpy.ops.import_scene.obj(filepath=model_path)
elif ext == ".3mf":
    bpy.ops.import_mesh.3mf(filepath=model_path)
else:
    print(f"Unsupported format: {ext}")
    sys.exit(1)

obj = bpy.context.selected_objects[0]

# Center
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
obj.location = (0, 0, 0)

# Add camera
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (0, -3, 1)
cam.rotation_euler = (1.2, 0, 0)

# Add light
light = bpy.data.objects.new("Light", bpy.data.lights.new(name="Light", type='SUN'))
bpy.context.scene.collection.objects.link(light)
light.rotation_euler = (0.8, 0, 0)

# Set render settings
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 72  # 3s at 24fps
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'WEBM'
scene.render.ffmpeg.codec = 'VP9'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.filepath = output_webm

# Animate rotation
obj.rotation_euler = (0, 0, 0)
obj.keyframe_insert(data_path="rotation_euler", frame=1)
obj.rotation_euler = (0, 0, 6.28319)  # 360 deg
obj.keyframe_insert(data_path="rotation_euler", frame=72)

bpy.ops.render.render(animation=True)
