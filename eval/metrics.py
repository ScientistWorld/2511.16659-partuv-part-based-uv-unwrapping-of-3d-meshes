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
                             chart_ids: np.ndarray) -> Tuple[float, float]:
    """Compute area distortion for UV mapping.

    Uses the paper's definition:
    distortion(C) = max over charts (1/|C| * sum_{f in C} max(stretch(f), 1/stretch(f)))
    where stretch(f) = (area2D/area3D) / (sum area2D / sum area3D)

    Args:
        vertices: (N, 3) vertex positions
        faces: (M, 3) triangle indices
        uv_coords: (N, 2) UV coordinates
        chart_ids: (M,) chart ID for each face

    Returns:
        (area_distortion, overall_area_distortion)
    """
    unique_charts = np.unique(chart_ids)
    chart_distortions = []

    for cid in unique_charts:
        mask = chart_ids == cid
        chart_faces = faces[mask]

        if len(chart_faces) == 0:
            continue

        # Compute per-face areas and stretch
        stretches = []
        total_area_2d = 0.0
        total_area_3d = 0.0

        for f in chart_faces:
            # 3D area
            v0, v1, v2 = vertices[f[0]], vertices[f[1]], vertices[f[2]]
            e1 = v1 - v0
            e2 = v2 - v0
            area3d = 0.5 * np.linalg.norm(np.cross(e1, e2))
            total_area_3d += area3d

            # 2D area
            u0, u1, u2 = uv_coords[f[0]], uv_coords[f[1]], uv_coords[f[2]]
            e1_2d = u1 - u0
            e2_2d = u2 - u0
            area2d = 0.5 * abs(e1_2d[0] * e2_2d[1] - e1_2d[1] * e2_2d[0])
            total_area_2d += area2d

        if total_area_3d < 1e-10 or total_area_2d < 1e-10:
            chart_distortions.append(1.0)
            continue

        scale = total_area_2d / total_area_3d

        # Compute stretch per face
        for f in chart_faces:
            v0, v1, v2 = vertices[f[0]], vertices[f[1]], vertices[f[2]]
            e1 = v1 - v0
            e2 = v2 - v0
            area3d = 0.5 * np.linalg.norm(np.cross(e1, e2))

            u0, u1, u2 = uv_coords[f[0]], uv_coords[f[1]], uv_coords[f[2]]
            e1_2d = u1 - u0
            e2_2d = u2 - u0
            area2d = 0.5 * abs(e1_2d[0] * e2_2d[1] - e1_2d[1] * e2_2d[0])

            if area3d > 1e-10 and area2d > 1e-10:
                stretch = (area2d / area3d) / scale
                stretches.append(max(stretch, 1.0 / stretch))

        if stretches:
            chart_distortion = np.mean(stretches)
            chart_distortions.append(min(chart_distortion, 10.0))

    if not chart_distortions:
        return 1.0, 1.0

    # area_distortion = worst chart's distortion
    area_distortion = max(chart_distortions)

    # overall_area_distortion = mean of all face distortions
    all_stretches = []
    for f in faces:
        v0, v1, v2 = vertices[f[0]], vertices[f[1]], vertices[f[2]]
        e1 = v1 - v0
        e2 = v2 - v0
        area3d = 0.5 * np.linalg.norm(np.cross(e1, e2))

        u0, u1, u2 = uv_coords[f[0]], uv_coords[f[1]], uv_coords[f[2]]
        e1_2d = u1 - u0
        e2_2d = u2 - u0
        area2d = 0.5 * abs(e1_2d[0] * e2_2d[1] - e1_2d[1] * e2_2d[0])

        if area3d > 1e-10:
            stretch = area2d / area3d
            all_stretches.append(min(max(stretch, 1.0 / stretch), 10.0))
        else:
            all_stretches.append(1.0)

    overall_distortion = np.mean(all_stretches)

    return min(area_distortion, 10.0), min(overall_distortion, 10.0)


def evaluate_uv_mapping(mesh: Mesh, uv_coords: np.ndarray,
                        chart_ids: np.ndarray) -> Dict[str, float]:
    """Evaluate a UV mapping.

    Args:
        mesh: Input 3D mesh
        uv_coords: (N, 2) UV coordinates
        chart_ids: (M,) chart ID for each face

    Returns:
        Dictionary of metrics
    """
    num_charts = len(np.unique(chart_ids))

    seam_length = compute_seam_length(mesh.vertices, mesh.faces, chart_ids)

    angular_dist = compute_angular_distortion(mesh.vertices, uv_coords, mesh.faces)

    area_dist, overall_area_dist = compute_area_distortion(
        mesh.vertices, mesh.faces, uv_coords, chart_ids
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
