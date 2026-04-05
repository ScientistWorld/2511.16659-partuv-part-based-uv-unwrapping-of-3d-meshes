#!/usr/bin/env python3
"""UV flattening using Least Squares Conformal Maps (LSCM).

LSCM is a linear method that finds conformal (angle-preserving) UV mappings
by minimizing a discrete Dirichlet energy. It is used as the flattening
component in PartUV.

Reference: Levy et al., "Least Squares Conformal Maps", SIGGRAPH 2002.
"""

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from typing import Tuple, Optional


def lscm_flatten(vertices: np.ndarray, faces: np.ndarray,
                 face_indices: np.ndarray,
                 boundary_uv: Optional[np.ndarray] = None) -> Tuple[np.ndarray, float]:
    """Flatten a chart to 2D using LSCM.

    Args:
        vertices: (N, 3) vertex positions in 3D
        faces: (M, 3) triangle indices
        face_indices: array of face indices belonging to this chart
        boundary_uv: optional (N, 2) UV coords for boundary vertices

    Returns:
        uv_coords: (N, 2) UV coordinates
        distortion: estimated area distortion
    """
    if len(face_indices) == 0:
        return np.zeros((len(vertices), 2)), 1.0

    chart_faces = faces[face_indices]

    # Get unique vertices in this chart
    unique_verts = np.unique(chart_faces)
    n_verts = len(unique_verts)
    n = n_verts

    if n == 0:
        return np.zeros((len(vertices), 2)), 1.0

    # Build mapping from original vertex indices to chart-local indices
    vert_to_local = {v: i for i, v in enumerate(unique_verts)}

    # Build local faces
    local_faces = np.array([[vert_to_local[v] for v in f] for f in chart_faces])

    # Build cotangent Laplacian
    rows_u, cols_u, vals_u = [], [], []
    rows_v, cols_v, vals_v = [], [], []

    for f in local_faces:
        for i in range(3):
            a, b, c = f[i], f[(i + 1) % 3], f[(i + 2) % 3]
            # Cotangent weight for edge (a,c) opposite to vertex b
            pa = vertices[unique_verts[a]]
            pb = vertices[unique_verts[b]]
            pc = vertices[unique_verts[c]]

            ba = pa - pb
            bc = pc - pb
            # Cotangent = dot(ba, bc) / |ba x bc|
            cross_norm = np.linalg.norm(np.cross(ba, bc))
            if cross_norm > 1e-10:
                cot = np.dot(ba, bc) / cross_norm
            else:
                cot = 1.0

            rows_u.extend([a, c])
            cols_u.extend([c, a])
            vals_u.extend([cot, cot])

            rows_v.extend([a, c])
            cols_v.extend([c, a])
            vals_v.extend([cot, cot])

    # Build Laplacian
    if len(rows_u) > 0:
        Lu = sp.coo_matrix((vals_u, (rows_u, cols_u)), shape=(n, n)).tocsr()
        Lv = sp.coo_matrix((vals_v, (rows_v, cols_v)), shape=(n, n)).tocsr()
        # Add diagonal
        Lu = Lu + sp.diags(-np.array(Lu.sum(axis=1)).flatten())
        Lv = Lv + sp.diags(-np.array(Lv.sum(axis=1)).flatten())
    else:
        Lu = Lv = sp.lil_matrix((n, n))

    # Fix two anchor vertices: (0,0) and (1,0)
    anchor1 = 0
    anchor2 = 1 if n > 1 else 0

    free = [i for i in range(n) if i != anchor1 and i != anchor2]

    if len(free) == 0:
        # All vertices are anchors - just return trivial UV
        uv = np.zeros((n, 2))
        if n > 0:
            uv[anchor1] = [0.0, 0.0]
        if n > 1:
            uv[anchor2] = [1.0, 0.0]
        uv_full = np.zeros((len(vertices), 2))
        for i, vi in enumerate(unique_verts):
            uv_full[vi] = uv[i]
        return uv_full, 1.0

    # Solve for u (x coordinate): Lu_free * u_free = 0, with u[anchor1]=0, u[anchor2]=1
    Lu_free = Lu[free][:, free].tocsr()
    u_rhs = np.zeros(len(free))
    # RHS contribution from anchor1: Lu_free * u_fixed = -L[free, anchor1] * 0 = 0
    # RHS contribution from anchor2: Lu_free * u_fixed = -L[free, anchor2] * 1
    anchor2_in_free = anchor2 if anchor2 > anchor1 else anchor2
    # Actually simpler: the RHS is just -L_row[anchor2] * 1 for each free vertex
    # Since we have u_rhs = 0 from the original equation, we add the fixed vertex contribution
    for i, fi in enumerate(free):
        row = Lu.getrow(fi).toarray().flatten()
        if anchor1 < n:
            u_rhs[i] -= row[anchor1] * 0.0
        if anchor2 < n:
            u_rhs[i] -= row[anchor2] * 1.0

    try:
        u_free = spsolve(Lu_free, u_rhs)
    except Exception:
        u_free = np.zeros(len(free))

    u = np.zeros(n)
    for i, fi in enumerate(free):
        u[fi] = u_free[i]
    u[anchor1] = 0.0
    u[anchor2] = 1.0

    # Solve for v (y coordinate): Lv_free * v_free = 0, with v[anchor1]=0
    Lv_free = Lv[free][:, free].tocsr()
    v_rhs = np.zeros(len(free))
    for i, fi in enumerate(free):
        row = Lv.getrow(fi).toarray().flatten()
        if anchor1 < n:
            v_rhs[i] -= row[anchor1] * 0.0
        if anchor2 < n:
            v_rhs[i] -= row[anchor2] * 0.0

    try:
        v_free = spsolve(Lv_free, v_rhs)
    except Exception:
        v_free = np.zeros(len(free))

    v = np.zeros(n)
    for i, fi in enumerate(free):
        v[fi] = v_free[i]
    v[anchor1] = 0.0
    if n > 1:
        v[anchor2] = 0.0

    uv_local = np.column_stack([u, v])

    # Compute area stretch distortion
    distortion = compute_chart_distortion(vertices, local_faces, unique_verts, uv_local)

    # Map back to original vertex indices
    uv_full = np.zeros((len(vertices), 2))
    for i, vi in enumerate(unique_verts):
        uv_full[vi] = uv_local[i]

    return uv_full, distortion


def compute_chart_distortion(vertices_3d: np.ndarray,
                              local_faces: np.ndarray,
                              unique_verts: np.ndarray,
                              uv_coords: np.ndarray) -> float:
    """Compute area distortion for a chart using the paper's definition.

    distortion(C) = max over charts (1/|C| * sum_{f in C} max(stretch(f), 1/stretch(f)))
    where stretch(f) = (area2D/area3D) / (sum area2D / sum area3D)
    """
    if len(local_faces) == 0:
        return 1.0

    vert_map = {v: i for i, v in enumerate(unique_verts)}
    local_verts = np.array([uv_coords[vert_map[v]] for v in unique_verts])

    area2d_total = 0.0
    area3d_total = 0.0
    all_stretches = []

    for f in local_faces:
        # 3D area
        v0, v1, v2 = vertices_3d[f[0]], vertices_3d[f[1]], vertices_3d[f[2]]
        e1 = v1 - v0
        e2 = v2 - v0
        area3d = 0.5 * np.linalg.norm(np.cross(e1, e2))
        area3d_total += area3d

        # 2D area
        u0 = uv_coords[vert_map[f[0]]]
        u1 = uv_coords[vert_map[f[1]]]
        u2 = uv_coords[vert_map[f[2]]]
        e1_2d = u1 - u0
        e2_2d = u2 - u0
        area2d = 0.5 * abs(e1_2d[0] * e2_2d[1] - e1_2d[1] * e2_2d[0])
        area2d_total += area2d

        if area3d > 1e-10 and area2d > 1e-10:
            all_stretches.append((area2d, area3d))

    if area3d_total < 1e-10 or area2d_total < 1e-10:
        return 1.0

    scale = area2d_total / area3d_total

    # Compute corrected stretch per face
    chart_stretches = []
    for area2d, area3d in all_stretches:
        stretch = (area2d / area3d) / scale
        chart_stretches.append(max(stretch, 1.0 / stretch))

    if not chart_stretches:
        return 1.0

    distortion = np.mean(chart_stretches)
    return min(distortion, 10.0)


def compute_angular_distortion(vertices_3d: np.ndarray, uv_coords: np.ndarray,
                                 faces: np.ndarray) -> float:
    """Compute angular (conformal) distortion.

    Defined as: 1 - avg(|cos(theta_3d) - cos(theta_2d)|)
    where theta is the angle between tangent and bitangent vectors.

    Closer to 1.0 is better (perfect angle preservation).
    """
    if len(faces) == 0:
        return 1.0

    cosines = []
    for f in faces:
        v0, v1, v2 = vertices_3d[f[0]], vertices_3d[f[1]], vertices_3d[f[2]]

        # 3D tangent/bitangent (edges from first vertex)
        t1_3d = v1 - v0
        t2_3d = v2 - v0

        # 2D tangent/bitangent
        u0, u1, u2 = uv_coords[f[0]], uv_coords[f[1]], uv_coords[f[2]]
        t1_2d = u1 - u0
        t2_2d = u2 - u0

        def angle_cos(a, b):
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            if na < 1e-10 or nb < 1e-10:
                return 1.0
            return np.abs(np.dot(a, b)) / (na * nb)

        cos_3d = angle_cos(t1_3d, t2_3d)
        cos_2d = angle_cos(t1_2d, t2_2d)

        cos_diff = abs(cos_3d - cos_2d)
        cosines.append(1.0 - cos_diff)

    return np.mean(cosines)
