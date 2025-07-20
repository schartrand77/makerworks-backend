import bpy
import sys
import json
import hashlib
import logging
from pathlib import Path
from traceback import format_exc

logger = logging.getLogger("model_metadata")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

def setup_file_logger(log_path: Path):
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info(f"📄 Log file created at {log_path}")

def fail(msg: str, code: int = 1, extra: dict = None):
    """
    Log, emit JSON error, and exit with code.
    """
    logger.error(msg)
    result = {"error": msg}
    if extra:
        result.update(extra)
    print(json.dumps(result, indent=2))
    sys.exit(code)

try:
    argv = sys.argv
    if "--" not in argv:
        fail("❌ No model path provided. Usage: blender ... -- <model_path>", 2)

    argv = argv[argv.index("--") + 1:]
    if not argv:
        fail("❌ No model file argument passed after '--'.", 2)

    model_path = Path(argv[0])

    if not model_path.exists():
        fail(f"❌ Model file does not exist: {model_path}", 2)

    log_file = model_path.with_suffix(".log")
    setup_file_logger(log_file)

    logger.info(f"🚀 Starting metadata extraction for: {model_path}")

    bpy.ops.wm.read_factory_settings(use_empty=True)

    ext = model_path.suffix.lower()[1:]
    logger.info(f"📦 Detected file extension: {ext}")

    import_ok = False
    try:
        if ext == "stl":
            bpy.ops.import_mesh.stl(filepath=str(model_path))
            import_ok = True
        elif ext == "obj":
            bpy.ops.import_scene.obj(filepath=str(model_path))
            import_ok = True
        elif ext == "3mf":
            bpy.ops.import_scene.three_mf(filepath=str(model_path))
            import_ok = True
    except Exception as import_exc:
        fail(f"❌ Failed to import model: {import_exc}", 2)

    if not import_ok:
        fail(f"❌ Unsupported format: {ext}", 2)

    logger.info("✅ Model imported successfully.")

    if not bpy.context.selected_objects:
        fail("❌ No object selected after import.", 2)

    obj = bpy.context.selected_objects[0]
    mesh = obj.data

    if not mesh:
        fail("❌ Imported object has no mesh data.", 2)

    logger.info(f"🎯 Selected object: {obj.name}")

    try:
        mesh.calc_volume()
        mesh.calc_loop_triangles()
    except Exception as calc_exc:
        fail(f"❌ Failed to calculate mesh properties: {calc_exc}", 2)

    if not hasattr(mesh, "volume"):
        fail("❌ Mesh has no 'volume' property.", 2)

    volume = mesh.volume
    bbox = [list(v) for v in obj.bound_box]
    faces = len(mesh.polygons)
    verts = len(mesh.vertices)

    logger.info(f"📊 Volume: {volume:.3f}")
    logger.info(f"📐 Bounding Box: {bbox}")
    logger.info(f"🔷 Faces: {faces}")
    logger.info(f"🔷 Vertices: {verts}")

    geo_str = "".join(f"{v.co.x:.6f}{v.co.y:.6f}{v.co.z:.6f}" for v in mesh.vertices)
    geometry_hash = hashlib.md5(geo_str.encode()).hexdigest()

    logger.info(f"🔑 Geometry hash: {geometry_hash}")

    result = {
        "volume": volume,
        "bbox": bbox,
        "faces": faces,
        "vertices": verts,
        "geometry_hash": geometry_hash,
    }

    logger.info("✅ Metadata extraction completed successfully.")
    print(json.dumps(result, indent=2))

except Exception as e:
    # always catch top-level errors and report
    logger.exception("❌ Fatal error during metadata extraction.")
    result = {
        "error": str(e),
        "traceback": format_exc()
    }
    print(json.dumps(result, indent=2))
    sys.exit(1)
