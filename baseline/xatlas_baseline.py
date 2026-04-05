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

    # Write mesh to temp file for xatlas
    tmpdir = tempfile.mkdtemp()
    try:
        obj_path = os.path.join(tmpdir, "mesh.obj")
        write_obj(obj_path, mesh.vertices, mesh.faces)

        # Load mesh into xatlas
        mesh_data = xatlas.Mesh(obj_path)

        # Generate UV atlas
        atlas = xatlas.Atlas()
        atlas.add(mesh_data)

        # Set parameters
        chart_options = xatlas.ChartOptions()
        chart_options.k = params.get('k', 16)  # Balance parameter
        chart_options.max_iterations = params.get('max_iterations', 4096)

        pack_options = xatlas.PackOptions()
        pack_options.padding = params.get('padding', 1)

        atlas.generate(chart_options=chart_options, pack_options=pack_options)

        # Extract results
        vmapping = atlas.vertex_mappings[0]
        chart_ids = atlas.chart_mappings[0]
        uv_coords = atlas.uvs[0]

        # Get number of charts
        num_charts = len(set(chart_ids))

        return {
            'uv_coords': np.array(uv_coords),
            'chart_ids': np.array(chart_ids, dtype=np.int32),
            'num_charts': num_charts,
            'vertex_map': np.array(vmapping),
        }
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def unwrap_xatlas_fallback(mesh: Mesh, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Fallback UV unwrapping when xatlas is not available.

    Uses a simple parameterization approach:
    1. Compute face normals
    2. Cluster faces by normal similarity
    3. Flatten each cluster using LSCM-like approach
    """
    from method.lscm_flattening import lscm_flatten
    from sklearn.cluster import AgglomerativeClustering

    params = params or {}

    normals = mesh.normals()

    # Cluster faces by normal similarity (similar to what xatlas does)
    n_clusters = params.get('n_clusters', 50)

    if mesh.n_faces <= n_clusters:
        # Use each face as its own cluster or all as one
        if mesh.n_faces <= 2:
            face_indices = np.arange(mesh.n_faces)
            uv, dist = lscm_flatten(mesh.vertices, mesh.faces, face_indices)
            return {
                'uv_coords': uv,
                'chart_ids': np.zeros(mesh.n_faces, dtype=np.int32),
                'num_charts': 1,
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
        uv, dist = lscm_flatten(mesh.vertices, mesh.faces, face_indices)
        return {
            'uv_coords': uv,
            'chart_ids': np.zeros(mesh.n_faces, dtype=np.int32),
            'num_charts': 1,
        }

    # Get connected components within each cluster
    from method.partuv import PartUV
    partuv = PartUV(distortion_threshold=1.5, use_merge_heuristic=False, max_candidates=5)

    chart_faces = []
    for label in range(labels.max() + 1):
        mask = labels == label
        face_idx = np.where(mask)[0]
        if len(face_idx) > 0:
            connected = partuv._get_connected_faces(mesh.faces, face_idx)
            chart_faces.extend(connected)

    # Assign chart IDs
    chart_ids = np.zeros(mesh.n_faces, dtype=np.int32)
    for cid, cf in enumerate(chart_faces):
        chart_ids[cf] = cid

    # Flatten all charts together (they share the UV space)
    # For simplicity, flatten each chart and combine
    all_uvs = np.zeros((mesh.n_vertices, 2))

    for cid, cf in enumerate(chart_faces):
        if len(cf) == 0:
            continue
        # Scale each chart to avoid overlap
        scale = 1.0 / np.sqrt(len(chart_faces))
        offset_x = (cid % 8) * scale
        offset_y = (cid // 8) * scale

        uv, _ = lscm_flatten(mesh.vertices, mesh.faces, cf)
        all_uvs[np.unique(mesh.faces[cf])] = uv[np.unique(mesh.faces[cf])] * scale + np.array([offset_x, offset_y])

    return {
        'uv_coords': all_uvs,
        'chart_ids': chart_ids,
        'num_charts': len(chart_faces),
    }
