#!/usr/bin/env python3
"""UV-unwrapping metrics for the visible training split.

Self-contained on purpose: eval/train/ shares no code with eval/test/ or method/.

Everything scored is recomputed here from two raw inputs: the input mesh (held by the
evaluator) and the method's UV OBJ. Nothing the method writes besides the OBJ is read.

Per mesh
--------
1. Integrity. The output must be the input surface: every output triangle, after mapping
   its corners to the input's vertices by position, must be a triangle of the input mesh
   (a quad may be split along either diagonal), every non-degenerate input triangle must
   be present (once), and every UV used must be finite. 3-D quantities are always taken
   from the input mesh, never from the output file. A mesh that fails integrity is a
   failed mesh: it gets the worst value of every metric (charts = number of input
   triangles, area distortion = 10, angular score = 0).
2. Charts. Two input triangles that share an input edge are in the same chart when the
   output gives both endpoints of that edge the same UV in both triangles (the map is
   continuous across the edge). Charts are the connected components of this relation.
   UV coincidence between triangles that are not neighbours on the surface joins nothing.
3. Constraints (the paper's admissibility test, Algorithm 1 / Eq. 3): a chart is valid
   when (a) its area distortion (Eq. 3, per-triangle values clipped at 10, degenerate UV
   triangles count 10) is at most TAU = 1.25 (+1e-3 numerical slack), (b) no interior
   edge is folded (the two triangles of a continuous edge must lie on opposite sides of
   it in UV), and (c) the chart does not overlap itself in UV (point-sampling test).
   A chart that fails any constraint is scored as failed: each of its triangles counts
   as its own chart, its triangles get the worst angular value, and the mesh's area
   distortion becomes 10. The mesh then counts as unsuccessful.
4. Metrics: number of charts; area distortion = max over charts of Eq. 3; angular score =
   1 - mean over triangles of |cos(tangent, bitangent)| (paper Sec. 4.1, the official
   PartUV evaluation code's ``angular_distortion_mean``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

TAU = 1.25                 # paper Sec. 4.1: "A distortion threshold of 1.25 is used in all experiments"
TAU_SLACK = 1e-3           # numerical slack on TAU (OBJ text precision)
CLIP = 10.0                # paper Sec. 4.1: triangle-level distortion values clipped to 10
WORST_AREA = CLIP
WORST_ANGULAR = 0.0
MAX_ABS_UV = 1e9           # larger UV coordinates are treated as invalid output
MAX_OUTPUT_BYTES = 1_500_000_000
OVERLAP_SAMPLES_PER_FACE = 6.0
OVERLAP_MAX_CANDIDATES = 30_000_000
OVERLAP_TOL_FRAC = 1e-4    # duplicate samples tolerated per chart (fraction of its samples)
OVERLAP_TOL_ABS = 2        # ... and in absolute count
_PHI_X = 0.5 + 0.1180339887
_PHI_Y = 0.5 - 0.0819660113


class OBJError(ValueError):
    pass


# ----------------------------------------------------------------------------- OBJ parsing

def _parse_floats(lines: list[str], width: int, what: str) -> np.ndarray:
    if not lines:
        return np.zeros((0, width), dtype=np.float64)
    toks = " ".join(lines).split()
    if len(toks) == width * len(lines):
        try:
            return np.asarray(toks, dtype=np.float64).reshape(-1, width)
        except ValueError as exc:
            raise OBJError(f"bad {what} line: {exc}") from exc
    out = np.empty((len(lines), width), dtype=np.float64)
    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) < width:
            raise OBJError(f"{what} line with {len(parts)} values")
        try:
            out[i] = [float(p) for p in parts[:width]]
        except ValueError as exc:
            raise OBJError(f"bad {what} line: {exc}") from exc
    return out


def _parse_faces(lines: list[str]):
    """Return (corner_v, corner_vt, face_sizes); 1-based indices, vt = 0 when absent."""
    if not lines:
        return np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0, np.int64)
    toks = " ".join(lines).split()
    first = toks[0]
    n_slash = first.count("/")
    fast = len(toks) == 3 * len(lines) and "//" not in first and n_slash <= 2
    if fast:
        k = n_slash + 1
        flat = " ".join(toks).replace("/", " ").split()
        if len(flat) == k * len(toks):
            try:
                arr = np.asarray(flat, dtype=np.int64).reshape(-1, k)
            except ValueError as exc:
                raise OBJError(f"bad face line: {exc}") from exc
            cv = arr[:, 0]
            cvt = arr[:, 1] if k >= 2 else np.zeros(len(arr), np.int64)
            return cv, cvt, np.full(len(lines), 3, np.int64)
    cv, cvt, sizes = [], [], []
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            raise OBJError("face with fewer than 3 corners")
        sizes.append(len(parts))
        for p in parts:
            sub = p.split("/")
            try:
                cv.append(int(sub[0]))
                cvt.append(int(sub[1]) if len(sub) > 1 and sub[1] != "" else 0)
            except ValueError as exc:
                raise OBJError(f"bad face corner {p!r}") from exc
    return np.asarray(cv, np.int64), np.asarray(cvt, np.int64), np.asarray(sizes, np.int64)


def parse_obj(text: str):
    """Minimal OBJ reader: v, vt and f records (positive indices only)."""
    vs, vts, fs = [], [], []
    for line in text.splitlines():
        s = line.strip()
        if len(s) < 2:
            continue
        c = s[0]
        if c == "v":
            c1 = s[1]
            if c1 == " " or c1 == "\t":
                vs.append(s[2:])
            elif c1 == "t" and len(s) > 2 and (s[2] == " " or s[2] == "\t"):
                vts.append(s[3:])
        elif c == "f" and (s[1] == " " or s[1] == "\t"):
            fs.append(s[2:])
    V = _parse_floats(vs, 3, "v")
    VT = _parse_floats(vts, 2, "vt")
    cv, cvt, sizes = _parse_faces(fs)
    if len(cv) and (cv.min() < 1 or cv.max() > len(V)):
        raise OBJError("face references a vertex index out of range (only positive indices are supported)")
    return V, VT, cv, cvt, sizes


def _fan(sizes: np.ndarray):
    """Fan triangulation of polygon corners: returns (corner index triples, polygon id)."""
    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]])
    if np.all(sizes == 3):
        tri = starts[:, None] + np.arange(3)[None, :]
        return tri, np.arange(len(sizes))
    tris, pid = [], []
    for p, (st, k) in enumerate(zip(starts.tolist(), sizes.tolist())):
        for i in range(1, k - 1):
            tris.append((st, st + i, st + i + 1))
            pid.append(p)
    return np.asarray(tris, np.int64).reshape(-1, 3), np.asarray(pid, np.int64)


# ----------------------------------------------------------------------------- input mesh

def _tri_area(P0, P1, P2):
    return 0.5 * np.linalg.norm(np.cross(P1 - P0, P2 - P0), axis=1)


def _keys(a, b, c, n):
    t = np.sort(np.stack([a, b, c], axis=1), axis=1)
    return (t[:, 0] * n + t[:, 1]) * n + t[:, 2]


@dataclass
class InputMesh:
    name: str
    canon_pos: np.ndarray          # canonical vertex positions
    n_canon: int
    diag: float
    tol_match: float
    allowed_keys: np.ndarray       # sorted triangle keys (canonical ids) the output may contain
    key_group: np.ndarray          # group id per allowed key
    group_required: np.ndarray     # triangles that must be present per group (0 = optional group)
    group_max: np.ndarray          # triangles allowed per group
    n_required: int                # number of required triangles (worst-case chart count)
    tree: cKDTree = field(repr=False, default=None)


def prepare_input(name: str, text: str) -> InputMesh:
    V, _, cv, _, sizes = parse_obj(text)
    if len(V) == 0 or len(sizes) == 0:
        raise OBJError(f"input mesh {name} is empty")
    ext = V.max(axis=0) - V.min(axis=0)
    diag = float(np.linalg.norm(ext))
    if not np.isfinite(diag) or diag <= 0:
        raise OBJError(f"input mesh {name} has zero size")
    tol_weld = max(1e-6 * diag, 2e-7)
    # canonical vertices: weld positions closer than tol_weld
    pairs = cKDTree(V).query_pairs(tol_weld, output_type="ndarray")
    if len(pairs):
        g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(V), len(V)))
        _, lab = connected_components(g, directed=False)
    else:
        lab = np.arange(len(V))
    _, canon = np.unique(lab, return_inverse=True)
    canon = canon.reshape(-1)
    n_canon = int(canon.max()) + 1
    first = np.full(n_canon, len(V), dtype=np.int64)
    np.minimum.at(first, canon, np.arange(len(V)))
    canon_pos = V[first]

    corner_c = canon[cv - 1]
    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]])
    h_tol = max(1e-6 * diag, 1e-7)   # slivers thinner than this are optional (loaders may drop them)

    keys_all, group_all = [], []
    req, gmax = [], []
    gid = 0
    tri_mask = sizes == 3
    # triangles (vectorised)
    if tri_mask.any():
        st = starts[tri_mask]
        a, b, c = corner_c[st], corner_c[st + 1], corner_c[st + 2]
        k = _keys(a, b, c, n_canon)
        P0, P1, P2 = canon_pos[a], canon_pos[b], canon_pos[c]
        area = _tri_area(P0, P1, P2)
        emax = np.maximum(np.maximum(np.linalg.norm(P1 - P0, axis=1), np.linalg.norm(P2 - P1, axis=1)),
                          np.linalg.norm(P0 - P2, axis=1))
        with np.errstate(divide="ignore", invalid="ignore"):
            height = np.where(emax > 0, 2.0 * area / emax, 0.0)
        collapsed = (a == b) | (b == c) | (c == a)
        degenerate = collapsed | ~(height > h_tol)
        uk, inv, mult = np.unique(k, return_inverse=True, return_counts=True)
        inv = inv.reshape(-1)
        # a key is required when at least one of its copies is non-degenerate
        nondeg_key = np.zeros(len(uk), bool)
        np.logical_or.at(nondeg_key, inv, ~degenerate)
        keys_all.append(uk)
        group_all.append(np.arange(len(uk)) + gid)
        req.append(nondeg_key.astype(np.int64))
        gmax.append(mult.astype(np.int64))
        gid += len(uk)
    # polygons (k >= 4): any triangulation of the polygon's vertices
    for p in np.flatnonzero(~tri_mask).tolist():
        st, kk = int(starts[p]), int(sizes[p])
        poly = corner_c[st:st + kk]
        if len(set(poly.tolist())) < 3:
            continue
        P = canon_pos[poly]
        fan_area = float(_tri_area(np.repeat(P[:1], kk - 2, 0), P[1:-1], P[2:]).sum())
        if kk <= 6:
            idx = [(i, j, l) for i in range(kk) for j in range(i + 1, kk) for l in range(j + 1, kk)]
        else:
            idx = [(0, i, i + 1) for i in range(1, kk - 1)]
        idx = np.asarray(idx, np.int64)
        a, b, c = poly[idx[:, 0]], poly[idx[:, 1]], poly[idx[:, 2]]
        ok = (a != b) & (b != c) & (c != a)
        if not ok.any():
            continue
        keys_all.append(np.unique(_keys(a[ok], b[ok], c[ok], n_canon)))
        group_all.append(np.full(len(keys_all[-1]), gid))
        required = (kk - 2) if fan_area > h_tol * diag else 0
        req.append(np.asarray([required], np.int64))
        gmax.append(np.asarray([kk - 2], np.int64))
        gid += 1
    keys = np.concatenate(keys_all)
    groups = np.concatenate(group_all)
    order = np.argsort(keys, kind="stable")
    keys, groups = keys[order], groups[order]
    # a key listed twice (two groups) keeps its first group
    keep = np.ones(len(keys), bool)
    keep[1:] = keys[1:] != keys[:-1]
    keys, groups = keys[keep], groups[keep]
    group_required = np.concatenate(req)
    group_max = np.concatenate(gmax)
    return InputMesh(
        name=name, canon_pos=canon_pos, n_canon=n_canon, diag=diag, tol_match=1e-5 * diag,
        allowed_keys=keys, key_group=groups, group_required=group_required, group_max=group_max,
        n_required=int(group_required.sum()), tree=cKDTree(canon_pos),
    )


# ----------------------------------------------------------------------------- scoring

def failed_mesh(inp: InputMesh, reason: str) -> dict:
    return {
        "success": False, "integrity_ok": False, "reason": reason,
        "num_charts": float(inp.n_required), "raw_charts": None,
        "area_distortion": WORST_AREA, "angular_distortion": WORST_ANGULAR,
        "n_invalid_charts": None,
    }


def _cross2(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def _overlap(uv_tri: np.ndarray, s2: np.ndarray, lab: np.ndarray, n_charts: int):
    """Point-sampling self-overlap test per chart: (samples, duplicated samples) per chart.

    Each chart gets its own sample grid (about OVERLAP_SAMPLES_PER_FACE samples per
    triangle); a sample strictly inside two triangles of the same chart is a duplicate.
    The candidate budget is per chart, so one badly shaped chart cannot coarsen the
    grid of the others.
    """
    nf = len(lab)
    a2 = 0.5 * np.abs(s2)
    area_c = np.bincount(lab, weights=a2, minlength=n_charts)
    nface_c = np.bincount(lab, minlength=n_charts).astype(np.float64)
    fx_min, fx_max = uv_tri[:, :, 0].min(1), uv_tri[:, :, 0].max(1)
    fy_min, fy_max = uv_tri[:, :, 1].min(1), uv_tri[:, :, 1].max(1)
    ox = np.full(n_charts, np.inf)
    oy = np.full(n_charts, np.inf)
    mx = np.full(n_charts, -np.inf)
    my = np.full(n_charts, -np.inf)
    np.minimum.at(ox, lab, fx_min)
    np.minimum.at(oy, lab, fy_min)
    np.maximum.at(mx, lab, fx_max)
    np.maximum.at(my, lab, fy_max)
    with np.errstate(divide="ignore", invalid="ignore"):
        h = np.sqrt(area_c / (OVERLAP_SAMPLES_PER_FACE * np.maximum(nface_c, 1.0)))
    good_c = np.isfinite(h) & (h > 0) & (nface_c >= 2)
    h = np.where(good_c, h, 1.0)
    cap_c = 20.0 * OVERLAP_SAMPLES_PER_FACE * nface_c + 2000.0
    active = good_c[lab] & (s2 != 0)

    def candidates(h):
        hf = h[lab]
        i0 = np.ceil((fx_min - ox[lab]) / hf - _PHI_X)
        i1 = np.floor((fx_max - ox[lab]) / hf - _PHI_X)
        j0 = np.ceil((fy_min - oy[lab]) / hf - _PHI_Y)
        j1 = np.floor((fy_max - oy[lab]) / hf - _PHI_Y)
        ni = np.maximum(i1 - i0 + 1, 0)
        nj = np.maximum(j1 - j0 + 1, 0)
        cnt = np.where(active, ni * nj, 0.0)
        return i0, j0, nj, cnt

    for _ in range(60):
        i0, j0, nj, cnt = candidates(h)
        tot_c = np.bincount(lab, weights=cnt, minlength=n_charts)
        over = tot_c > cap_c
        if not over.any() and tot_c.sum() <= OVERLAP_MAX_CANDIDATES:
            break
        if over.any():
            h[over] = h[over] * np.sqrt(tot_c[over] / cap_c[over]) * 1.05
        else:
            h = h * math.sqrt(tot_c.sum() / OVERLAP_MAX_CANDIDATES) * 1.05
    else:
        i0, j0, nj, cnt = candidates(h)
    rows = np.minimum(np.floor((my - oy) / h), 2.0 ** 40).astype(np.int64) + 3
    rows[~good_c] = 1
    cnt = cnt.astype(np.int64)
    i0 = np.where(active, i0, 0).astype(np.int64)
    j0 = np.where(active, j0, 0).astype(np.int64)
    nj = np.where(active, nj, 1).astype(np.int64)
    keys_out, labs_out = [], []
    csum = np.cumsum(cnt)
    chunk = 2_000_000
    s = 0
    while s < nf:
        # largest e such that sum(cnt[s:e]) <= chunk (at least one face)
        lim = (csum[s - 1] if s > 0 else 0) + chunk
        e = int(np.searchsorted(csum, lim, side="right"))
        e = max(e, s + 1)
        e = min(e, nf)
        c = cnt[s:e]
        tot = int(c.sum())
        if tot > 0:
            fidx = np.repeat(np.arange(s, e), c)
            startpos = np.repeat(np.cumsum(c) - c, c)
            local = np.arange(tot, dtype=np.int64) - startpos
            njf = nj[fidx]
            ii = i0[fidx] + local // njf
            jj = j0[fidx] + local % njf
            lf = lab[fidx]
            qx = ox[lf] + (ii + _PHI_X) * h[lf]
            qy = oy[lf] + (jj + _PHI_Y) * h[lf]
            p = uv_tri[fidx]
            sg = np.sign(s2[fidx])
            w0 = (p[:, 1, 0] - qx) * (p[:, 2, 1] - qy) - (p[:, 1, 1] - qy) * (p[:, 2, 0] - qx)
            w1 = (p[:, 2, 0] - qx) * (p[:, 0, 1] - qy) - (p[:, 2, 1] - qy) * (p[:, 0, 0] - qx)
            w2 = (p[:, 0, 0] - qx) * (p[:, 1, 1] - qy) - (p[:, 0, 1] - qy) * (p[:, 1, 0] - qx)
            inside = (w0 * sg > 0) & (w1 * sg > 0) & (w2 * sg > 0)
            if inside.any():
                key = (ii + 1) * rows[lf] + (jj + 1)   # cell id within the chart's own grid
                keys_out.append(key[inside])
                labs_out.append(lf[inside])
        s = e
    if not keys_out:
        z = np.zeros(n_charts, np.int64)
        return z, z.copy()
    keys = np.concatenate(keys_out)
    labs = np.concatenate(labs_out)
    order = np.lexsort((keys, labs))
    keys, labs = keys[order], labs[order]
    dup = np.zeros(len(keys), bool)
    dup[1:] = (keys[1:] == keys[:-1]) & (labs[1:] == labs[:-1])
    hits = np.bincount(labs, minlength=n_charts)
    dups = np.bincount(labs[dup], minlength=n_charts)
    return hits, dups


def evaluate_output(inp: InputMesh, text: str) -> dict:
    """Score one UV OBJ (as text) against its input mesh."""
    try:
        V, VT, cv, cvt, sizes = parse_obj(text)
    except OBJError as exc:
        return failed_mesh(inp, f"unreadable OBJ: {exc}")
    if len(sizes) == 0:
        return failed_mesh(inp, "no faces")
    if len(VT) == 0 or len(cvt) == 0 or cvt.min() < 1 or cvt.max() > len(VT):
        return failed_mesh(inp, "missing or out-of-range vt indices (every face corner needs a UV)")
    if len(sizes) > 20 * max(inp.n_required, 1) + 1000:
        return failed_mesh(inp, "far more faces than the input mesh")
    if not np.all(np.isfinite(V)):
        return failed_mesh(inp, "non-finite vertex position")
    tri, _ = _fan(sizes)
    cvi = cv[tri] - 1                    # (F,3) output vertex index per corner
    cti = cvt[tri] - 1
    uv = VT[cti]                         # (F,3,2)
    if not np.all(np.isfinite(uv)) or np.abs(uv).max() > MAX_ABS_UV:
        return failed_mesh(inp, f"non-finite or out-of-range UV (|uv| must be <= {MAX_ABS_UV:g})")

    # map output vertices to canonical input vertices
    used = np.unique(cvi)
    dist, nn = inp.tree.query(V[used], k=1, distance_upper_bound=inp.tol_match)
    vmap = np.full(len(V), -1, np.int64)
    ok_v = np.isfinite(dist)
    vmap[used[ok_v]] = nn[ok_v]
    cc = vmap[cvi]                       # (F,3) canonical ids (-1 = not on the input)
    bad_corner = (cc < 0).any(axis=1)
    collapsed = ~bad_corner & ((cc[:, 0] == cc[:, 1]) | (cc[:, 1] == cc[:, 2]) | (cc[:, 2] == cc[:, 0]))
    n = inp.n_canon
    fk = np.where(bad_corner | collapsed, -1, _keys(np.maximum(cc[:, 0], 0), np.maximum(cc[:, 1], 0),
                                                     np.maximum(cc[:, 2], 0), n))
    pos = np.searchsorted(inp.allowed_keys, fk)
    pos = np.minimum(pos, len(inp.allowed_keys) - 1)
    found = (fk >= 0) & (inp.allowed_keys[pos] == fk)
    # output triangles that are not on the input: tolerated only when degenerate in 3-D
    # (they are then ignored entirely: no metric and no chart connectivity uses them)
    if (~found).any():
        cand = np.flatnonzero(~found)
        P = np.where(cc[cand, :, None] >= 0, inp.canon_pos[np.maximum(cc[cand], 0)], V[cvi[cand]])
        a3 = _tri_area(P[:, 0], P[:, 1], P[:, 2])
        off = cand[(a3 > (1e-7 * inp.diag) ** 2) & ~collapsed[cand]]
        if len(off):
            return failed_mesh(inp, f"{len(off)} output triangles are not triangles of the input mesh "
                                    f"(vertices must keep the input positions)")
    fidx = np.flatnonzero(found)
    grp = inp.key_group[pos[fidx]]
    gcount = np.bincount(grp, minlength=len(inp.group_required))
    over = gcount > inp.group_max
    if over.any():
        return failed_mesh(inp, f"{int(over.sum())} input faces appear more often than in the input")
    # distinct keys per group must cover the requirement
    gk = np.unique(np.stack([grp, fk[fidx]], 1), axis=0)
    gdistinct = np.bincount(gk[:, 0], minlength=len(inp.group_required))
    missing = gdistinct < inp.group_required
    if missing.any():
        return failed_mesh(inp, f"{int(inp.group_required[missing].sum() - gdistinct[missing].sum())} "
                                f"input triangles are missing from the output")
    # metric faces: one copy per key, in required groups
    req_face = inp.group_required[grp] > 0
    fidx, grp = fidx[req_face], grp[req_face]
    fkeys = fk[fidx]
    _, first_copy = np.unique(fkeys, return_index=True)
    fidx = fidx[np.sort(first_copy)]
    nf = len(fidx)
    if nf == 0:
        return failed_mesh(inp, "no input triangle present")
    C = cc[fidx]                         # (nf,3) canonical ids
    UV = uv[fidx]                        # (nf,3,2)
    P = inp.canon_pos[C]                 # (nf,3,3) input geometry
    # centre UVs per mesh for precision
    UV = UV - UV.reshape(-1, 2).mean(axis=0)

    # ---------------------------------------------------------------- charts
    he_f = np.repeat(np.arange(nf), 3)
    he_a = C[:, [0, 1, 2]].reshape(-1)
    he_b = C[:, [1, 2, 0]].reshape(-1)
    he_o = np.tile(np.array([2, 0, 1]), nf)          # opposite corner
    he_ua = UV[:, [0, 1, 2]].reshape(-1, 2)
    he_ub = UV[:, [1, 2, 0]].reshape(-1, 2)
    swap = he_a > he_b
    lo = np.where(swap, he_b, he_a)
    hi = np.where(swap, he_a, he_b)
    u_lo = np.where(swap[:, None], he_ub, he_ua)
    u_hi = np.where(swap[:, None], he_ua, he_ub)
    ekey = lo * n + hi
    order = np.argsort(ekey, kind="stable")
    ek = ekey[order]
    newgrp = np.ones(len(ek), bool)
    newgrp[1:] = ek[1:] != ek[:-1]
    gstart = np.flatnonzero(newgrp)
    gsize = np.diff(np.concatenate([gstart, [len(ek)]]))
    pair_start = gstart[gsize == 2]      # manifold interior edges only; others are seams
    h1, h2 = order[pair_start], order[pair_start + 1]
    f1, f2 = he_f[h1], he_f[h2]
    d_lo = np.linalg.norm(u_lo[h1] - u_lo[h2], axis=1)
    d_hi = np.linalg.norm(u_hi[h1] - u_hi[h2], axis=1)
    L = np.maximum(np.linalg.norm(u_lo[h1] - u_hi[h1], axis=1), np.linalg.norm(u_lo[h2] - u_hi[h2], axis=1))
    scale = 1.0 + np.maximum(np.abs(u_lo[h1]).max(1), np.abs(u_hi[h1]).max(1))
    tol = 1e-5 * L + 1e-12 * scale
    cont = (d_lo <= tol) & (d_hi <= tol) & (f1 != f2)
    f1c, f2c, h1c, h2c = f1[cont], f2[cont], h1[cont], h2[cont]
    g = coo_matrix((np.ones(len(f1c)), (f1c, f2c)), shape=(nf, nf))
    n_charts, lab = connected_components(g, directed=False)
    lab = lab.astype(np.int64)

    # ---------------------------------------------------------------- per-face quantities
    A3 = _tri_area(P[:, 0], P[:, 1], P[:, 2])
    e1 = UV[:, 1] - UV[:, 0]
    e2 = UV[:, 2] - UV[:, 0]
    S2 = 0.5 * _cross2(e1, e2)           # signed UV area
    A2 = np.abs(S2)
    sum3 = np.bincount(lab, weights=A3, minlength=n_charts)
    sum2 = np.bincount(lab, weights=A2, minlength=n_charts)
    with np.errstate(divide="ignore", invalid="ignore"):
        R = sum2 / sum3
        s = (A2 / A3) / R[lab]
        d = np.maximum(s, 1.0 / s)
    d = np.where(np.isfinite(d) & (A2 > 0), np.minimum(d, CLIP), CLIP)
    has3 = (A3 > 0).astype(np.float64)   # zero-area 3-D triangles are skipped (paper Eq. 3)
    nface_c = np.bincount(lab, minlength=n_charts)
    n3_c = np.bincount(lab, weights=has3, minlength=n_charts)
    dist_c = np.where(n3_c > 0, np.bincount(lab, weights=d * has3, minlength=n_charts) / np.maximum(n3_c, 1), 1.0)
    dist_c = np.where(sum3 > 0, dist_c, 1.0)

    # folds across continuous edges: the two opposite corners must lie on opposite sides
    uo1 = UV[f1c, he_o[h1c]]
    uo2 = UV[f2c, he_o[h2c]]
    o1 = _cross2(u_hi[h1c] - u_lo[h1c], uo1 - u_lo[h1c])
    o2 = _cross2(u_hi[h2c] - u_lo[h2c], uo2 - u_lo[h2c])
    folded = ~(o1 * o2 < 0)
    fold_c = np.bincount(lab[f1c[folded]], minlength=n_charts)

    # self-overlap
    hits_c, dup_c = _overlap(UV, 2.0 * S2, lab, n_charts)
    overlap_bad = dup_c > np.maximum(OVERLAP_TOL_ABS, OVERLAP_TOL_FRAC * hits_c)

    dist_bad = ~(dist_c <= TAU + TAU_SLACK)
    fold_bad = fold_c > 0
    invalid_c = dist_bad | fold_bad | overlap_bad

    # angular (tangent / bitangent orthogonality, paper Sec. 4.1)
    D = P[:, 1] - P[:, 0]
    E = P[:, 2] - P[:, 0]
    eu = e2[:, 1, None] * D - e1[:, 1, None] * E
    ev = -e2[:, 0, None] * D + e1[:, 0, None] * E
    nu = np.linalg.norm(eu, axis=1)
    nv = np.linalg.norm(ev, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        cosv = np.abs(np.einsum("ij,ij->i", eu, ev)) / (nu * nv)
    det = _cross2(e1, e2)
    degenerate_uv = ~(np.abs(det) > 1e-14 * np.linalg.norm(e1, axis=1) * np.linalg.norm(e2, axis=1))
    cosv = np.where(np.isfinite(cosv) & ~degenerate_uv, np.clip(cosv, 0.0, 1.0), 1.0)
    cos_scored = np.where(invalid_c[lab], 1.0, cosv)

    n_invalid = int(invalid_c.sum())
    valid_c = ~invalid_c
    charts = float(valid_c.sum() + nface_c[invalid_c].sum())
    area = float(dist_c[valid_c].max()) if valid_c.any() else WORST_AREA
    if n_invalid:
        area = WORST_AREA
    per_chart = None
    if n_charts <= 5000:   # compact per-chart statistics (diagnostics only, never scored)
        per_chart = {
            "nface": nface_c.tolist(), "dist": np.round(dist_c, 6).tolist(), "folds": fold_c.tolist(),
            "dups": dup_c.tolist(), "hits": hits_c.tolist(),
            "cos_sum": np.round(np.bincount(lab, weights=cosv, minlength=n_charts), 4).tolist(),
        }
    return {
        "success": n_invalid == 0, "integrity_ok": True, "reason": None if n_invalid == 0 else
        f"{n_invalid} chart(s) fail a constraint ({int(dist_bad.sum())} distortion>{TAU}, "
        f"{int(fold_bad.sum())} folded, {int(overlap_bad.sum())} overlapping)",
        "num_charts": charts, "raw_charts": int(n_charts),
        "area_distortion": float(area), "angular_distortion": float(1.0 - cos_scored.mean()),
        "n_invalid_charts": n_invalid,
        "diag": {
            "faces_scored": int(nf),
            "faces_in_invalid_charts": int(nface_c[invalid_c].sum()),
            "charts_over_tau": int(dist_bad.sum()), "charts_folded": int(fold_bad.sum()),
            "charts_overlapping": int(overlap_bad.sum()),
            "max_chart_distortion_all": float(dist_c.max()),
            "angular_unmasked": float(1.0 - cosv.mean()),
            "folded_edges": int(folded.sum()), "overlap_dup_samples": int(dup_c.sum()),
            "overlap_samples": int(hits_c.sum()),
        },
        "per_chart": per_chart,
    }


def aggregate(per_mesh: list[dict]) -> dict:
    """Dataset-level scores. Every value is finite: failed meshes carry worst values."""
    ch = np.asarray([m["num_charts"] for m in per_mesh], np.float64)
    ar = np.asarray([m["area_distortion"] for m in per_mesh], np.float64)
    an = np.asarray([m["angular_distortion"] for m in per_mesh], np.float64)
    ok = np.asarray([bool(m["success"]) for m in per_mesh])
    out = {
        "success_rate": float(100.0 * ok.mean()),
        "avg_charts": float(ch.mean()),
        "median_charts": float(np.median(ch)),
        "angular_distortion": float(an.mean()),
        "area_distortion": float(ar.mean()),
    }
    for k, v in out.items():
        if not math.isfinite(v):
            raise RuntimeError(f"non-finite aggregate {k}={v}")
    return out
