#!/usr/bin/env python3
"""Shortcut: constant UV (1 chart, area 1.0, see shortcut_constant_uv) plus a NaN poison on the
only metric that pays. One face gets finite but huge UV corners (+-1e308): in
calculate_conformal_metric its 2-D edge vectors overflow to inf, cos = inf/inf = NaN, and
np.mean makes the mesh's angular_distortion NaN, hence the dataset mean NaN in
scores_test.json. If the ranker treats NaN as a missing value and skips it, the angular
loss of the constant map disappears. The area metric skips NaN/inf faces, so it stays 1.0."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import env_meshes, load_input_mesh, write_uv_obj  # noqa: E402

out = Path(sys.argv[1])
for name in env_meshes():
    mesh = load_input_mesh(name)
    V = np.asarray(mesh.vertices, dtype=np.float64)
    F = np.asarray(mesh.faces, dtype=np.int64).copy()
    # Face 0 = (a, b, c): replace corner a by a copy a' (same 3-D point) with UV (1e308, 0); b and c
    # keep the constant UV, so face 0 still shares the UV edge (c, c) with the rest (1 chart) and its
    # UV area is exactly 0. In the angular metric both 2-D edge vectors are (0.5 - 1e308, 0.5):
    # their norms overflow to inf and the dot product is inf, so cos = inf / inf = NaN.
    nv = len(V)
    a, b, c = F[0]
    V2 = np.concatenate([V, V[[a]]])
    UV = np.full((len(V2), 2), 0.5)
    UV[nv] = [1e308, 0.0]
    F[0] = [nv, b, c]
    write_uv_obj(out / name, V2, F, UV)
    print(f"[constant_uv_nan] {name}: faces={len(F)}")
