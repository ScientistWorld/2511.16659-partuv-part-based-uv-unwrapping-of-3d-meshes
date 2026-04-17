#!/usr/bin/env python3
"""Download Common Shapes dataset from GitHub.

The Common Shapes dataset contains 24 widely-used test meshes in computer graphics.
Repository: https://github.com/alecjacobson/common-3d-test-models
"""

import os
import urllib.request
import zipfile
import io

REPO_URL = "https://github.com/alecjacobson/common-3d-test-models"
ARCHIVE_URL = "https://github.com/alecjacobson/common-3d-test-models/archive/refs/heads/master.zip"
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(DATA_DIR, "common_shapes")

# Known mesh files in the repo
MESH_FILES = [
    "data/igea.obj",
    "data/bimba.obj",
    "data/stanford_bunny.obj",
    "data/xyzrgb_dragon.obj",
    "data/armadillo.obj",
    "data/happy_buddha.obj",
    "data/Lucy.obj",
    "data/nefertiti.obj",
    "data/shark.obj",
    "data/horse.obj",
    "data/lioness.obj",
    "data/lion.obj",
    "data/chinese_dragon.obj",
    "data/buddha.obj",
    "data/dinosaur.obj",
    "data/dog.obj",
    "data/gandhi.obj",
    "data/gargoyle.obj",
    "data/vase与中国.obj",
    "data/torus.obj",
    "data/screwdriver.obj",
    "data/helmet.obj",
    "data/cube.obj",
    "data/sphere.obj",
    "data/cylinder.obj",
]


def download_common_shapes():
    """Download and extract Common Shapes meshes."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    archive_path = os.path.join(DATA_DIR, "common_shapes.zip")

    if not os.path.exists(archive_path):
        print(f"Downloading Common Shapes from {ARCHIVE_URL}...")
        try:
            urllib.request.urlretrieve(ARCHIVE_URL, archive_path)
        except Exception as e:
            print(f"Download failed: {e}")
            # Fallback: try individual files
            print("Trying to download individual mesh files...")
            download_individual_files()
            return

    print("Extracting...")
    try:
        with zipfile.ZipFile(archive_path, 'r') as z:
            z.extractall(DATA_DIR)
        # Move extracted content to common_shapes/
        extracted_root = os.path.join(DATA_DIR, "common-3d-test-models-master")
        if os.path.exists(extracted_root):
            for item in os.listdir(extracted_root):
                src = os.path.join(extracted_root, item)
                dst = os.path.join(OUTPUT_DIR, item)
                if not os.path.exists(dst):
                    os.rename(src, dst)
            os.rmdir(extracted_root)
        # Clean up zip
        os.remove(archive_path)
        print(f"Extracted to {OUTPUT_DIR}")
    except Exception as e:
        print(f"Extraction failed: {e}")
        download_individual_files()


def download_individual_files():
    """Fallback: download individual mesh files."""
    base_url = "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/"
    for mesh_file in MESH_FILES:
        url = base_url + mesh_file
        local_path = os.path.join(OUTPUT_DIR, os.path.basename(mesh_file))
        if os.path.exists(local_path):
            print(f"  Skipping {mesh_file} (exists)")
            continue
        print(f"  Downloading {mesh_file}...")
        try:
            urllib.request.urlretrieve(url, local_path)
        except Exception as e:
            print(f"  Failed: {e}")


if __name__ == "__main__":
    download_common_shapes()
    # List what we got
    if os.path.exists(OUTPUT_DIR):
        files = os.listdir(OUTPUT_DIR)
        print(f"\nDownloaded {len(files)} files to {OUTPUT_DIR}:")
        for f in sorted(files)[:10]:
            print(f"  {f}")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")
