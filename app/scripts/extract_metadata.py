#!/usr/bin/env python3

import os
import subprocess
import sys
import json
import logging

# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("extract-metadata")

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "extract_metadata.py")  # blender will call this
BLENDER_EXECUTABLE = "/usr/bin/blender"  # <-- Change if Blender is elsewhere

# ─────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────
def main():
    if len(sys.argv) != 4:
        print("Usage: extract_metadata.py <model_path> <json_output> <preview_output>")
        sys.exit(1)

    model_path = sys.argv[1]
    json_output = sys.argv[2]
    preview_output = sys.argv[3]

    if not os.path.exists(model_path):
        logger.error(f"❌ Model file does not exist: {model_path}")
        sys.exit(1)

    command = [
        BLENDER_EXECUTABLE,
        "--background",
        "--python", SCRIPT_PATH,
        "--",
        model_path,
        json_output,
        preview_output
    ]

    logger.info(f"Running Blender headless extraction for: {os.path.basename(model_path)}")
    logger.debug(f"Command: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info("✅ Metadata extraction complete.")
        if result.stdout:
            logger.debug(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("❌ Blender script failed.")
        if e.stdout:
            logger.error(f"stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    main()
