#!/usr/bin/env python3
"""Main pipeline for PartUV evaluation.

Runs the full evaluation on the Common Shapes dataset.
"""

import os
import sys
import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.mesh_loader import load_all_common_shapes, Mesh
from method.partuv import PartUV
from baseline.xatlas_baseline import unwrap_xatlas
from eval.metrics import evaluate_uv_mapping, aggregate_metrics


def run_partuv(mesh: Mesh, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run PartUV on a mesh."""
    params = params or {}
    tau = params.get('distortion_threshold', 1.25)

    partuv = PartUV(
        distortion_threshold=tau,
        use_merge_heuristic=params.get('use_merge', True),
        max_candidates=params.get('max_candidates', 10),
        max_depth=params.get('max_depth', 15),
        n_threads=params.get('n_threads', 1)
    )

    chart_set = partuv.unwrap(mesh)

    # Build chart IDs for each face
    chart_ids = np.zeros(mesh.n_faces, dtype=np.int32)
    uv_coords = np.zeros((mesh.n_vertices, 2))

    # Combine UVs from all charts (scale to avoid overlap)
    scale = 1.0 / np.sqrt(max(1, chart_set.chart_count))
    for cid, chart in enumerate(chart_set.charts):
        for fi in chart.face_indices:
            chart_ids[fi] = cid

        # Scale and offset UVs
        offset_x = (cid % 8) * scale
        offset_y = (cid // 8) * scale
        for vi in chart.vertex_indices:
            uv_coords[vi] = chart.uv_coords[vi] * scale + np.array([offset_x, offset_y])

    return {
        'uv_coords': uv_coords,
        'chart_ids': chart_ids,
        'num_charts': chart_set.chart_count,
        'max_distortion': chart_set.max_distortion,
    }


def run_xatlas(mesh: Mesh, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run xatlas on a mesh."""
    params = params or {}
    result = unwrap_xatlas(mesh, params)
    return result


def evaluate_dataset(method_name: str, meshes: List[Mesh],
                    method_fn, params: Dict[str, Any] = None,
                    output_dir: str = None) -> Dict[str, Any]:
    """Evaluate a method on the dataset.

    Args:
        method_name: Name of the method
        meshes: List of meshes
        method_fn: Function that takes a mesh and returns UV mapping
        params: Method parameters
        output_dir: Directory to save per-mesh results

    Returns:
        Aggregated metrics and per-mesh results
    """
    params = params or {}
    all_metrics = []
    per_mesh_results = []
    success_count = 0
    total_time = 0.0

    for i, mesh in enumerate(meshes):
        print(f"  [{i+1}/{len(meshes)}] Processing {mesh.name}...", flush=True)
        start_time = time.time()

        try:
            result = method_fn(mesh, params)
            elapsed = time.time() - start_time

            if result is None:
                print(f"    FAILED: {mesh.name}")
                all_metrics.append({
                    'num_charts': float('inf'),
                    'seam_length': float('inf'),
                    'angular_distortion': 0.0,
                    'area_distortion': float('inf'),
                    'overall_area_distortion': float('inf'),
                })
                per_mesh_results.append({'name': mesh.name, 'success': False})
                continue

            # Evaluate
            metrics = evaluate_uv_mapping(mesh, result['uv_coords'], result['chart_ids'])
            metrics['time_seconds'] = elapsed
            all_metrics.append(metrics)
            success_count += 1
            total_time += elapsed

            print(f"    Charts: {metrics['num_charts']:.0f}, "
                  f"Angular: {metrics['angular_distortion']:.4f}, "
                  f"Area Dist: {metrics['area_distortion']:.3f}, "
                  f"Time: {elapsed:.1f}s", flush=True)

            per_mesh_results.append({
                'name': mesh.name,
                'success': True,
                **metrics
            })

            # Save per-mesh result
            if output_dir:
                mesh_dir = os.path.join(output_dir, mesh.name)
                os.makedirs(mesh_dir, exist_ok=True)
                # Save UV coords and chart IDs
                np.save(os.path.join(mesh_dir, 'uv_coords.npy'), result['uv_coords'])
                np.save(os.path.join(mesh_dir, 'chart_ids.npy'), result['chart_ids'])
                with open(os.path.join(mesh_dir, 'metrics.json'), 'w') as f:
                    json.dump(metrics, f, indent=2)

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"    ERROR on {mesh.name}: {e}", flush=True)
            all_metrics.append({
                'num_charts': float('inf'),
                'seam_length': float('inf'),
                'angular_distortion': 0.0,
                'area_distortion': float('inf'),
                'overall_area_distortion': float('inf'),
            })
            per_mesh_results.append({'name': mesh.name, 'success': False, 'error': str(e)})

    # Aggregate
    success_rate = (success_count / len(meshes)) * 100.0 if meshes else 0.0
    agg = aggregate_metrics(all_metrics)
    agg['success_rate'] = success_rate
    agg['avg_time'] = total_time / max(1, success_count)

    return {
        'method': method_name,
        'success_rate': success_rate,
        **agg,
        'per_mesh': per_mesh_results,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='PartUV Evaluation Pipeline')
    parser.add_argument('--data-dir', type=str,
                        default='/home/user/data/common_shapes',
                        help='Directory containing mesh files')
    parser.add_argument('--output-dir', type=str,
                        default='/home/user/checkpoints',
                        help='Output directory for results')
    parser.add_argument('--method', type=str, default='partuv',
                        choices=['partuv', 'xatlas', 'both'],
                        help='Method to evaluate')
    parser.add_argument('--distortion-threshold', type=float, default=1.25,
                        help='Distortion threshold tau')
    parser.add_argument('--use-merge', action='store_true', default=False,
                        help='Use Merge heuristic')
    parser.add_argument('--max-candidates', type=int, default=10,
                        help='Max chart candidates from Normal heuristic')
    parser.add_argument('--n-threads', type=int, default=1,
                        help='Number of threads')
    parser.add_argument('--name', type=str, default='run1',
                        help='Name for this run')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load dataset
    print(f"\n=== Loading meshes from {args.data_dir} ===")
    meshes = load_all_common_shapes(args.data_dir)
    print(f"Loaded {len(meshes)} meshes\n")

    if not meshes:
        print("ERROR: No meshes found. Please run the download script first.")
        sys.exit(1)

    results = {}

    if args.method in ('partuv', 'both'):
        print(f"\n=== Running PartUV (tau={args.distortion_threshold}) ===")
        params = {
            'distortion_threshold': args.distortion_threshold,
            'use_merge': args.use_merge,
            'max_candidates': args.max_candidates,
            'n_threads': args.n_threads,
        }
        run_dir = os.path.join(args.output_dir, f'partuv_{args.name}')
        result = evaluate_dataset('partuv', meshes, run_partuv, params, run_dir)
        results['partuv'] = result

        print(f"\nPartUV Results:")
        print(f"  Avg Charts: {result['avg_charts']:.1f}")
        print(f"  Median Charts: {result['median_charts']:.1f}")
        print(f"  Angular Dist: {result['angular_distortion']:.4f}")
        print(f"  Area Dist: {result['area_distortion']:.3f}")
        print(f"  Success Rate: {result['success_rate']:.1f}%")
        print(f"  Avg Time: {result['avg_time']:.1f}s")

    if args.method in ('xatlas', 'both'):
        print(f"\n=== Running xatlas baseline ===")
        params = {}
        run_dir = os.path.join(args.output_dir, f'xatlas_{args.name}')
        result = evaluate_dataset('xatlas', meshes, run_xatlas, params, run_dir)
        results['xatlas'] = result

        print(f"\nxatlas Results:")
        print(f"  Avg Charts: {result['avg_charts']:.1f}")
        print(f"  Median Charts: {result['median_charts']:.1f}")
        print(f"  Angular Dist: {result['angular_distortion']:.4f}")
        print(f"  Area Dist: {result['area_distortion']:.3f}")
        print(f"  Success Rate: {result['success_rate']:.1f}%")
        print(f"  Avg Time: {result['avg_time']:.1f}s")

    # Save results
    results_path = os.path.join(args.output_dir, f'results_{args.name}.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")

    return results


if __name__ == '__main__':
    main()
