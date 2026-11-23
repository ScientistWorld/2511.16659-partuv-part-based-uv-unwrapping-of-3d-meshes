#!/usr/bin/env python3
"""Run the official PartUV pipeline on a folder of meshes.

For every ``<name>.obj`` in ``--data-dir`` this writes ``<output-dir>/<name>/uv.obj`` (the
un-packed UV chart layout produced by PartUV, identical to its ``final_components.obj``)
plus ``run_summary.json`` with PartUV's own chart count and distortion.

Default settings are the released pipeline (tau = 1.25, ABF++, PartField part tree, the
released PartField sampling seed). The optional knobs below reproduce the paper's
ablations and are used only for the gym's hardening study:
  --seed N            PartField point/face sampling seed (released default: 42)
  --features normals  build the part tree from face normals instead of PartField (Tab. 4b)
  --set k=v           config override, e.g. unwrap.method=lscm (Tab. 7), unwrap.agg_parts=20
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import torch
import yaml

import partuv
from partuv.preprocess_utils.partfield_official.run_PF import PFInferenceModel
from partuv.preprocess_utils.PartField_pipeline import PF_pipeline
from partuv.preprocess_utils.manifold import fix_mesh_trimesh
from partuv.preprocess_utils.merge_V_obj import load_mesh_and_merge
from partuv.preprocess import save_results


def build_config(base: str, overrides: list[str], out_path: Path) -> str:
    if not overrides:
        return base
    with open(base) as f:
        cfg = yaml.safe_load(f)
    for item in overrides:
        key, value = item.split("=", 1)
        node = cfg
        parts = key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = yaml.safe_load(value)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        yaml.safe_dump(cfg, f)
    return str(out_path)


def install_seed(seed: int) -> None:
    original = PFInferenceModel.process_face

    def process_face_seeded(self, *args, **kwargs):
        kwargs["seed"] = seed
        return original(self, *args, **kwargs)

    PFInferenceModel.process_face = process_face_seeded


def install_normal_features(pf_model: PFInferenceModel) -> None:
    """Paper ablation (Tab. 4b / A2.1): part tree from face normals instead of PartField features."""
    original = pf_model.model.run_inference

    def run_inference_normals(*args, **kwargs):
        feat, mesh, num_bridge = original(*args, **kwargs)
        normals = np.asarray(mesh.face_normals, dtype=np.float64).copy()
        bad = np.linalg.norm(normals, axis=1) < 1e-12
        normals[bad] = np.array([0.0, 0.0, 1.0])
        if normals.shape[0] != feat.shape[0]:
            raise RuntimeError(f"normal/feature row mismatch {normals.shape} vs {tuple(feat.shape)}")
        if torch.is_tensor(feat):
            return torch.as_tensor(normals, dtype=torch.float32, device=feat.device), mesh, num_bridge
        return normals.astype(np.float32), mesh, num_bridge

    pf_model.model.run_inference = run_inference_normals


def run_one_mesh(mesh_path: Path, output_dir: Path, pf_model: PFInferenceModel, config_path: str,
                 threshold: float, keep_intermediates: bool) -> dict:
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

    final_obj = mesh_dir / "final_components.obj"
    shutil.copyfile(final_obj, mesh_dir / "uv.obj")
    if not keep_intermediates:
        for extra in ("individual_parts", "bin"):
            shutil.rmtree(mesh_dir / extra, ignore_errors=True)
        for extra in (final_obj, processed_mesh):
            extra.unlink(missing_ok=True)

    summary = {
        "mesh": mesh_name,
        "success": True,
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
    parser.add_argument("--meshes", nargs="*", default=None, help="Optional subset of mesh stems.")
    parser.add_argument("--seed", type=int, default=None, help="PartField sampling seed (default: released 42).")
    parser.add_argument("--features", choices=["partfield", "normals"], default="partfield")
    parser.add_argument("--set", action="append", default=[], help="config override section.key=value")
    parser.add_argument("--keep-intermediates", action="store_true")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mesh_paths = sorted(data_dir.glob("*.obj"))
    if args.meshes:
        wanted = set(args.meshes)
        mesh_paths = [p for p in mesh_paths if p.stem in wanted]
    if args.limit > 0:
        mesh_paths = mesh_paths[:args.limit]
    if not mesh_paths:
        raise SystemExit(f"No OBJ meshes found in {data_dir}")

    config_path = build_config(args.config_path, args.set, output_dir / "_config" / "config.yaml")
    if args.seed is not None:
        install_seed(args.seed)
    # PartField runs on the CPU by default so that results do not depend on the node's GPU.
    device = os.environ.get("PARTUV_DEVICE", "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"
    pf_model = PFInferenceModel(checkpoint_path=args.checkpoint_path, device=device)
    if args.features == "normals":
        install_normal_features(pf_model)
    print(f"[PartUV] device={device} seed={args.seed} features={args.features} tau={args.threshold} "
          f"overrides={args.set} meshes={len(mesh_paths)}", flush=True)

    results = []
    failures = []
    for mesh_path in mesh_paths:
        try:
            print(f"[PartUV] {mesh_path.name}", flush=True)
            results.append(run_one_mesh(mesh_path, output_dir, pf_model, config_path, args.threshold,
                                        args.keep_intermediates))
            print(f"[PartUV] {mesh_path.stem}: charts={results[-1]['num_components']} "
                  f"t={results[-1]['total_seconds']:.1f}s", flush=True)
        except Exception as exc:  # pragma: no cover - captured in job logs
            traceback.print_exc()
            failures.append({"mesh": mesh_path.stem, "success": False, "error": str(exc)})
            print(f"[PartUV] FAILED {mesh_path.name}: {exc}", file=sys.stderr, flush=True)

    with open(output_dir / "run_manifest.json", "w") as f:
        json.dump({"results": results, "failures": failures}, f, indent=2)

    if failures:
        raise SystemExit(f"PartUV failed on {len(failures)} meshes")


if __name__ == "__main__":
    main()
