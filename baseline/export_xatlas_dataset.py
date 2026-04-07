#!/usr/bin/env python3
"""Export xatlas UVs for a dataset as OBJ files."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import xatlas

from data.mesh_loader import load_obj_mesh


def compute_vertex_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    face_normals = np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]], vertices[faces[:, 2]] - vertices[faces[:, 0]])
    vertex_normals = np.zeros_like(vertices)
    for fi, face in enumerate(faces):
        vertex_normals[face] += face_normals[fi]
    norms = np.linalg.norm(vertex_normals, axis=1, keepdims=True)
    norms[norms < 1e-12] = 1.0
    return vertex_normals / norms


def write_uv_obj(path: Path, vertices: np.ndarray, faces: np.ndarray, uvs: np.ndarray) -> None:
    with open(path, "w") as f:
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        for uv in uvs:
            f.write(f"vt {uv[0]} {uv[1]}\n")
        for tri in faces:
            a, b, c = tri + 1
            f.write(f"f {a}/{a} {b}/{b} {c}/{c}\n")


def run_one(mesh_path: Path, output_dir: Path) -> dict:
    vertices, faces = load_obj_mesh(str(mesh_path))
    normals = compute_vertex_normals(vertices, faces).astype(np.float32)

    start = time.perf_counter()
    vmapping, atlas_faces, atlas_uvs = xatlas.parametrize(
        vertices.astype(np.float32),
        faces.astype(np.uint32),
        normals,
    )
    elapsed = time.perf_counter() - start

    atlas_vertices = vertices[np.asarray(vmapping, dtype=np.int64)]
    atlas_faces = np.asarray(atlas_faces, dtype=np.int64)
    atlas_uvs = np.asarray(atlas_uvs, dtype=np.float64)

    mesh_dir = output_dir / mesh_path.stem
    mesh_dir.mkdir(parents=True, exist_ok=True)
    write_uv_obj(mesh_dir / "xatlas.obj", atlas_vertices, atlas_faces, atlas_uvs)

    summary = {"mesh": mesh_path.stem, "success": True, "runtime_seconds": elapsed}
    with open(mesh_dir / "run_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run xatlas baseline on a dataset.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mesh_paths = sorted(data_dir.glob("*.obj"))
    if args.limit > 0:
        mesh_paths = mesh_paths[:args.limit]
    if not mesh_paths:
        raise SystemExit(f"No OBJ meshes found in {data_dir}")

    results = [run_one(mesh_path, output_dir) for mesh_path in mesh_paths]
    with open(output_dir / "run_manifest.json", "w") as f:
        json.dump({"results": results, "failures": []}, f, indent=2)


if __name__ == "__main__":
    main()
