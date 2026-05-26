#!/bin/bash
# Download datasets and model checkpoints needed by this environment.
# Estimated download: ~1.3 GB (Common Shapes archive + PartField checkpoint).
set -e
export TMPDIR=/dev/shm
cd /home/user

echo "=== Downloading datasets ==="

COMMON_SHAPES_DIR="data/common_shapes"
DOWNLOAD_DIR="data/downloads"
mkdir -p "$DOWNLOAD_DIR"
python3 - <<'PY'
import os
import shutil
import urllib.request
import zipfile

url = 'https://github.com/alecjacobson/common-3d-test-models/archive/refs/heads/master.zip'
zip_path = 'data/downloads/common_shapes_master.zip'
output_dir = 'data/common_shapes'

os.makedirs(output_dir, exist_ok=True)

if not any(name.endswith('.obj') for name in os.listdir(output_dir)):
    print(f'Downloading Common Shapes from {url}...')
    urllib.request.urlretrieve(url, zip_path)
    print('Extracting Common Shapes...')
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall('data/')
    extracted = 'data/common-3d-test-models-master'
    if os.path.exists(extracted):
        for item in os.listdir(extracted):
            src = os.path.join(extracted, item)
            dst = os.path.join(output_dir, item)
            if not os.path.exists(dst):
                shutil.move(src, dst)
        os.rmdir(extracted)
    os.remove(zip_path)
else:
    print('Common Shapes already present')
PY

echo ""
echo "=== Downloading PartField checkpoint ==="
CKPT_DIR="/home/user/data/downloads/partfield"
CKPT_PATH="${CKPT_DIR}/model_objaverse.ckpt"
mkdir -p "$CKPT_DIR"
if [ ! -f "$CKPT_PATH" ]; then
  wget -O "$CKPT_PATH" https://huggingface.co/mikaelaangel/partfield-ckpt/resolve/main/model_objaverse.ckpt
else
  echo "Checkpoint already present: $CKPT_PATH"
fi

mkdir -p /home/user/checkpoints/partfield
if [ ! -e /home/user/checkpoints/partfield/model_objaverse.ckpt ]; then
  ln -s "$CKPT_PATH" /home/user/checkpoints/partfield/model_objaverse.ckpt
fi

echo ""
echo "=== Available meshes ==="
find "$COMMON_SHAPES_DIR" -name "*.obj" 2>/dev/null | wc -l
echo "meshes found"
du -sh "$CKPT_PATH" 2>/dev/null || true

echo ""
echo "Download complete!"
