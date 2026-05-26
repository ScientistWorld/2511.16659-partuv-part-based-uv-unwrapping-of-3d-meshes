#!/usr/bin/env python3
"""xatlas baseline for UV unwrapping.

xatlas is a widely-used open-source UV unwrapping tool that uses greedy chart
growing with LSCM flattening. It serves as a key baseline in the paper.
"""

import numpy as np
import tempfile
import os
from typing import Tuple, Dict, Any, Optional

from data.mesh_loader import Mesh


def connected_face_components(faces: np.ndarray, face_indices: np.ndarray) -> list[np.ndarray]:
    """Split a subset of faces into connected components by shared mesh edges."""
    face_set = set(int(i) for i in face_indices)
    edge_to_faces: dict[tuple[int, int], list[int]] = {}
    for fi in face_set:
        face = faces[fi]
        for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge = (int(min(a, b)), int(max(a, b)))
            edge_to_faces.setdefault(edge, []).append(fi)

    adjacency: dict[int, set[int]] = {fi: set() for fi in face_set}
    for incident in edge_to_faces.values():
        if len(incident) < 2:
            continue
        for i in incident:
            adjacency[i].update(j for j in incident if j != i)

    components = []
    seen: set[int] = set()
    for start in sorted(face_set):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component = []
        while stack:
            cur = stack.pop()
            component.append(cur)
            for nxt in adjacency[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        components.append(np.asarray(component, dtype=np.int64))
    return components


def planar_project(mesh: Mesh, face_indices: np.ndarray) -> np.ndarray:
    """Simple diagnostic fallback projection used only if xatlas is unavailable."""
    verts = mesh.vertices
    unique = np.unique(mesh.faces[face_indices])
    centered = verts[unique] - verts[unique].mean(axis=0, keepdims=True)
    if len(unique) < 3:
        uv = np.zeros((mesh.n_vertices, 2), dtype=np.float64)
        uv[unique, : min(2, centered.shape[1])] = centered[:, :2]
        return uv
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    projected = centered @ vh[:2].T
    extent = np.ptp(projected, axis=0)
    extent[extent < 1e-12] = 1.0
    uv = np.zeros((mesh.n_vertices, 2), dtype=np.float64)
    uv[unique] = (projected - projected.min(axis=0)) / extent
    return uv


def write_obj(filepath: str, vertices: np.ndarray, faces: np.ndarray):
    """Write mesh to .obj file."""
    with open(filepath, 'w') as f:
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        for face in faces:
            if len(face) == 3:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
            elif len(face) == 4:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")


def unwrap_xatlas(mesh: Mesh, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Unwrap a mesh using xatlas.

    Args:
        mesh: Input 3D mesh
        params: Optional parameters for xatlas

    Returns:
        Dictionary with 'uv_coords', 'chart_ids', 'num_charts', or None if failed
    """
    try:
        import xatlas
    except ImportError:
        print("xatlas not available, using fallback")
        return unwrap_xatlas_fallback(mesh, params)

    params = params or {}

    # Use parametrize API (xatlas v0.x)
    positions = mesh.vertices.astype(np.float32)
    indices = mesh.faces.astype(np.uint32)
    # xatlas.parametrize expects vertex normals (not per-face normals)
    # Compute vertex normals by averaging face normals
    face_normals = mesh.normals()
    vertex_normals = np.zeros_like(mesh.vertices)
    for fi, f in enumerate(mesh.faces):
        for vi in f:
            vertex_normals[vi] += face_normals[fi]
    norms = np.linalg.norm(vertex_normals, axis=1, keepdims=True)
    norms[norms < 1e-10] = 1.0
    vertex_normals = (vertex_normals / norms).astype(np.float32)

    try:
        result = xatlas.parametrize(positions, indices, vertex_normals)
        chart_ids_per_vertex = np.array(result[0], dtype=np.int32)
        vertex_map = np.array(result[1], dtype=np.int32)  # (n_faces, 3) vertex indices
        uv_coords = np.array(result[2], dtype=np.float64)
        num_charts = len(set(chart_ids_per_vertex))

        # xatlas returns vertex-chart mapping. Assign each face to the most common chart among its vertices.
        face_chart_ids = np.zeros(mesh.n_faces, dtype=np.int32)
        for fi in range(mesh.n_faces):
            v0, v1, v2 = vertex_map[fi]
            c0, c1, c2 = chart_ids_per_vertex[v0], chart_ids_per_vertex[v1], chart_ids_per_vertex[v2]
            # All 3 vertices should be in the same chart
            if c0 == c1 == c2:
                face_chart_ids[fi] = c0
            else:
                # Majority vote
                from collections import Counter
                face_chart_ids[fi] = Counter([c0, c1, c2]).most_common(1)[0][0]

        # Build raw_chart_uvs and raw_chart_faces from xatlas result
        raw_chart_uvs = {}
        raw_chart_faces = {}
        for cid in range(num_charts):
            mask = face_chart_ids == cid
            chart_face_indices = np.where(mask)[0]
            if len(chart_face_indices) > 0:
                raw_chart_faces[cid] = chart_face_indices
                raw_chart_uvs[cid] = uv_coords.copy()

        return {
            'uv_coords': uv_coords,
            'chart_ids': face_chart_ids,
            'num_charts': num_charts,
            'vertex_map': vertex_map,
            # Don't pass raw_chart_uvs — xatlas uses its own vertex indexing
            # The global UV packing approach will be used for area distortion
        }
    except Exception as e:
        print(f"xatlas.parametrize failed: {e}, using fallback")
        return unwrap_xatlas_fallback(mesh, params)


def unwrap_xatlas_fallback(mesh: Mesh, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Fallback UV unwrapping when xatlas is not available.

    Uses a simple parameterization approach:
    1. Compute face normals
    2. Cluster faces by normal similarity
    3. Flatten each cluster using LSCM-like approach
    """
    from sklearn.cluster import AgglomerativeClustering

    params = params or {}

    normals = mesh.normals()

    # Cluster faces by normal similarity (similar to what xatlas does)
    n_clusters = params.get('n_clusters', 50)

    if mesh.n_faces <= n_clusters:
        # Use each face as its own cluster or all as one
        if mesh.n_faces <= 2:
            face_indices = np.arange(mesh.n_faces)
            uv = planar_project(mesh, face_indices)
            return {
                'uv_coords': uv,
                'chart_ids': np.zeros(mesh.n_faces, dtype=np.int32),
                'num_charts': 1,
                'raw_chart_uvs': {0: uv},
                'raw_chart_faces': {0: face_indices},
            }

    try:
        clustering = AgglomerativeClustering(
            n_clusters=min(n_clusters, mesh.n_faces // 2),
            linkage='ward'
        )
        labels = clustering.fit_predict(normals)
    except Exception:
        # Fallback to one chart
        face_indices = np.arange(mesh.n_faces)
        uv = planar_project(mesh, face_indices)
        return {
            'uv_coords': uv,
            'chart_ids': np.zeros(mesh.n_faces, dtype=np.int32),
            'num_charts': 1,
            'raw_chart_uvs': {0: uv},
            'raw_chart_faces': {0: face_indices},
        }

    chart_faces = []
    for label in range(labels.max() + 1):
        mask = labels == label
        face_idx = np.where(mask)[0]
        if len(face_idx) > 0:
            chart_faces.extend(connected_face_components(mesh.faces, face_idx))

    # Assign chart IDs
    chart_ids = np.zeros(mesh.n_faces, dtype=np.int32)
    for cid, cf in enumerate(chart_faces):
        chart_ids[cf] = cid

    # Flatten all charts together (they share the UV space)
    # For simplicity, flatten each chart and combine
    all_uvs = np.zeros((mesh.n_vertices, 2))
    raw_chart_uvs = {}
    raw_chart_faces = {}
    scale = 1.0 / np.sqrt(len(chart_faces))

    for cid, cf in enumerate(chart_faces):
        if len(cf) == 0:
            continue
        offset_x = (cid % 8) * scale
        offset_y = (cid // 8) * scale

        uv = planar_project(mesh, cf)
        all_uvs[np.unique(mesh.faces[cf])] = uv[np.unique(mesh.faces[cf])] * scale + np.array([offset_x, offset_y])

        # Store raw UVs for area distortion computation
        raw_chart_uvs[cid] = uv
        raw_chart_faces[cid] = cf

    return {
        'uv_coords': all_uvs,
        'chart_ids': chart_ids,
        'num_charts': len(chart_faces),
        'raw_chart_uvs': raw_chart_uvs,
        'raw_chart_faces': raw_chart_faces,
    }
