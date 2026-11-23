#!/usr/bin/env python3
"""Run the released PartUV pipeline (same steps as method/official_pipeline.py) with
red-team knobs: PartField sampling seed, tree features (PartField vs face normals,
paper ablation Table 4b), config overrides (e.g. unwrap.method=lscm, Table 7) and the
distortion threshold tau. Outputs <output-dir>/<mesh>/final_components.obj like method.sh.
"""

from __future__ import annotations

import argparse
import json
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--meshes", nargs="+", required=True)
    p.add_argument("--data-dir", default="/home/user/data/downloads/common_shapes")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--checkpoint-path", default="/home/user/data/downloads/partfield/model_objaverse.ckpt")
    p.add_argument("--base-config", default="/home/user/method/official_partuv/config/config.yaml")
    p.add_argument("--threshold", type=float, default=1.25)
    p.add_argument("--seed", type=int, default=42, help="PartField point/face sampling seed (released default 42)")
    p.add_argument("--features", choices=["partfield", "normals"], default="partfield")
    p.add_argument("--set", action="append", default=[], help="config override section.key=value")
    return p.parse_args()


def build_config(base: str, overrides: list[str], out_path: Path) -> Path:
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
    return out_path


def install_seed(seed: int) -> None:
    original = PFInferenceModel.process_face

    def process_face_seeded(self, *args, **kwargs):
        kwargs["seed"] = seed
        return original(self, *args, **kwargs)

    PFInferenceModel.process_face = process_face_seeded


def install_normal_features(pf_model: PFInferenceModel) -> None:
    """Ablation (paper Table 4b / A2.1): build the part tree from face normals, not PartField features."""
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


def run_one(mesh_path: Path, out_root: Path, pf_model, config_path: Path, threshold: float, info: dict) -> dict:
    name = mesh_path.stem
    mesh_dir = out_root / name
    mesh_dir.mkdir(parents=True, exist_ok=True)
    timings: dict[str, float] = {}
    t = time.perf_counter()
    mesh = load_mesh_and_merge(str(mesh_path), epsilon=1e-7)
    mesh = fix_mesh_trimesh(mesh)
    processed = mesh_dir / f"{name}_processed.obj"
    mesh.export(processed)
    timings["prep_seconds"] = time.perf_counter() - t

    t = time.perf_counter()
    bin_path, _ = PF_pipeline(
        pf_model=pf_model,
        mesh_path=str(processed),
        mesh=mesh,
        output_path=str(mesh_dir / "bin"),
        save_binary=True,
        sample_on_faces=10,
        sample_batch_size=100_000,
    )
    timings["partfield_seconds"] = time.perf_counter() - t

    t = time.perf_counter()
    result = partuv.pipeline(
        tree_filename=str(bin_path),
        mesh_filename=str(processed),
        configPath=str(config_path),
        threshold=threshold,
    )
    final_parts, individual_parts = result[0], result[1]
    timings["unwrap_seconds"] = time.perf_counter() - t

    t = time.perf_counter()
    save_results(mesh_dir, final_parts, individual_parts)
    timings["save_results_seconds"] = time.perf_counter() - t
    timings["total_seconds"] = sum(timings.values())

    summary = {
        "mesh": name,
        "success": True,
        "num_components": int(final_parts.num_components),
        "distortion": float(final_parts.distortion),
        **info,
        **timings,
    }
    with open(mesh_dir / "run_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main() -> None:
    args = parse_args()
    out_root = Path(args.output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    config_path = build_config(args.base_config, args.set, out_root / "variant_config.yaml")
    info = {"seed": args.seed, "features": args.features, "threshold": args.threshold, "overrides": args.set}
    print(f"[variant] {info} config={config_path}", flush=True)

    install_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pf_model = PFInferenceModel(checkpoint_path=args.checkpoint_path, device=device)
    if args.features == "normals":
        install_normal_features(pf_model)

    summaries, failures = [], []
    for name in args.meshes:
        mesh_dir = out_root / name
        done = mesh_dir / "run_summary.json"
        if done.exists() and (mesh_dir / "final_components.obj").exists():
            print(f"[variant] skip {name} (done)", flush=True)
            continue
        try:
            print(f"[variant] {name}", flush=True)
            summaries.append(run_one(Path(args.data_dir) / f"{name}.obj", out_root, pf_model, config_path, args.threshold, info))
            print(f"[variant] {name} charts={summaries[-1]['num_components']} t={summaries[-1]['total_seconds']:.1f}s", flush=True)
        except Exception as exc:  # recorded, the evaluator counts the mesh as failed
            traceback.print_exc()
            failures.append({"mesh": name, "error": str(exc)})
            print(f"[variant] FAILED {name}: {exc}", file=sys.stderr, flush=True)

    with open(out_root / "variant_manifest.json", "w") as f:
        json.dump({"info": info, "results": summaries, "failures": failures}, f, indent=2)


if __name__ == "__main__":
    main()
