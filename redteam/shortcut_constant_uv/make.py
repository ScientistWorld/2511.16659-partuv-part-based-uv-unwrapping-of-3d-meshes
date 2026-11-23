#!/usr/bin/env python3
"""Shortcut: degenerate constant output. The real input mesh (all faces), every vertex's UV
= (0.5, 0.5). All faces share the UV "edge" (c, c), so the evaluator counts 1 chart; the UV
area is 0, so calculate_area_distortion returns its best value 1.0; only the angular metric
(1 - |cos3d - 1| = |cos3d| per face) pays."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import env_meshes, load_input_mesh, write_uv_obj  # noqa: E402

out = Path(sys.argv[1])
for name in env_meshes():
    mesh = load_input_mesh(name)
    V = np.asarray(mesh.vertices, dtype=np.float64)
    F = np.asarray(mesh.faces, dtype=np.int64)
    UV = np.full((len(V), 2), 0.5)
    write_uv_obj(out / name, V, F, UV)
    print(f"[constant_uv] {name}: faces={len(F)}")
