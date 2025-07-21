#!/usr/bin/env python3

import sys
import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path

def extract_3mf(model_path: Path) -> dict:
    if not zipfile.is_zipfile(model_path):
        raise ValueError("Not a valid .3mf file (not a zip archive)")

    with zipfile.ZipFile(model_path, 'r') as z:
        # Look for the 3D model XML file
        names = z.namelist()
        model_xml_path = next((n for n in names if n.lower().endswith("3dmodel.model")), None)
        if not model_xml_path:
            raise ValueError("No 3D model XML found in .3mf")

        with z.open(model_xml_path) as f:
            tree = ET.parse(f)
            root = tree.getroot()

            # namespace handling
            ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
            objects = root.findall(".//m:object", ns)

            result = {
                "object_count": len(objects),
                "objects": []
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

            return result

def main():
    if len(sys.argv) < 2:
        print("Usage: extract_3mf_metadata.py <path-to-.3mf>")
        sys.exit(2)

    model_path = Path(sys.argv[1])
    if not model_path.exists():
        print(f"File not found: {model_path}")
        sys.exit(2)

    try:
        metadata = extract_3mf(model_path)
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
