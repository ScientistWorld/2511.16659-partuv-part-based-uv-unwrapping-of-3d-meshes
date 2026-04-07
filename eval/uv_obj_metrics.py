#!/usr/bin/env python3
"""Metric computation for UV-mapped OBJ meshes.

This is adapted from the official PartUV evaluation code so that evaluation
stays separate from method/ and can score any UV-mapped OBJ output.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict

import numpy as np
import trimesh


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> None:
        rx = self.find(x)
        ry = self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1


def calculate_3d_face_area(vertices: np.ndarray, face: np.ndarray) -> float:
    v0, v1, v2 = vertices[face]
    return np.linalg.norm(np.cross(v1 - v0, v2 - v0)) / 2.0


def calculate_uv_face_area(uvs: np.ndarray) -> float:
    shifts = np.roll(uvs, -1, axis=0)
    return float(abs(np.sum(uvs[:, 0] * shifts[:, 1] - shifts[:, 0] * uvs[:, 1])) / 2.0)


def normalize_to_unit_box(vertices: np.ndarray) -> np.ndarray:
    vertices = vertices.astype(np.float64, copy=False)
    v_min = vertices.min(axis=0)
    v_max = vertices.max(axis=0)
    center = (v_min + v_max) * 0.5
    shifted = vertices - center
    half_extent = (v_max - v_min).max() * 0.5
    if half_extent == 0:
        raise ValueError("Mesh has zero size")
    return shifted / half_extent


def calculate_area_distortion(vertices: np.ndarray, faces: np.ndarray, uvs: np.ndarray) -> float:
    vertices = normalize_to_unit_box(vertices)
    total_3d_area = sum(calculate_3d_face_area(vertices, face) for face in faces)
    face_uvs = [uvs[face] for face in faces]
    total_uv_area = sum(calculate_uv_face_area(face_uv) for face_uv in face_uvs)
    total_ratio = total_uv_area / total_3d_area if total_3d_area > 0 else 1.0
    if total_ratio == 0:
        return 1.0

    distortions = []
    for face, face_uv in zip(faces, face_uvs):
        area_3d = calculate_3d_face_area(vertices, face)
        if area_3d <= 0:
            continue
        area_uv = calculate_uv_face_area(face_uv)
        distortion = (area_uv / area_3d) / total_ratio
        if distortion == 0 or math.isnan(distortion):
            continue
        distortions.append(distortion if distortion >= 1 else 1 / distortion)

    if not distortions:
        return 1.0
    return float(np.mean(np.clip(distortions, 0, 10)))


def calculate_conformal_metric(mesh: trimesh.Trimesh) -> float:
    uv = np.asarray(mesh.visual.uv, dtype=np.float64)
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    faces = np.asarray(mesh.faces, dtype=np.int64)
    values = []
    for f in faces:
        v0, v1, v2 = vertices[f[0]], vertices[f[1]], vertices[f[2]]
        u0, u1, u2 = uv[f[0]], uv[f[1]], uv[f[2]]
        t1_3d = v1 - v0
        t2_3d = v2 - v0
        t1_2d = u1 - u0
        t2_2d = u2 - u0

        def angle_cos(a: np.ndarray, b: np.ndarray) -> float:
            na = np.linalg.norm(a)
            nb = np.linalg.norm(b)
            if na < 1e-12 or nb < 1e-12:
                return 1.0
            return float(abs(np.dot(a, b)) / (na * nb))

        values.append(1.0 - abs(angle_cos(t1_3d, t2_3d) - angle_cos(t1_2d, t2_2d)))
    return float(np.mean(values)) if values else 1.0


def uv_seam_length(mesh: trimesh.Trimesh) -> float:
    uv = np.asarray(mesh.visual.uv, dtype=np.float64)
    faces = np.asarray(mesh.faces, dtype=np.int64)
    edges = np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]])).astype(np.int64)
    edges_sorted = np.sort(edges, axis=1)
    _, inv, counts = np.unique(edges_sorted, axis=0, return_inverse=True, return_counts=True)
    diff = uv[edges[:, 0]] - uv[edges[:, 1]]
    lengths = np.linalg.norm(diff, axis=1)
    seam_mask = counts[inv] == 1
    return float(lengths[seam_mask].sum())


def evaluate_uv_obj(obj_path: str) -> Dict[str, Any]:
    mesh = trimesh.load(obj_path, force="mesh")
    if mesh.visual is None or mesh.visual.uv is None:
        raise ValueError(f"No UV coordinates found in {obj_path}")

    uv_data = np.asarray(mesh.visual.uv, dtype=np.float64)
    uv_map: Dict[tuple[float, float], int] = {}
    vertex_to_uv_index = [None] * len(mesh.vertices)
    next_index = 0
    for vidx, uv in enumerate(uv_data):
        key = (float(uv[0]), float(uv[1]))
        if key not in uv_map:
            uv_map[key] = next_index
            next_index += 1
        vertex_to_uv_index[vidx] = uv_map[key]

    faces_uv_indices = []
    for face in mesh.faces:
        faces_uv_indices.append([vertex_to_uv_index[int(face[0])], vertex_to_uv_index[int(face[1])], vertex_to_uv_index[int(face[2])]])

    uf = UnionFind(len(faces_uv_indices))
    edge_map: Dict[tuple[int, int], int] = {}
    for face_idx, uv_inds in enumerate(faces_uv_indices):
        for i in range(3):
            a = uv_inds[i]
            b = uv_inds[(i + 1) % 3]
            if a > b:
                a, b = b, a
            edge = (a, b)
            if edge in edge_map:
                uf.union(face_idx, edge_map[edge])
            else:
                edge_map[edge] = face_idx

    roots = {uf.find(i) for i in range(len(faces_uv_indices))}
    charts = defaultdict(list)
    for face_idx in range(len(mesh.faces)):
        charts[uf.find(face_idx)].append(face_idx)

    chart_distortions = []
    for chart in charts.values():
        chart_distortions.append(calculate_area_distortion(mesh.vertices, mesh.faces[np.asarray(chart)], uv_data))

    return {
        "num_charts": float(len(roots)),
        "seam_length": uv_seam_length(mesh),
        "angular_distortion": calculate_conformal_metric(mesh),
        "area_distortion": float(max(chart_distortions) if chart_distortions else 1.0),
        "overall_area_distortion": calculate_area_distortion(mesh.vertices, mesh.faces, uv_data),
        "vertex_count": int(len(mesh.vertices)),
        "face_count": int(len(mesh.faces)),
    }
