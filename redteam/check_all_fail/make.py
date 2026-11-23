#!/usr/bin/env python3
"""Every held-out output is an unreadable file (the registration mesh is valid so the
folder is discovered). Checks what a fully failed run writes to scores_test.json."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import env_meshes, write_uv_obj  # noqa: E402

out = Path(sys.argv[1])
V = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=np.float64)
for name in env_meshes():
    if name == "woody":
        write_uv_obj(out / name, V, np.array([[0, 1, 2], [0, 2, 3]]), V[:, :2].copy())
    else:
        (out / name).mkdir(parents=True, exist_ok=True)
        (out / name / "final_components.obj").write_text("this run crashed before writing a mesh\n")
