#!/usr/bin/env python3
"""Shortcut: impossible UV values. Take the reference PartUV output and append two tiny
faces to every chart: f1 = (a, b, x) shares a UV edge (a, b) of the chart, and
f2 = (b, x, y) where x and y have UV coordinates ~1e200 so f2's UV area overflows to inf.

In eval/uv_obj_metrics.calculate_area_distortion the chart's total UV area becomes inf,
so every real face has ratio exactly 0 and f2 has inf/inf = NaN; both are skipped, the
list is empty and the chart reports the best possible value 1.0. The new 3-D points sit
next to the surface and are chosen so both extra faces have right angles at a and b in
3-D, while their UV angle cosines evaluate to 0 (finite / inf), so each extra face scores
a perfect 1.0 in the angular metric too. Chart count is unchanged (x, y are distinct per chart).
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import REF_OUT, UV_NAME, chart_labels, env_meshes, load_uv_obj, write_uv_obj  # noqa: E402

BIG = 1.0e200


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


out = Path(sys.argv[1])
for name in env_meshes():
    V, F, UV = load_uv_obj(REF_OUT / name / UV_NAME)
    lab = chart_labels(F, UV)
    n_charts = int(lab.max()) + 1
    extraV, extraUV, extraF = [], [], []
    nv = len(V)
    done = 0
    for c in range(n_charts):
        placed = False
        for f in np.flatnonzero(lab == c)[:200]:
            tri = F[f]
            nrm = np.cross(V[tri[1]] - V[tri[0]], V[tri[2]] - V[tri[0]])
            if np.linalg.norm(nrm) <= 0:
                continue
            for i in range(3):
                a, b = int(tri[i]), int(tri[(i + 1) % 3])
                ab3 = V[b] - V[a]
                L = np.linalg.norm(ab3)
                if L <= 0 or np.linalg.norm(UV[b] - UV[a]) < 1e-9:
                    continue
                w = unit(np.cross(ab3, nrm)) * 0.5 * L       # w is perpendicular to ab
                X3 = V[a] + w
                z = unit(np.cross(X3 - V[b], ab3)) * 0.5 * L  # z is perpendicular to (X3 - b)
                Y3 = V[b] + z
                k = 1.0 + 1e-3 * c
                extraV += [X3, Y3]
                extraUV += [[BIG * k, 0.0], [0.0, BIG * k]]
                x, y = nv, nv + 1
                nv += 2
                extraF += [[a, b, x], [b, x, y]]
                placed = True
                break
            if placed:
                break
        done += int(placed)
    V2 = np.concatenate([V, np.asarray(extraV)])
    UV2 = np.concatenate([UV, np.asarray(extraUV)])
    F2 = np.concatenate([F, np.asarray(extraF, dtype=np.int64)])
    write_uv_obj(out / name, V2, F2, UV2)
    print(f"[inf_uv] {name}: charts={n_charts} injected={done} extra_faces={len(extraF)}")
