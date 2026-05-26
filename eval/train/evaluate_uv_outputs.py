#!/usr/bin/env python3
"""Evaluate the visible Common Shapes train slice from UV OBJ artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from eval.uv_obj_metrics import evaluate_uv_obj as evaluate_uv_mesh


SLICE = "train"
EXPERIMENT = "common_shapes_comparison"
MESH_NAMES = (
    "alligator",
    "beast",
    "beetle",
    "cheburashka",
    "fandisk",
    "homer",
    "igea",
    "max-planck",
    "ogre",
    "spot",
    "suzanne",
    "woody",
)
SCORED_KEYS = {
    "success_rate",
    "avg_charts",
    "median_charts",
    "angular_distortion",
    "p05_angular_distortion",
    "area_distortion",
    "p95_area_distortion",
}
CANDIDATE_UV_FILENAMES = (
    "final_components.obj",
    "xatlas.obj",
    "uv.obj",
    "output.obj",
    "result.obj",
    "final.obj",
)


@dataclass
class UVEvalResult:
    name: str
    success: bool
    metrics: dict | None = None
    error: str | None = None


def evaluate_uv_obj(name: str, obj_path: Path, runtime_seconds: float | None) -> UVEvalResult:
    try:
        metrics = evaluate_uv_mesh(str(obj_path))
        return UVEvalResult(
            name=name,
            success=True,
            metrics={
                "num_charts": float(metrics["num_charts"]),
                "seam_length": float(metrics["seam_length"]),
                "angular_distortion": float(metrics["angular_distortion"]),
                "area_distortion": float(metrics["area_distortion"]),
                "overall_area_distortion": float(metrics["overall_area_distortion"]),
                "time_seconds": float(runtime_seconds or 0.0),
            },
        )
    except Exception as exc:  # pragma: no cover - driven by job runtime
        return UVEvalResult(name=name, success=False, error=str(exc))


def aggregate(results: list[UVEvalResult]) -> dict:
    success_metrics = [r.metrics for r in results if r.success and r.metrics]
    success_rate = 100.0 * len(success_metrics) / max(1, len(results))
    if not success_metrics:
        return {
            "success_rate": success_rate,
            "avg_charts": float("inf"),
            "median_charts": float("inf"),
            "seam_length": float("inf"),
            "angular_distortion": 0.0,
            "p05_angular_distortion": 0.0,
            "area_distortion": float("inf"),
            "p95_area_distortion": float("inf"),
            "overall_area_distortion": float("inf"),
            "avg_time": 0.0,
        }

    def arr(key: str) -> np.ndarray:
        return np.array([m[key] for m in success_metrics], dtype=np.float64)

    return {
        "success_rate": success_rate,
        "avg_charts": float(arr("num_charts").mean()),
        "median_charts": float(np.median(arr("num_charts"))),
        "seam_length": float(np.median(arr("seam_length"))),
        "angular_distortion": float(arr("angular_distortion").mean()),
        "p05_angular_distortion": float(np.percentile(arr("angular_distortion"), 5)),
        "area_distortion": float(arr("area_distortion").mean()),
        "p95_area_distortion": float(np.percentile(arr("area_distortion"), 95)),
        "overall_area_distortion": float(arr("overall_area_distortion").mean()),
        "avg_time": float(arr("time_seconds").mean()),
    }


def evaluate_method(method_name: str, input_root: Path, uv_filename: str) -> dict:
    results: list[UVEvalResult] = []
    for mesh_name in MESH_NAMES:
        mesh_dir = input_root / mesh_name
        uv_path = mesh_dir / uv_filename
        if not uv_path.exists():
            results.append(UVEvalResult(name=mesh_name, success=False, error=f"Missing {uv_filename}"))
            continue

        runtime = None
        summary_path = mesh_dir / "run_summary.json"
        if summary_path.exists():
            with open(summary_path) as f:
                summary = json.load(f)
            runtime = summary.get("runtime_seconds", summary.get("total_seconds"))
        results.append(evaluate_uv_obj(mesh_name, uv_path, runtime))

    return {
        method_name: {
            **aggregate(results),
            "slice": SLICE,
            "input_root": str(input_root),
            "uv_filename": uv_filename,
            "expected_meshes": list(MESH_NAMES),
            "per_mesh": [
                {"name": r.name, "success": r.success, **(r.metrics or {}), **({"error": r.error} if r.error else {})}
                for r in results
            ],
        }
    }


def load_method_name(result_json: Path, fallback: str) -> str:
    if not result_json.exists():
        return fallback
    try:
        with open(result_json) as f:
            payload = json.load(f)
    except json.JSONDecodeError:
        return fallback
    names = [name for name, value in payload.items() if isinstance(value, dict)]
    return names[0] if len(names) == 1 else fallback


def infer_uv_filename(input_root: Path) -> str | None:
    counts: dict[str, int] = {}
    for candidate in CANDIDATE_UV_FILENAMES:
        counts[candidate] = sum(1 for mesh_name in MESH_NAMES if (input_root / mesh_name / candidate).exists())
    best_name, best_count = max(counts.items(), key=lambda item: item[1])
    return best_name if best_count > 0 else None


def discover_methods(checkpoints_root: Path) -> list[tuple[str, Path, str]]:
    discovered = []
    for input_root in sorted(p for p in checkpoints_root.iterdir() if p.is_dir()):
        uv_filename = infer_uv_filename(input_root)
        if uv_filename is None:
            continue
        fallback_name = input_root.name.removesuffix("_repro")
        method_name = load_method_name(input_root / "results.json", fallback_name)
        discovered.append((method_name, input_root, uv_filename))
    return discovered


def write_single(method_name: str, input_root: Path, uv_filename: str, output_json: Path) -> None:
    payload = evaluate_method(method_name, input_root, uv_filename)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w") as f:
        json.dump(payload, f, indent=2)


def load_result_payloads(paths: list[Path]) -> dict:
    merged: dict = {}
    for path in paths:
        with open(path) as f:
            payload = json.load(f)
        for method_name, result in payload.items():
            if isinstance(result, dict):
                merged[method_name] = result
    return merged


def write_scores(results: dict, output_json: Path, manifest_json: Path | None) -> None:
    scores = {"experiments": {EXPERIMENT: {"results": {}}}}
    manifest = {"slice": SLICE, "methods": {}}
    for method_name, result in sorted(results.items()):
        scores["experiments"][EXPERIMENT]["results"][method_name] = {
            key: value for key, value in result.items() if key in SCORED_KEYS
        }
        if "input_root" in result and "uv_filename" in result:
            manifest["methods"][method_name] = {
                "input_root": result["input_root"],
                "uv_filename": result["uv_filename"],
                "slice": SLICE,
            }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w") as f:
        json.dump(scores, f, indent=2)

    if manifest_json is not None:
        manifest_json.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_json, "w") as f:
            json.dump(manifest, f, indent=2)


def command_single(args: argparse.Namespace) -> None:
    write_single(args.method_name, Path(args.input_root), args.uv_filename, Path(args.output_json))


def command_compare(args: argparse.Namespace) -> None:
    results = load_result_payloads([Path(args.baseline_json), Path(args.method_json)])
    write_scores(results, Path(args.output_json), Path(args.manifest_json))


def command_discover(args: argparse.Namespace) -> None:
    results = {}
    result_paths = []
    for method_name, input_root, uv_filename in discover_methods(Path(args.checkpoints_root)):
        result_path = input_root / "results_train.json"
        write_single(method_name, input_root, uv_filename, result_path)
        result_paths.append(result_path)
    if not result_paths:
        raise SystemExit(f"No UV output roots discovered under {args.checkpoints_root}")
    results = load_result_payloads(result_paths)
    write_scores(results, Path(args.output_json), Path(args.manifest_json))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    single = subparsers.add_parser("single")
    single.add_argument("--method-name", required=True)
    single.add_argument("--input-root", required=True)
    single.add_argument("--uv-filename", required=True)
    single.add_argument("--output-json", required=True)
    single.set_defaults(func=command_single)

    compare = subparsers.add_parser("compare")
    compare.add_argument("--baseline-json", required=True)
    compare.add_argument("--method-json", required=True)
    compare.add_argument("--output-json", required=True)
    compare.add_argument("--manifest-json", required=True)
    compare.set_defaults(func=command_compare)

    discover = subparsers.add_parser("discover")
    discover.add_argument("--checkpoints-root", required=True)
    discover.add_argument("--output-json", required=True)
    discover.add_argument("--manifest-json", required=True)
    discover.set_defaults(func=command_discover)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
