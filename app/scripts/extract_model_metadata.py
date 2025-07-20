import bpy
import sys
import json
import hashlib

argv = sys.argv[sys.argv.index("--") + 1:]
model_path = argv[0]

bpy.ops.wm.read_factory_settings(use_empty=True)

ext = model_path.split(".")[-1].lower()
if ext == "stl":
    bpy.ops.import_mesh.stl(filepath=model_path)
elif ext == "obj":
    bpy.ops.import_scene.obj(filepath=model_path)
else:
    raise RuntimeError(f"Unsupported format: {ext}")

obj = bpy.context.selected_objects[0]
mesh = obj.data

mesh.calc_volume()
mesh.calc_loop_triangles()

volume = mesh.volume
bbox = [list(v) for v in obj.bound_box]
faces = len(mesh.polygons)
verts = len(mesh.vertices)

geo_str = "".join(f"{v.co.x}{v.co.y}{v.co.z}" for v in mesh.vertices)
geometry_hash = hashlib.md5(geo_str.encode()).hexdigest()

result = {
    "volume": volume,
    "bbox": bbox,
    "faces": faces,
    "vertices": verts,
    "geometry_hash": geometry_hash,
}

print(json.dumps(result))
