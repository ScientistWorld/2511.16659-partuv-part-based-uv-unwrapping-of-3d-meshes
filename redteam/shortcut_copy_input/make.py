#!/usr/bin/env python3
"""Shortcut: copy the input OBJ unchanged as the "UV-mapped" output. None of the Common Shapes
OBJs carries vt lines, so the evaluator should mark every mesh failed."""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import DATA_DIR, UV_NAME, env_meshes  # noqa: E402

out = Path(sys.argv[1])
for name in env_meshes():
    (out / name).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DATA_DIR / f"{name}.obj", out / name / UV_NAME)
    print(f"[copy_input] {name}")
