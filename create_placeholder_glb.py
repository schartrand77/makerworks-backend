import bpy

# clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# add cube
bpy.ops.mesh.primitive_cube_add(size=2)

# export as GLB
bpy.ops.export_scene.gltf(
    filepath="uploads/placeholders/placeholder.glb",
    export_format='GLB'
)
print("✅ placeholder.glb created.")
