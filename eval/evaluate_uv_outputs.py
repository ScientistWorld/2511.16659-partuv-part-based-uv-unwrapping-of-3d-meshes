#!/usr/bin/env python3
"""Evaluate UV-mapped OBJ outputs without importing method code."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from eval.uv_obj_metrics import evaluate_uv_obj as evaluate_uv_mesh


@dataclass
class UVEvalResult:
    name: str
    success: bool
    metrics: dict | None = None
    error: str | None = None


def evaluate_uv_obj(name: str, obj_path: Path, runtime_seconds: float | None) -> UVEvalResult:
    try:
        metrics = evaluate_uv_mesh(str(obj_path))

        metrics = {
            "num_charts": float(metrics["num_charts"]),
            "seam_length": float(metrics["seam_length"]),
            "angular_distortion": float(metrics["angular_distortion"]),
            "area_distortion": float(metrics["area_distortion"]),
            "overall_area_distortion": float(metrics["overall_area_distortion"]),
            "time_seconds": float(runtime_seconds or 0.0),
        }
        return UVEvalResult(name=name, success=True, metrics=metrics)
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
            "angular_distortion": 0.0,
            "area_distortion": float("inf"),
            "overall_area_distortion": float("inf"),
            "avg_time": 0.0,
        }

    def arr(key: str) -> np.ndarray:
        return np.array([m[key] for m in success_metrics], dtype=np.float64)

    return {
        "success_rate": success_rate,
        "avg_charts": float(arr("num_charts").mean()),
        "median_charts": float(np.median(arr("num_charts"))),
        "seam_length": float(arr("seam_length").mean()),
        "angular_distortion": float(arr("angular_distortion").mean()),
        "area_distortion": float(arr("area_distortion").mean()),
        "overall_area_distortion": float(arr("overall_area_distortion").mean()),
        "avg_time": float(arr("time_seconds").mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate per-mesh UV OBJ outputs.")
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--uv-filename", required=True)
    parser.add_argument("--method-name", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    input_root = Path(args.input_root)
    mesh_dirs = sorted([p for p in input_root.iterdir() if p.is_dir()])
    results: list[UVEvalResult] = []

    for mesh_dir in mesh_dirs:
        uv_path = mesh_dir / args.uv_filename
        if not uv_path.exists():
            continue
        runtime = None
        summary_path = mesh_dir / "run_summary.json"
        if summary_path.exists():
            with open(summary_path) as f:
                summary = json.load(f)
            runtime = summary.get("runtime_seconds", summary.get("total_seconds"))
        results.append(evaluate_uv_obj(mesh_dir.name, uv_path, runtime))

    payload = {
        args.method_name: {
            **aggregate(results),
            "per_mesh": [
                {"name": r.name, "success": r.success, **(r.metrics or {}), **({"error": r.error} if r.error else {})}
                for r in results
            ],
        }
    }

    with open(args.output_json, "w") as f:
        json.dump(payload, f, indent=2)


if __name__ == "__main__":
    main()
