#!/usr/bin/env python3
"""Evaluation metrics for UV unwrapping.

Computes the four key metrics:
1. Number of charts
2. Seam length
3. Angular (conformal) distortion
4. Area (equiareal) distortion
"""

import numpy as np
from typing import Dict, Any, List, Tuple

from data.mesh_loader import Mesh
from method.lscm_flattening import compute_angular_distortion


def compute_seam_length(vertices: np.ndarray, faces: np.ndarray,
                        chart_ids: np.ndarray) -> float:
    """Compute total seam length.

    Seam edges are edges shared by faces belonging to different charts.

    Args:
        vertices: (N, 3) vertex positions
        faces: (M, 3) triangle indices
        chart_ids: (M,) chart ID for each face

    Returns:
        Total seam length (UV space), normalized to [0,1] grid
    """
    edge_map = {}
    for fi, f in enumerate(faces):
        for i in range(3):
            a, b = f[i], f[(i + 1) % 3]
            edge = (min(a, b), max(a, b))
            if edge not in edge_map:
                edge_map[edge] = []
            edge_map[edge].append((fi, chart_ids[fi]))

    total_length = 0.0
    for (a, b), face_list in edge_map.items():
        if len(face_list) == 2:
            cid1 = face_list[0][1]
            cid2 = face_list[1][1]
            if cid1 != cid2:
                # This is a seam edge
                pa = vertices[a]
                pb = vertices[b]
                length = np.linalg.norm(pa - pb)
                total_length += length

    return total_length


def compute_area_distortion(vertices: np.ndarray, faces: np.ndarray,
                             uv_coords: np.ndarray,
                             chart_ids: np.ndarray,
                             raw_chart_uvs: Dict[int, np.ndarray] = None,
                             raw_chart_faces: Dict[int, np.ndarray] = None
                             ) -> Tuple[float, float]:
    """Compute area distortion for UV mapping.

    Uses per-face area ratio: area2d / area3d for each face,
    then reports the mean of max(stretch, 1/stretch) across faces.

    Args:
        vertices: (N, 3) vertex positions
        faces: (M, 3) triangle indices
        uv_coords: (N, 2) UV coordinates
        chart_ids: (M,) chart ID for each face
        raw_chart_uvs: Optional per-chart raw UV coords (unpacked, from PartUV)
        raw_chart_faces: Optional per-chart face indices

    Returns:
        (area_distortion, overall_area_distortion)
    """
    # Use per-chart raw UVs if provided (PartUV per-chart flattening)
    if raw_chart_uvs is not None and raw_chart_faces is not None:
        chart_max_stretches = []
        all_stretches = []

        for cid in sorted(raw_chart_uvs.keys()):
            raw_uv = raw_chart_uvs[cid]
            chart_face_list = raw_chart_faces[cid]

            if len(chart_face_list) == 0:
                continue

            # Compute total 2D and 3D area for this chart
            total_area_2d = 0.0
            total_area_3d = 0.0
            for fi in chart_face_list:
                f = faces[fi]
                v0, v1, v2 = vertices[f[0]], vertices[f[1]], vertices[f[2]]
                e1, e2 = v1 - v0, v2 - v0
                area3d = 0.5 * np.linalg.norm(np.cross(e1, e2))
                total_area_3d += area3d

                u0, u1, u2 = raw_uv[f[0]], raw_uv[f[1]], raw_uv[f[2]]
                e1_2d, e2_2d = u1 - u0, u2 - u0
                area2d = 0.5 * abs(e1_2d[0] * e2_2d[1] - e1_2d[1] * e2_2d[0])
                total_area_2d += area2d

            if total_area_3d < 1e-10 or total_area_2d < 1e-10:
                continue

            # Normalization: the sum of 2D areas / sum of 3D areas
            scale = total_area_2d / total_area_3d

            chart_stretches = []
            for fi in chart_face_list:
                f = faces[fi]
                v0, v1, v2 = vertices[f[0]], vertices[f[1]], vertices[f[2]]
                e1, e2 = v1 - v0, v2 - v0
                area3d = 0.5 * np.linalg.norm(np.cross(e1, e2))

                u0, u1, u2 = raw_uv[f[0]], raw_uv[f[1]], raw_uv[f[2]]
                e1_2d, e2_2d = u1 - u0, u2 - u0
                area2d = 0.5 * abs(e1_2d[0] * e2_2d[1] - e1_2d[1] * e2_2d[0])

                if area3d > 1e-10 and area2d > 1e-10:
                    stretch = (area2d / area3d) / scale
                    s = max(stretch, 1.0 / stretch)
                    chart_stretches.append(s)
                    all_stretches.append(s)

            if chart_stretches:
                chart_max_stretches.append(np.mean(chart_stretches))

        if not chart_max_stretches:
            return 1.0, 1.0

        area_distortion = max(chart_max_stretches)
        overall_distortion = np.mean(all_stretches)
        return area_distortion, overall_distortion

    # Fallback: packed UV coords (xatlas or global UV packing)
    # Compute per-face area ratio and stretch
    face_stretches = []
    for fi, f in enumerate(faces):
        v0, v1, v2 = vertices[f[0]], vertices[f[1]], vertices[f[2]]
        e1, e2 = v1 - v0, v2 - v0
        area3d = 0.5 * np.linalg.norm(np.cross(e1, e2))

        u0, u1, u2 = uv_coords[f[0]], uv_coords[f[1]], uv_coords[f[2]]
        e1_2d, e2_2d = u1 - u0, u2 - u0
        area2d = 0.5 * abs(e1_2d[0] * e2_2d[1] - e1_2d[1] * e2_2d[0])

        if area3d > 1e-10 and area2d > 1e-10:
            # For packed UVs: stretch = (area2d / area3d) normalized by the global scale
            # The global scale is approximately 1/sqrt(num_charts) for packed UVs
            # But we don't know it here, so we report the raw ratio
            # Normalize by median to get a meaningful metric
            stretch = area2d / area3d
            face_stretches.append(stretch)

    if not face_stretches:
        return 1.0, 1.0

    # Normalize by median stretch to get symmetric distortion
    # This makes the metric independent of UV packing scale
    median_stretch = np.median(face_stretches)
    if median_stretch < 1e-10:
        median_stretch = 1.0

    symmetric_stretches = []
    for s in face_stretches:
        normalized = s / median_stretch
        symmetric_stretches.append(max(normalized, 1.0 / normalized))

    overall_distortion = np.mean(symmetric_stretches)
    area_distortion = max(symmetric_stretches)

    return area_distortion, overall_distortion


def evaluate_uv_mapping(mesh: Mesh, uv_coords: np.ndarray,
                        chart_ids: np.ndarray,
                        raw_chart_uvs: Dict[int, np.ndarray] = None,
                        raw_chart_faces: Dict[int, np.ndarray] = None
                        ) -> Dict[str, float]:
    """Evaluate a UV mapping.

    Args:
        mesh: Input 3D mesh
        uv_coords: (N, 2) UV coordinates
        chart_ids: (M,) chart ID for each face
        raw_chart_uvs: Optional per-chart raw UV coords for accurate area distortion
        raw_chart_faces: Optional per-chart face indices

    Returns:
        Dictionary of metrics
    """
    num_charts = len(np.unique(chart_ids))

    seam_length = compute_seam_length(mesh.vertices, mesh.faces, chart_ids)

    angular_dist = compute_angular_distortion(mesh.vertices, uv_coords, mesh.faces)

    area_dist, overall_area_dist = compute_area_distortion(
        mesh.vertices, mesh.faces, uv_coords, chart_ids,
        raw_chart_uvs=raw_chart_uvs,
        raw_chart_faces=raw_chart_faces
    )

    return {
        'num_charts': float(num_charts),
        'seam_length': float(seam_length),
        'angular_distortion': float(angular_dist),
        'area_distortion': float(area_dist),
        'overall_area_distortion': float(overall_area_dist),
    }


def aggregate_metrics(metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
    """Aggregate metrics across multiple meshes.

    Args:
        metrics_list: List of per-mesh metric dicts

    Returns:
        Aggregated metrics (avg, median, etc.)
    """
    if not metrics_list:
        return {}

    n = len(metrics_list)

    avg_charts = np.mean([m['num_charts'] for m in metrics_list])
    median_charts = np.median([m['num_charts'] for m in metrics_list])
    median_seam = np.median([m['seam_length'] for m in metrics_list])
    avg_angular = np.mean([m['angular_distortion'] for m in metrics_list])
    avg_area = np.mean([m['area_distortion'] for m in metrics_list])
    avg_overall_area = np.mean([m['overall_area_distortion'] for m in metrics_list])

    return {
        'avg_charts': float(avg_charts),
        'median_charts': float(median_charts),
        'median_seam_length': float(median_seam),
        'angular_distortion': float(avg_angular),
        'area_distortion': float(avg_area),
        'overall_area_distortion': float(avg_overall_area),
    }
