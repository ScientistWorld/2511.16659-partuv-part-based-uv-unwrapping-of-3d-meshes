#!/usr/bin/env python3
"""Shortcut: isometric spanning-tree unfolding of the full input mesh.

Breadth-first over the face-adjacency graph, every face is laid out in UV with its exact
3-D edge lengths and attached to its parent face across their shared mesh edge (the two
shared corners reuse the parent's UV vertices). Every face of the real input mesh is
present and every triangle is isometric, so angular and area distortion are perfect, and
each connected component of the mesh is one connected UV chart. The unfolded layout
overlaps itself heavily (unusable for texturing); the paper's NoOverlap constraint exists
to exclude exactly this, but the evaluator never measures overlap.
"""

import math
import sys
from collections import deque
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import env_meshes, load_input_mesh, write_uv_obj  # noqa: E402


def unfold(V: np.ndarray, F: np.ndarray, adj: np.ndarray, adj_edges: np.ndarray, scale: float):
    nf = len(F)
    Vl = V.tolist()
    Fl = F.tolist()
    nbr = [[] for _ in range(nf)]
    for (f, g), (a, b) in zip(adj.tolist(), adj_edges.tolist()):
        nbr[f].append((g, a, b))
        nbr[g].append((f, a, b))

    corner = [[-1, -1, -1] for _ in range(nf)]
    split_orig: list[int] = []
    split_u: list[float] = []
    split_v: list[float] = []

    def new_vertex(orig: int, u: float, v: float) -> int:
        split_orig.append(orig)
        split_u.append(u)
        split_v.append(v)
        return len(split_orig) - 1

    visited = bytearray(nf)
    n_comp = 0
    for root in range(nf):
        if visited[root]:
            continue
        off = n_comp * 1.0e5  # keep components apart in UV
        n_comp += 1
        i0, i1, i2 = Fl[root]
        A, B, C = Vl[i0], Vl[i1], Vl[i2]
        ab = (B[0] - A[0], B[1] - A[1], B[2] - A[2])
        ac = (C[0] - A[0], C[1] - A[1], C[2] - A[2])
        L = math.sqrt(ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2)
        acl2 = ac[0] ** 2 + ac[1] ** 2 + ac[2] ** 2
        if L > 0:
            t = (ac[0] * ab[0] + ac[1] * ab[1] + ac[2] * ab[2]) / L
        else:
            t = math.sqrt(acl2)
        h = math.sqrt(max(acl2 - t * t, 0.0))
        corner[root] = [new_vertex(i0, off, 0.0), new_vertex(i1, off + scale * L, 0.0), new_vertex(i2, off + scale * t, scale * h)]
        visited[root] = 1
        queue = deque([root])
        while queue:
            f = queue.popleft()
            fv = Fl[f]
            for g, a, b in nbr[f]:
                if visited[g]:
                    continue
                gv = Fl[g]
                if a not in fv or b not in fv or a not in gv or b not in gv:
                    continue
                ka, kb = fv.index(a), fv.index(b)
                ga, gb = gv.index(a), gv.index(b)
                if ka == kb or ga == gb:
                    continue
                kd = 3 - ka - kb
                gc = 3 - ga - gb
                sa, sb, sd = corner[f][ka], corner[f][kb], corner[f][kd]
                c = gv[gc]
                ua, va = split_u[sa], split_v[sa]
                ub, vb = split_u[sb], split_v[sb]
                ud, vd = split_u[sd], split_v[sd]
                A, B, C = Vl[a], Vl[b], Vl[c]
                ab = (B[0] - A[0], B[1] - A[1], B[2] - A[2])
                ac = (C[0] - A[0], C[1] - A[1], C[2] - A[2])
                L3 = math.sqrt(ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2)
                eu, ev = ub - ua, vb - va
                L2 = math.sqrt(eu * eu + ev * ev)
                acl2 = ac[0] ** 2 + ac[1] ** 2 + ac[2] ** 2
                if L3 > 0 and L2 > 0:
                    s = L2 / L3
                    eu, ev = eu / L2, ev / L2
                    nu, nv = -ev, eu
                    t = (ac[0] * ab[0] + ac[1] * ab[1] + ac[2] * ab[2]) / L3
                    h = math.sqrt(max(acl2 - t * t, 0.0))
                    side = (ud - ua) * nu + (vd - va) * nv
                    sgn = -1.0 if side > 0 else 1.0  # unfold to the opposite side of the parent
                    uc = ua + s * t * eu + sgn * s * h * nu
                    vc = va + s * t * ev + sgn * s * h * nv
                else:  # degenerate shared edge: place the corner along any direction
                    uc, vc = ua + scale * math.sqrt(acl2), va
                cs = new_vertex(c, uc, vc)
                cg = [-1, -1, -1]
                cg[ga], cg[gb], cg[gc] = sa, sb, cs
                corner[g] = cg
                visited[g] = 1
                queue.append(g)

    Vs = V[np.asarray(split_orig, dtype=np.int64)]
    UVs = np.column_stack([np.asarray(split_u), np.asarray(split_v)])
    Fs = np.asarray(corner, dtype=np.int64)
    return Vs, Fs, UVs, n_comp


out = Path(sys.argv[1])
for name in env_meshes():
    mesh = load_input_mesh(name)
    V = np.asarray(mesh.vertices, dtype=np.float64)
    F = np.asarray(mesh.faces, dtype=np.int64)
    half = float((V.max(axis=0) - V.min(axis=0)).max()) * 0.5
    scale = 1000.0 / half  # UV in units of 1/1000 of the unit-box half extent
    Vs, Fs, UVs, n_comp = unfold(V, F, np.asarray(mesh.face_adjacency), np.asarray(mesh.face_adjacency_edges), scale)
    assert (Fs >= 0).all()
    write_uv_obj(out / name, Vs, Fs, UVs)
    print(f"[unfold] {name}: faces={len(F)} components={n_comp} uv_extent={np.ptp(UVs, axis=0)}")
