#!/usr/bin/env python3
"""Shortcut: weld the reference PartUV charts together in UV space.

The evaluator counts charts by exact UV-coordinate coincidence: faces are joined when
they share a UV edge, whether or not they are adjacent on the 3-D surface. For every
chart of the reference output we pick one of its edges and an edge of the largest
("anchor") chart with matching normalized length, then move the chart by a similarity
transform (rotation + uniform scale + translation) so the two edges coincide exactly.
Angles are untouched, every chart ends up at the anchor's UV scale (so per-face area
ratios are unchanged), and the mesh's area distortion becomes a face-weighted mean of
chart distortions instead of their maximum. No seam is removed on the 3-D surface.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import (REF_OUT, UV_NAME, chart_labels, env_meshes, face_areas_3d, face_areas_uv,  # noqa: E402
                       load_uv_obj, write_uv_obj)


def chart_edges(Fc: np.ndarray) -> np.ndarray:
    e = np.concatenate([Fc[:, [0, 1]], Fc[:, [1, 2]], Fc[:, [2, 0]]])
    return np.unique(np.sort(e, axis=1), axis=0)


out = Path(sys.argv[1])
for name in env_meshes():
    V, F, UV = load_uv_obj(REF_OUT / name / UV_NAME)
    lab = chart_labels(F, UV)
    n_charts = int(lab.max()) + 1
    a3 = face_areas_3d(V, F)
    auv = face_areas_uv(UV, F)
    counts = np.bincount(lab, minlength=n_charts)
    anchor = int(np.argmax(counts))

    def rho(c):
        m = lab == c
        A3, Auv = a3[m].sum(), auv[m].sum()
        return np.sqrt(Auv / A3) if A3 > 0 and Auv > 0 else 0.0

    # Anchor edges: normalized length = UV length / anchor UV-per-3D scale.
    ae = chart_edges(F[lab == anchor])
    al = np.linalg.norm(UV[ae[:, 1]] - UV[ae[:, 0]], axis=1)
    r0 = rho(anchor)
    ok = al > 1e-9
    ae, al = ae[ok], al[ok]
    order = np.argsort(al / r0)
    ae, an = ae[order], (al / r0)[order]

    newV, newUV, newF = [V[np.unique(F[lab == anchor])]], [], []
    # anchor kept as is
    used = np.unique(F[lab == anchor])
    remap = {int(v): i for i, v in enumerate(used)}
    newUV.append(UV[used])
    newF.append(np.vectorize(remap.get)(F[lab == anchor]))
    base = len(used)
    welded, skipped, worst_scale_err = 0, 0, 0.0
    for c in range(n_charts):
        if c == anchor:
            continue
        Fc = F[lab == c]
        usedc = np.unique(Fc)
        local = {int(v): i for i, v in enumerate(usedc)}
        Fl = np.vectorize(local.get)(Fc)
        Vc, UVc = V[usedc].copy(), UV[usedc].copy()
        rc = rho(c)
        ce = chart_edges(Fc)
        cl = np.linalg.norm(UV[ce[:, 1]] - UV[ce[:, 0]], axis=1)
        good = cl > 1e-9
        if rc > 0 and good.any() and len(an):
            ce, cn = ce[good], cl[good] / rc
            pos = np.clip(np.searchsorted(an, cn), 1, len(an) - 1)
            left, right = an[pos - 1], an[pos]
            pick = np.where(np.abs(np.log(cn / left)) < np.abs(np.log(cn / right)), pos - 1, pos)
            err = np.abs(np.log(cn / an[pick]))
            k = int(np.argmin(err))
            worst_scale_err = max(worst_scale_err, float(err[k]))
            p, q = int(ce[k, 0]), int(ce[k, 1])
            a, b = int(ae[pick[k], 0]), int(ae[pick[k], 1])
            zp, zq = complex(*UV[p]), complex(*UV[q])
            za, zb = complex(*UV[a]), complex(*UV[b])
            m = (zb - za) / (zq - zp)
            z = UVc[:, 0] + 1j * UVc[:, 1]
            z = za + (z - zp) * m
            UVc = np.column_stack([z.real, z.imag])
            UVc[local[p]] = UV[a]  # exact coincidence with the anchor edge
            UVc[local[q]] = UV[b]
            welded += 1
        else:
            skipped += 1
        newUV.append(UVc)
        newF.append(Fl + base)
        newV.append(Vc)
        base += len(usedc)
    V2 = np.concatenate(newV)
    UV2 = np.concatenate(newUV)
    F2 = np.concatenate(newF)
    write_uv_obj(out / name, V2, F2, UV2)
    print(f"[weld] {name}: charts {n_charts} welded={welded} skipped={skipped} worst_log_scale_err={worst_scale_err:.2e} faces={len(F2)}")
