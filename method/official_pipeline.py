#!/usr/bin/env python3
"""Run the official PartUV pipeline on a mesh folder."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

import partuv
from partuv.preprocess_utils.partfield_official.run_PF import PFInferenceModel
from partuv.preprocess_utils.PartField_pipeline import PF_pipeline
from partuv.preprocess_utils.manifold import fix_mesh_trimesh
from partuv.preprocess_utils.merge_V_obj import load_mesh_and_merge
from partuv.preprocess import save_results


def run_one_mesh(mesh_path: Path, output_dir: Path, pf_model: PFInferenceModel, config_path: str, threshold: float) -> dict:
    mesh_name = mesh_path.stem
    mesh_dir = output_dir / mesh_name
    mesh_dir.mkdir(parents=True, exist_ok=True)

    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    mesh = load_mesh_and_merge(str(mesh_path), epsilon=1e-7)
    timings["load_seconds"] = time.perf_counter() - t0

    t1 = time.perf_counter()
    mesh = fix_mesh_trimesh(mesh)
    timings["repair_seconds"] = time.perf_counter() - t1

    processed_mesh = mesh_dir / f"{mesh_name}_processed.obj"
    t2 = time.perf_counter()
    mesh.export(processed_mesh)
    timings["export_seconds"] = time.perf_counter() - t2

    t3 = time.perf_counter()
    bin_path, _ = PF_pipeline(
        pf_model=pf_model,
        mesh_path=str(processed_mesh),
        mesh=mesh,
        output_path=str(mesh_dir / "bin"),
        save_binary=True,
        sample_on_faces=10,
        sample_batch_size=100_000,
    )
    timings["partfield_seconds"] = time.perf_counter() - t3

    t4 = time.perf_counter()
    # Use file-based pipeline (avoids CUDA/stream issues with numpy arrays on CPU)
    result = partuv.pipeline(
        tree_filename=str(bin_path),
        mesh_filename=str(processed_mesh),
        configPath=config_path,
        threshold=threshold,
    )
    final_parts, individual_parts = result[0], result[1]
    timings["unwrap_seconds"] = time.perf_counter() - t4

    t5 = time.perf_counter()
    save_results(mesh_dir, final_parts, individual_parts)
    timings["save_results_seconds"] = time.perf_counter() - t5
    timings["total_seconds"] = sum(timings.values())

    summary = {
        "mesh": mesh_name,
        "success": True,
        "tree_bin": str(bin_path),
        "num_components": int(final_parts.num_components),
        "distortion": float(final_parts.distortion),
        **timings,
    }
    with open(mesh_dir / "run_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run official PartUV on a dataset folder.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--checkpoint-path", required=True)
    parser.add_argument("--config-path", default="/home/user/method/official_partuv/config/config.yaml")
    parser.add_argument("--threshold", type=float, default=1.25)
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on number of meshes.")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mesh_paths = sorted(data_dir.glob("*.obj"))
    if args.limit > 0:
        mesh_paths = mesh_paths[:args.limit]
    if not mesh_paths:
        raise SystemExit(f"No OBJ meshes found in {data_dir}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pf_model = PFInferenceModel(checkpoint_path=args.checkpoint_path, device=device)

    results = []
    failures = []
    for mesh_path in mesh_paths:
        try:
            print(f"[PartUV] {mesh_path.name}", flush=True)
            results.append(run_one_mesh(mesh_path, output_dir, pf_model, args.config_path, args.threshold))
        except Exception as exc:  # pragma: no cover - captured in job logs
            failures.append({"mesh": mesh_path.stem, "success": False, "error": str(exc)})
            print(f"[PartUV] FAILED {mesh_path.name}: {exc}", file=sys.stderr, flush=True)

    with open(output_dir / "run_manifest.json", "w") as f:
        json.dump({"results": results, "failures": failures}, f, indent=2)

    if failures:
        raise SystemExit(f"PartUV failed on {len(failures)} meshes")


if __name__ == "__main__":
    main()