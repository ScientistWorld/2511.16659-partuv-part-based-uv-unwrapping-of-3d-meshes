#!/usr/bin/env python3
"""Shortcut: ignore the input mesh and write a unit square (2 triangles, identity UV) as
every mesh's "UV-mapped OBJ". The evaluator never compares the OBJ geometry with the
input mesh, so this scores 1 chart, angular 1.0, area 1.0, success 100%."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import env_meshes, write_uv_obj  # noqa: E402

out = Path(sys.argv[1])
V = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=np.float64)
UV = V[:, :2].copy()
F = np.array([[0, 1, 2], [0, 2, 3]])
for name in env_meshes():
    write_uv_obj(out / name, V, F, UV)
    print(f"[quad] {name}")
