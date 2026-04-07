#!/usr/bin/env python3
"""Run the published PartUV method on one or more meshes."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import partuv
import torch
from partuv.preprocess import preprocess, save_results
from partuv.preprocess_utils.partfield_official.run_PF import PFInferenceModel

from eval.uv_obj_metrics import evaluate_uv_obj


def discover_meshes(data_dir: Path, mesh_name: str | None) -> list[Path]:
    meshes = sorted(p for p in data_dir.iterdir() if p.suffix.lower() == ".obj")
    if mesh_name:
        meshes = [p for p in meshes if p.stem == mesh_name or p.name == mesh_name]
    return meshes


def run_single_mesh(mesh_path: Path, output_root: Path, pf_model: PFInferenceModel, threshold: float) -> dict:
    mesh_dir = output_root / mesh_path.stem
    mesh_dir.mkdir(parents=True, exist_ok=True)

    timings = {}
    start = time.time()
    mesh, _, tree_dict, preprocess_times = preprocess(
        str(mesh_path),
        pf_model=pf_model,
        output_path=str(mesh_dir / "preprocess"),
        save_tree_file=False,
        save_processed_mesh=False,
        sample_on_faces=10,
        sample_batch_size=100_000,
        merge_vertices_epsilon=1e-7,
    )
    timings.update(preprocess_times)
    timings["preprocess_total"] = time.time() - start

    start = time.time()
    final_parts, individual_parts = partuv.pipeline_numpy(
        V=mesh.vertices,
        F=mesh.faces,
        tree_dict=tree_dict,
        configPath="",
        threshold=threshold,
        pack_final_mesh=False,
    )
    timings["pipeline"] = time.time() - start

    start = time.time()
    save_results(mesh_dir, final_parts, individual_parts)
    timings["save_results"] = time.time() - start

    obj_path = mesh_dir / "final_components.obj"
    metrics = evaluate_uv_obj(str(obj_path))
    metrics["time_seconds"] = float(sum(v for v in timings.values() if isinstance(v, (float, int))))

    summary = {
        "mesh": mesh_path.stem,
        "output_obj": str(obj_path),
        "metrics": metrics,
        "timings": timings,
    }
    with open(mesh_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run official PartUV")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--mesh-name", type=str, default=None)
    parser.add_argument("--threshold", type=float, default=1.25)
    args = parser.parse_args()

    os.environ.setdefault("OMP_NUM_THREADS", "8")
    os.environ.setdefault("MKL_NUM_THREADS", "8")

    meshes = discover_meshes(args.data_dir, args.mesh_name)
    if not meshes:
        raise SystemExit(f"No meshes found in {args.data_dir} for mesh_name={args.mesh_name!r}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pf_model = PFInferenceModel(checkpoint_path=str(args.checkpoint), device=device)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = {"method": "partuv_official", "meshes": []}
    for mesh_path in meshes:
        print(f"Running PartUV on {mesh_path.name}")
        results["meshes"].append(run_single_mesh(mesh_path, args.output_dir, pf_model, args.threshold))

    with open(args.output_dir / "summary.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
