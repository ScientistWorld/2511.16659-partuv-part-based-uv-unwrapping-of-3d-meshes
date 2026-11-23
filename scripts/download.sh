#!/bin/bash
# Download the public artifacts this environment needs (~1.3 GB):
#  - Common Shapes (github.com/alecjacobson/common-3d-test-models): the 12 visible training
#    meshes listed in data/common_shapes_train.txt go to data/downloads/common_shapes/.
#    (The held-out meshes are kept, compressed, in eval/test/meshes/; if any is missing and
#    eval/test/ is present they are rebuilt from the same archive and checked by sha256.)
#  - PartField checkpoint (huggingface.co/mikaelaangel/partfield-ckpt) used by the reference method.
set -euo pipefail
export TMPDIR=/dev/shm
cd /home/user

COMMON_SHAPES_URL="https://github.com/alecjacobson/common-3d-test-models/archive/refs/heads/master.zip"
OUT_DIR="data/downloads/common_shapes"
ZIP="data/downloads/common_shapes_master.zip"
mkdir -p "$OUT_DIR"

need_zip=0
while read -r name; do
  [ -z "$name" ] && continue
  [ -f "$OUT_DIR/$name.obj" ] || need_zip=1
done < data/common_shapes_train.txt
if [ -f eval/test/fetch_meshes.py ]; then
  python3 - <<'PY' || need_zip=1
import json, sys
from pathlib import Path
man = json.loads(Path("eval/test/meshes/manifest.json").read_text())
sys.exit(0 if all((Path("eval/test/meshes") / e["file"]).is_file() for e in man["meshes"]) else 1)
PY
fi

if [ "$need_zip" = 1 ]; then
  echo "=== Downloading Common Shapes ==="
  curl -fL "$COMMON_SHAPES_URL" -o "$ZIP"
  python3 - "$ZIP" "$OUT_DIR" <<'PY'
import sys, zipfile
from pathlib import Path
zip_path, out_dir = sys.argv[1], Path(sys.argv[2])
train = [l.strip() for l in open("data/common_shapes_train.txt") if l.strip()]
with zipfile.ZipFile(zip_path) as zf:
    names = {Path(n).name: n for n in zf.namelist() if n.endswith(".obj")}
    for t in train:
        (out_dir / f"{t}.obj").write_bytes(zf.read(names[f"{t}.obj"]))
        print("extracted", t)
PY
  if [ -f eval/test/fetch_meshes.py ]; then
    python3 eval/test/fetch_meshes.py "$ZIP"
  fi
  rm -f "$ZIP"
else
  echo "Common Shapes training meshes already present"
fi

echo ""
echo "=== Downloading PartField checkpoint ==="
CKPT_DIR="data/downloads/partfield"
CKPT_PATH="${CKPT_DIR}/model_objaverse.ckpt"
mkdir -p "$CKPT_DIR"
if [ ! -f "$CKPT_PATH" ]; then
  wget -O "$CKPT_PATH" https://huggingface.co/mikaelaangel/partfield-ckpt/resolve/main/model_objaverse.ckpt
else
  echo "Checkpoint already present: $CKPT_PATH"
fi

echo ""
echo "Training meshes: $(ls "$OUT_DIR"/*.obj 2>/dev/null | wc -l)"
du -sh "$CKPT_PATH" 2>/dev/null || true
echo "Download complete!"
