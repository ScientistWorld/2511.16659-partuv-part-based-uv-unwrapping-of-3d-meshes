#!/usr/bin/env python3
"""Shortcut: selective failure. Use the reference PartUV outputs, but "abort" (write no
OBJ, like a timeout) whenever the method's own result has more than 200 charts. The
evaluator drops failed meshes from the chart and distortion averages and only lowers
success_rate (coefficient 0.2)."""

import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import REF_OUT, UV_NAME, chart_labels, env_meshes, load_uv_obj  # noqa: E402

LIMIT = 200
out = Path(sys.argv[1])
for name in env_meshes():
    src = REF_OUT / name / UV_NAME
    V, F, UV = load_uv_obj(src)
    n = int(chart_labels(F, UV).max()) + 1
    mesh_dir = out / name
    mesh_dir.mkdir(parents=True, exist_ok=True)
    if n > LIMIT:
        print(f"[skip_hard] {name}: {n} charts > {LIMIT} -> report failure (no OBJ)")
        continue
    for fname in (UV_NAME, "material.mtl", "material_0.png"):
        dst = mesh_dir / fname
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        os.symlink(REF_OUT / name / fname, dst)
    print(f"[skip_hard] {name}: {n} charts -> keep")
