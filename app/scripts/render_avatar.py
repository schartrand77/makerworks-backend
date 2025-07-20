# scripts/render_avatar.py

import bpy
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:]
input_path, output_path, thumb_path = argv

use_gpu = os.getenv("USE_GPU") == "1"
prefs = bpy.context.preferences.addons['cycles'].preferences

if use_gpu:
    print("🔷 Using GPU")
    prefs.compute_device_type = "CUDA"
    for d in prefs.devices:
        d.use = True
else:
    print("🔷 Using CPU")
    prefs.compute_device_type = "NONE"

# Remove default cube
for obj in bpy.data.objects:
    bpy.data.objects.remove(obj)

# Load image as plane
bpy.ops.import_image.to_plane(files=[{"name": os.path.basename(input_path)}], directory=os.path.dirname(input_path))
bpy.context.scene.render.filepath = str(output_path)
bpy.context.scene.render.resolution_x = 256
bpy.context.scene.render.resolution_y = 256
bpy.ops.render.render(write_still=True)

bpy.context.scene.render.filepath = str(thumb_path)
bpy.context.scene.render.resolution_x = 64
bpy.context.scene.render.resolution_y = 64
bpy.ops.render.render(write_still=True)
