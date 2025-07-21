#!/usr/bin/env python3

import bpy
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:]
input_path, output_path, thumb_path = argv

use_gpu = os.getenv("USE_GPU") == "1"

# Enable GPU if requested
prefs = bpy.context.preferences.addons['cycles'].preferences
if use_gpu:
    print("🔷 Using GPU")
    prefs.compute_device_type = "CUDA"
    for d in prefs.devices:
        d.use = True
else:
    print("🔷 Using CPU")
    prefs.compute_device_type = "NONE"

# Enable 'Import Images as Planes' add-on
try:
    bpy.ops.wm.addon_enable(module='io_import_images_as_planes')
    print("✅ Enabled 'Import Images as Planes' add-on.")
except Exception as e:
    print(f"⚠️ Failed to enable 'Import Images as Planes': {e}")
    sys.exit(1)

# Remove all default objects
for obj in bpy.data.objects:
    bpy.data.objects.remove(obj, do_unlink=True)

# Import image as plane
try:
    bpy.ops.import_image.to_plane(
        files=[{"name": os.path.basename(input_path)}],
        directory=os.path.dirname(input_path)
    )
except Exception as e:
    print(f"❌ Failed to import image as plane: {e}")
    sys.exit(1)

# Configure render
scene = bpy.context.scene
scene.render.image_settings.file_format = 'PNG'

# Render full-size
scene.render.filepath = str(output_path)
scene.render.resolution_x = 256
scene.render.resolution_y = 256
print(f"🎨 Rendering full avatar → {output_path}")
bpy.ops.render.render(write_still=True)

# Render thumbnail
scene.render.filepath = str(thumb_path)
scene.render.resolution_x = 64
scene.render.resolution_y = 64
print(f"🎨 Rendering thumbnail → {thumb_path}")
bpy.ops.render.render(write_still=True)

print("✅ Avatar render complete.")
