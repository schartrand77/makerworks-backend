#!/usr/bin/env python3

import sys
import json
import hashlib
import logging
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from traceback import format_exc

import trimesh

logger = logging.getLogger("model_metadata")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def setup_file_logger(log_path: Path):
    file_handler = logging.FileHandler(log_path, mode="a")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info(f"📄 Log file created at {log_path}")
    return file_handler


def fail(msg: str, code: int = 1, extra: dict = None):
    logger.error(msg)
    result = {"error": msg}
    if extra:
        result.update(extra)
    print(json.dumps(result, indent=2))
    sys.exit(code)


def compute_geometry_hash(mesh: trimesh.Trimesh) -> str:
    geo_str = "".join(f"{v[0]:.6f}{v[1]:.6f}{v[2]:.6f}" for v in mesh.vertices)
    return hashlib.md5(geo_str.encode()).hexdigest()


def extract_with_trimesh(model_path: Path) -> dict:
    mesh = trimesh.load(str(model_path), force="mesh")

    if isinstance(mesh, trimesh.Scene):
        logger.info("ℹ️ Detected Scene: merging geometries.")
        mesh = trimesh.util.concatenate(mesh.dump())

    if not isinstance(mesh, trimesh.Trimesh):
        fail("❌ Loaded object is not a mesh", 2)

    if mesh.is_empty:
        fail("❌ Mesh is empty", 2)

    volume = float(mesh.volume)
    bounds = mesh.bounds.tolist()
    faces = int(len(mesh.faces))
    vertices = int(len(mesh.vertices))
    geometry_hash = compute_geometry_hash(mesh)

    logger.info(f"📊 Volume: {volume:.3f}")
    logger.info(f"📐 Bounding Box: {bounds}")
    logger.info(f"🔷 Faces: {faces}")
    logger.info(f"🔷 Vertices: {vertices}")
    logger.info(f"🔑 Geometry hash: {geometry_hash}")

    return {
        "volume": volume,
        "bbox": bounds,
        "faces": faces,
        "vertices": vertices,
        "geometry_hash": geometry_hash,
        "format": model_path.suffix.lower()[1:]
    }


def extract_3mf(model_path: Path) -> dict:
    if not zipfile.is_zipfile(model_path):
        fail("❌ Not a valid .3mf file (not a zip archive)")

    with zipfile.ZipFile(model_path, 'r') as z:
        names = z.namelist()
        model_xml_path = next((n for n in names if n.lower().endswith("3dmodel.model")), None)
        if not model_xml_path:
            fail("❌ No 3D model XML found in .3mf")

        with z.open(model_xml_path) as f:
            tree = ET.parse(f)
            root = tree.getroot()

            ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
            objects = root.findall(".//m:object", ns)

            result = {
                "object_count": len(objects),
                "objects": [],
                "format": "3mf"
            }

            for obj in objects:
                obj_id = obj.attrib.get('id')
                obj_type = obj.attrib.get('type')
                mesh = obj.find("m:mesh", ns)
                vertices = len(mesh.findall(".//m:vertex", ns)) if mesh is not None else 0
                triangles = len(mesh.findall(".//m:triangle", ns)) if mesh is not None else 0

                result["objects"].append({
                    "id": obj_id,
                    "type": obj_type,
                    "vertices": vertices,
                    "triangles": triangles
                })

            logger.info(f"📋 Extracted metadata from .3mf: {result}")
            return result


def main():
    try:
        argv = sys.argv
        if "--" not in argv:
            fail("❌ Usage: python extract_model_metadata.py -- <model_path>", 2)

        argv = argv[argv.index("--") + 1:]
        if not argv:
            fail("❌ No model file argument passed after '--'.", 2)

        model_path = Path(argv[0])

        if not model_path.exists():
            fail(f"❌ Model file does not exist: {model_path}", 2)

        log_file = model_path.with_suffix(".log")
        file_handler = setup_file_logger(log_file)

        logger.info(f"🚀 Starting metadata extraction for: {model_path}")

        ext = model_path.suffix.lower()[1:]
        logger.info(f"📦 Detected file extension: {ext}")

        if ext in {"stl", "obj", "ply"}:
            result = extract_with_trimesh(model_path)
        elif ext == "3mf":
            result = extract_3mf(model_path)
        else:
            fail(f"❌ Unsupported format: {ext}", 2)

        logger.info("✅ Metadata extraction completed successfully.")
        print(json.dumps(result, indent=2))

        logger.removeHandler(file_handler)
        file_handler.close()

    except Exception as e:
        logger.exception("❌ Fatal error during metadata extraction.")
        result = {
            "error": str(e),
            "traceback": format_exc()
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
