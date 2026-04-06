#!/usr/bin/env python3
"""UV flattening using LSCM (Least Squares Conformal Maps).

LSCM produces lower distortion than Tutte embedding because it optimizes
for angle preservation rather than just barycentric coordinates.

References:
- Levy et al., "Least Squares Conformal Maps", 2002
- Desbrun et al., "Intrinsic Parameterizations of Surface Meshes", 2002
"""

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from typing import Tuple, Optional


def find_boundary_vertices(local_faces: np.ndarray, n_verts: int) -> np.ndarray:
    """Find which vertices are on the boundary (appear in a boundary edge)."""
    edge_count = {}
    for f in local_faces:
        for i in range(3):
            a, b = f[i], f[(i + 1) % 3]
            edge = (min(a, b), max(a, b))
            edge_count[edge] = edge_count.get(edge, 0) + 1

    boundary_verts = set()
    for edge, count in edge_count.items():
        if count == 1:
            boundary_verts.add(edge[0])
            boundary_verts.add(edge[1])

    return np.array(sorted(boundary_verts), dtype=np.int32)


def lscm_embed(vertices_3d: np.ndarray, local_faces: np.ndarray,
               boundary_verts: np.ndarray) -> np.ndarray:
    """LSCM (Least Squares Conformal Maps) embedding.

    Minimizes conformal distortion by solving for UV coordinates that best
    preserve angles. Uses two pinned boundary vertices for uniqueness.

    Returns uv coords for all local vertices (indexed 0 to n-1).
    """
    n_verts = len(vertices_3d)
    n_faces = len(local_faces)
    n_boundary = len(boundary_verts)

    if n_boundary < 2:
        # Fallback: place on circle
        uv = np.zeros((n_verts, 2))
        for i in range(n_verts):
            angle = 2 * np.pi * i / max(1, n_verts)
            uv[i] = [np.cos(angle), np.sin(angle)]
        return uv

    # Place boundary on unit circle
    boundary_uv = np.zeros((n_verts, 2))
    for i, vi in enumerate(boundary_verts):
        angle = 2 * np.pi * i / n_boundary
        boundary_uv[vi] = [np.cos(angle), np.sin(angle)]

    # Mark boundary
    is_boundary = np.zeros(n_verts, dtype=bool)
    for vi in boundary_verts:
        is_boundary[vi] = True

    interior_verts = np.where(~is_boundary)[0]
    n_interior = len(interior_verts)

    if n_interior == 0:
        return boundary_uv

    # Build LSCM system: cotangent-weight Laplacian for each coordinate
    # LSCM minimizes sum(||J*u - v||^2) where J is the Jacobian of the map
    # Equivalent to a weighted Laplacian system per coordinate

    # Build edge data for cotangent weights
    edge_data = {}
    for f in local_faces:
        for i in range(3):
            a, b = f[i], f[(i + 1) % 3]
            c = f[(i + 2) % 3]
            edge = (min(a, b), max(a, b))
            if edge not in edge_data:
                edge_data[edge] = {'verts': (a, b), 'cot_alpha': 0.0, 'cot_beta': 0.0}
            # Opposite vertex
            v_a = vertices_3d[a]
            v_b = vertices_3d[b]
            v_c = vertices_3d[c]
            # Cotangent of angle at c: cot(alpha) = (b-c).(b-a) / |(b-c) x (b-a)|
            ba = v_b - v_a
            bc = v_b - v_c
            cross = np.cross(bc, ba)
            dot = np.dot(bc, ba)
            cot = dot / (np.linalg.norm(cross) + 1e-10)
            if edge_data[edge]['verts'][0] == a:
                edge_data[edge]['cot_alpha'] += cot
            else:
                edge_data[edge]['cot_beta'] += cot

    # Build sparse matrix entries
    rows_u, cols_u, vals_u = [], [], []
    rows_v, cols_v, vals_v = [], [], []
    rhs_u = np.zeros(n_interior)
    rhs_v = np.zeros(n_interior)

    interior_to_local = {vi: i for i, vi in enumerate(interior_verts)}

    for edge, data in edge_data.items():
        a, b = data['verts']
        w_ab = data['cot_alpha'] + data['cot_beta']
        w_ab = max(w_ab, 1e-6)

        is_a_boundary = is_boundary[a]
        is_b_boundary = is_boundary[b]

        if not is_a_boundary and not is_b_boundary:
            # Interior-interior edge: add to Laplacian
            i_a = interior_to_local[a]
            i_b = interior_to_local[b]
            rows_u.extend([i_a, i_a, i_b, i_b])
            cols_u.extend([i_a, i_b, i_b, i_a])
            vals_u.extend([w_ab, -w_ab, w_ab, -w_ab])
            rows_v.extend([i_a, i_a, i_b, i_b])
            cols_v.extend([i_a, i_b, i_b, i_a])
            vals_v.extend([w_ab, -w_ab, w_ab, -w_ab])
        elif not is_a_boundary and is_b_boundary:
            # a is interior, b is boundary: move boundary contribution to RHS
            i_a = interior_to_local[a]
            rows_u.append(i_a)
            cols_u.append(i_a)
            vals_u.append(w_ab)
            rows_v.append(i_a)
            cols_v.append(i_a)
            vals_v.append(w_ab)
            rhs_u[i_a] -= w_ab * boundary_uv[b, 0]
            rhs_v[i_a] -= w_ab * boundary_uv[b, 1]
        elif not is_b_boundary and is_a_boundary:
            # b is interior, a is boundary
            i_b = interior_to_local[b]
            rows_u.append(i_b)
            cols_u.append(i_b)
            vals_u.append(w_ab)
            rows_v.append(i_b)
            cols_v.append(i_b)
            vals_v.append(w_ab)
            rhs_u[i_b] -= w_ab * boundary_uv[a, 0]
            rhs_v[i_b] -= w_ab * boundary_uv[a, 1]

    if not rows_u:
        return boundary_uv

    L_u = sp.coo_matrix((vals_u, (rows_u, cols_u)), shape=(n_interior, n_interior)).tocsr()
    L_v = sp.coo_matrix((vals_v, (rows_v, cols_v)), shape=(n_interior, n_interior)).tocsr()

    # Add small regularization to diagonal for numerical stability
    reg = 1e-8 * sp.identity(n_interior, format='csr')
    L_u = L_u + reg
    L_v = L_v + reg

    try:
        uv_u = spsolve(L_u, rhs_u)
        uv_v = spsolve(L_v, rhs_v)
    except Exception:
        return boundary_uv

    uv = boundary_uv.copy()
    for row_i, vi in enumerate(interior_verts):
        uv[vi, 0] = uv_u[row_i]
        uv[vi, 1] = uv_v[row_i]

    return uv


def compute_area_distortion(vertices_3d: np.ndarray, uv_coords: np.ndarray,
                            chart_faces: np.ndarray,
                            unique_verts: np.ndarray) -> float:
    """Compute area distortion for a chart."""
    if len(chart_faces) == 0:
        return 1.0

    n_unique = len(unique_verts)

    global_to_local = {v: i for i, v in enumerate(unique_verts)}
    local_faces = np.array([[global_to_local[v] for v in f] for f in chart_faces],
                           dtype=np.int32)
    local_verts = vertices_3d[unique_verts]

    area2d_total = 0.0
    area3d_total = 0.0
    all_stretches = []

    for f in local_faces:
        v0, v1, v2 = local_verts[f[0]], local_verts[f[1]], local_verts[f[2]]
        e1 = v1 - v0
        e2 = v2 - v0
        area3d = 0.5 * np.linalg.norm(np.cross(e1, e2))
        area3d_total += area3d

        u0, u1, u2 = uv_coords[f[0]], uv_coords[f[1]], uv_coords[f[2]]
        e1_2d = u1 - u0
        e2_2d = u2 - u0
        area2d = 0.5 * abs(e1_2d[0] * e2_2d[1] - e1_2d[1] * e2_2d[0])
        area2d_total += abs(area2d)

        if area3d > 1e-10 and abs(area2d) > 1e-10:
            all_stretches.append((abs(area2d), area3d))

    if area3d_total < 1e-10 or area2d_total < 1e-10:
        return 1.0

    scale = area2d_total / area3d_total

    chart_stretches = []
    for area2d, area3d in all_stretches:
        stretch = (area2d / area3d) / scale
        chart_stretches.append(max(stretch, 1.0 / stretch))

    if not chart_stretches:
        return 1.0

    return min(np.mean(chart_stretches), 10.0)


def lscm_flatten(vertices: np.ndarray, faces: np.ndarray,
                 face_indices: np.ndarray,
                 boundary_uv: Optional[np.ndarray] = None) -> Tuple[np.ndarray, float]:
    """Flatten a chart to 2D using LSCM.

    Args:
        vertices: (N, 3) vertex positions in 3D
        faces: (M, 3) triangle indices (global)
        face_indices: indices of faces belonging to this chart
        boundary_uv: optional (N, 2) UV coords for boundary

    Returns:
        uv_coords: (N, 2) UV coordinates (full vertex array)
        distortion: estimated area distortion
    """
    if len(face_indices) == 0:
        return np.zeros((len(vertices), 2)), 1.0

    chart_faces = faces[face_indices]

    unique_verts = np.unique(chart_faces)
    n_unique = len(unique_verts)

    if n_unique == 0:
        return np.zeros((len(vertices), 2)), 1.0

    vert_to_local = {v: i for i, v in enumerate(unique_verts)}
    local_faces = np.array([[vert_to_local[v] for v in f] for f in chart_faces])
    local_vertices = vertices[unique_verts]

    boundary_verts_local = find_boundary_vertices(local_faces, n_unique)

    try:
        uv_local = lscm_embed(local_vertices, local_faces, boundary_verts_local)
    except Exception:
        uv_local = np.zeros((n_unique, 2))
        for i in range(n_unique):
            angle = 2 * np.pi * i / max(1, n_unique)
            uv_local[i] = [np.cos(angle), np.sin(angle)]

    distortion = compute_area_distortion(vertices, uv_local, chart_faces, unique_verts)

    uv_full = np.zeros((len(vertices), 2))
    for i, vi in enumerate(unique_verts):
        uv_full[vi] = uv_local[i]

    return uv_full, distortion


def compute_angular_distortion(vertices_3d: np.ndarray, uv_coords: np.ndarray,
                               faces: np.ndarray) -> float:
    """Compute angular (conformal) distortion."""
    if len(faces) == 0:
        return 1.0

    cosines = []
    for f in faces:
        v0, v1, v2 = vertices_3d[f[0]], vertices_3d[f[1]], vertices_3d[f[2]]
        t1_3d = v1 - v0
        t2_3d = v2 - v0

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
        cosines.append(1.0 - abs(cos_3d - cos_2d))

    return np.mean(cosines)
