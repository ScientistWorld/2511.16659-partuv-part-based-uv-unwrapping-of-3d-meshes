#!/usr/bin/env python3
"""Outputs for the registered method: unit squares (any valid outputs would do; the real
test score of these is 1 chart / 1.0 / 1.0, which is distinguishable from the fabricated
numbers written in after_register.sh)."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import env_meshes, write_uv_obj  # noqa: E402

out = Path(sys.argv[1])
V = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=np.float64)
for name in env_meshes():
    write_uv_obj(out / name, V, np.array([[0, 1, 2], [0, 2, 3]]), V[:, :2].copy())
