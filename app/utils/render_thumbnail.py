#!/usr/bin/env python3
"""Generate a simple PNG thumbnail for a 3D model using trimesh."""

from __future__ import annotations

import sys
from pathlib import Path

import trimesh


DEFAULT_RESOLUTION = (256, 256)


def generate_thumbnail(model_path: Path, resolution: tuple[int, int] = DEFAULT_RESOLUTION) -> Path:
    """Render ``model_path`` to a PNG thumbnail.

    The thumbnail is saved next to the model with the same stem and a
    ``.png`` extension.
    """
    thumb_path = model_path.with_suffix(".png")

    try:
        mesh = trimesh.load(model_path, force="mesh")
    except Exception as exc:
        raise RuntimeError(f"Failed to load model: {exc}") from exc

    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(mesh.dump())

    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError("Loaded file is not a triangular mesh")

    scene = mesh.scene()
    png_data = scene.save_image(resolution=resolution, visible=False)
    if not png_data:
        raise RuntimeError("Thumbnail generation failed")

    with open(thumb_path, "wb") as f:
        f.write(png_data)

    return thumb_path


def main(argv: list[str]):
    if "--" not in argv:
        print("Usage: render_thumbnail.py -- <model_path>")
        return 1

    model_path = Path(argv[argv.index("--") + 1])
    try:
        out_path = generate_thumbnail(model_path)
    except Exception as exc:
        print(f"❌ {exc}")
        return 1

    print(f"✅ thumbnail saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
