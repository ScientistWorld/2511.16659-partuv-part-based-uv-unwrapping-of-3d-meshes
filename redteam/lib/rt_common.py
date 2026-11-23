"""Shared helpers for the red-team shortcut generators.

Only uses what a future agent has: the downloaded meshes, its own method outputs and
public libraries. Nothing here is imported by eval/.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

DATA_DIR = Path("/home/user/data/downloads/common_shapes")
REF_OUT = Path("/home/user/checkpoints/partuv_repro")
MATERIAL_DIR = REF_OUT / "teapot"
UV_NAME = "final_components.obj"


def env_meshes() -> list[str]:
    return os.environ["RUN_MESHES"].split()


def load_uv_obj(path: Path):
    """Load an OBJ exactly the way eval/uv_obj_metrics.py does."""
    mesh = trimesh.load(str(path), force="mesh")
    V = np.asarray(mesh.vertices, dtype=np.float64)
    F = np.asarray(mesh.faces, dtype=np.int64)
    UV = np.asarray(mesh.visual.uv, dtype=np.float64)
    return V, F, UV


def load_input_mesh(name: str):
    """The input mesh with vertices merged by position only (true 3-D connectivity)."""
    raw = trimesh.load(str(DATA_DIR / f"{name}.obj"), force="mesh")
    mesh = trimesh.Trimesh(np.asarray(raw.vertices, dtype=np.float64), np.asarray(raw.faces, dtype=np.int64), process=True)
    return mesh


def chart_labels(F: np.ndarray, UV: np.ndarray) -> np.ndarray:
    """Chart id per face with the evaluator's rule: vertices are identified by exact UV
    coordinate and faces are joined when they share a UV edge."""
    _, uv_id = np.unique(UV, axis=0, return_inverse=True)
    uv_id = np.asarray(uv_id).reshape(-1)
    fu = uv_id[F]
    edges = np.concatenate([fu[:, [0, 1]], fu[:, [1, 2]], fu[:, [2, 0]]])
    edges.sort(axis=1)
    _, eid = np.unique(edges, axis=0, return_inverse=True)
    eid = np.asarray(eid).reshape(-1)
    n_f = len(F)
    n_e = int(eid.max()) + 1
    rows = np.tile(np.arange(n_f), 3)
    cols = n_f + eid
    graph = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_f + n_e, n_f + n_e))
    _, lab = connected_components(graph, directed=False)
    _, lab = np.unique(lab[:n_f], return_inverse=True)
    return np.asarray(lab).reshape(-1)


def write_uv_obj(mesh_dir: Path, V: np.ndarray, F: np.ndarray, UV: np.ndarray) -> Path:
    """Write a UV OBJ in the same layout as the reference export (v index == vt index),
    with full float precision."""
    mesh_dir.mkdir(parents=True, exist_ok=True)
    path = mesh_dir / UV_NAME
    idx = np.asarray(F, dtype=np.int64) + 1
    with open(path, "w") as f:
        f.write("mtllib material.mtl\nusemtl material_0\n")
        np.savetxt(f, np.asarray(V, dtype=np.float64), fmt="v %.17g %.17g %.17g")
        np.savetxt(f, np.asarray(UV, dtype=np.float64), fmt="vt %.17g %.17g")
        np.savetxt(f, np.column_stack([idx[:, 0], idx[:, 0], idx[:, 1], idx[:, 1], idx[:, 2], idx[:, 2]]),
                   fmt="f %d/%d %d/%d %d/%d")
    for extra in ("material.mtl", "material_0.png"):
        src = MATERIAL_DIR / extra
        if src.exists():
            shutil.copyfile(src, mesh_dir / extra)
    return path


def compact(V: np.ndarray, F: np.ndarray, UV: np.ndarray):
    used, inv = np.unique(F.reshape(-1), return_inverse=True)
    return V[used], np.asarray(inv).reshape(F.shape), UV[used]


def face_areas_3d(V: np.ndarray, F: np.ndarray) -> np.ndarray:
    return 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)


def face_areas_uv(UV: np.ndarray, F: np.ndarray) -> np.ndarray:
    a = UV[F[:, 1]] - UV[F[:, 0]]
    b = UV[F[:, 2]] - UV[F[:, 0]]
    return 0.5 * np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])
