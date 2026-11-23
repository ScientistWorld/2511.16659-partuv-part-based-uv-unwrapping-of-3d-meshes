#!/usr/bin/env python3
"""Shortcut: take the reference PartUV output and keep only its largest chart, dropping
every other face. Nothing checks that the output covers the input surface, so this
reports 1 chart per mesh with the largest chart's (low) distortion."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import REF_OUT, UV_NAME, chart_labels, compact, env_meshes, load_uv_obj, write_uv_obj  # noqa: E402

out = Path(sys.argv[1])
for name in env_meshes():
    V, F, UV = load_uv_obj(REF_OUT / name / UV_NAME)
    lab = chart_labels(F, UV)
    counts = np.bincount(lab)
    keep = lab == int(np.argmax(counts))
    V2, F2, UV2 = compact(V, F[keep], UV)
    write_uv_obj(out / name, V2, F2, UV2)
    print(f"[largest] {name}: charts {len(counts)} -> 1, faces {len(F)} -> {int(keep.sum())}")
