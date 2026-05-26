#!/usr/bin/env python3
"""Legacy prototype evaluation pipeline.

This module predates the official PartUV package integration and uses the
simplified `method.partuv` prototype. It is not used by the reproduction
scripts or by the claimed milestone. The actual method entry point is
`method/official_pipeline.py`.
"""

import os
import sys
import json
import time
import signal
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
    tau = params.get('distortion_threshold', 1.5)

    partuv = PartUV(
        distortion_threshold=tau,
        use_merge_heuristic=params.get('use_merge', False),
        max_candidates=params.get('max_candidates', 3),
        max_depth=params.get('max_depth', 8),
        n_threads=params.get('n_threads', 1)
    )

    chart_set = partuv.unwrap(mesh)

    # Build chart IDs for each face
    chart_ids = np.zeros(mesh.n_faces, dtype=np.int32)
    uv_coords = np.zeros((mesh.n_vertices, 2))

    # Store raw (unpacked) UVs per chart for area distortion computation
    raw_chart_uvs = {}
    raw_chart_faces = {}

    # Combine UVs from all charts (scale to avoid overlap)
    scale = 1.0 / np.sqrt(max(1, chart_set.chart_count))
    for cid, chart in enumerate(chart_set.charts):
        for fi in chart.face_indices:
            chart_ids[fi] = cid

        # Store raw UVs for distortion computation
        raw_chart_uvs[cid] = chart.uv_coords.copy()
        raw_chart_faces[cid] = chart.face_indices.copy()

        # Scale and offset UVs for the packed output
        offset_x = (cid % 8) * scale
        offset_y = (cid // 8) * scale
        for vi in chart.vertex_indices:
            uv_coords[vi] = chart.uv_coords[vi] * scale + np.array([offset_x, offset_y])

    return {
        'uv_coords': uv_coords,
        'chart_ids': chart_ids,
        'num_charts': chart_set.chart_count,
        'max_distortion': chart_set.max_distortion,
        'raw_chart_uvs': raw_chart_uvs,
        'raw_chart_faces': raw_chart_faces,
    }


def run_xatlas(mesh: Mesh, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run xatlas on a mesh."""
    params = params or {}
    result = unwrap_xatlas(mesh, params)
    return result


class TimeoutException(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutException()

def _run_with_timeout(method_fn, mesh, params, timeout_seconds):
    """Run a method with a timeout using SIGALRM."""
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(int(timeout_seconds))
    try:
        result = method_fn(mesh, params)
        signal.alarm(0)
        return result, None
    except TimeoutException:
        signal.alarm(0)
        return None, 'timeout'
    except Exception as e:
        signal.alarm(0)
        return None, str(e)
    finally:
        signal.signal(signal.SIGALRM, old_handler)


def evaluate_dataset(method_name: str, meshes: List[Mesh],
                    method_fn, params: Dict[str, Any] = None,
                    output_dir: str = None,
                    mesh_timeout: int = 300) -> Dict[str, Any]:
    """Evaluate a method on the dataset."""
    params = params or {}
    all_metrics = []
    per_mesh_results = []
    success_count = 0
    total_time = 0.0

    for i, mesh in enumerate(meshes):
        print(f"  [{i+1}/{len(meshes)}] Processing {mesh.name}...", flush=True)

        # Determine timeout based on mesh size
        timeout = mesh_timeout
        if mesh.n_faces < 2000:
            timeout = 120
        elif mesh.n_faces < 5000:
            timeout = 300
        elif mesh.n_faces < 10000:
            timeout = 600

        start_time = time.time()
        result, error = _run_with_timeout(method_fn, mesh, params, timeout)
        elapsed = time.time() - start_time

        if error or result is None:
            print(f"    {'TIMEOUT' if error == 'timeout' else 'FAILED'}: {mesh.name} ({error})")
            all_metrics.append({
                'num_charts': float('inf'),
                'seam_length': float('inf'),
                'angular_distortion': 0.0,
                'area_distortion': float('inf'),
                'overall_area_distortion': float('inf'),
                'time_seconds': elapsed,
            })
            per_mesh_results.append({'name': mesh.name, 'success': False, 'error': error})
            continue

        # Evaluate
        try:
            metrics = evaluate_uv_mapping(
                mesh, result['uv_coords'], result['chart_ids'],
                result.get('raw_chart_uvs'),
                result.get('raw_chart_faces')
            )
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
                np.save(os.path.join(mesh_dir, 'uv_coords.npy'), result['uv_coords'])
                np.save(os.path.join(mesh_dir, 'chart_ids.npy'), result['chart_ids'])
                with open(os.path.join(mesh_dir, 'metrics.json'), 'w') as f:
                    json.dump(metrics, f, indent=2)

        except Exception as e:
            print(f"    ERROR on {mesh.name}: {e}", flush=True)
            all_metrics.append({
                'num_charts': float('inf'),
                'seam_length': float('inf'),
                'angular_distortion': 0.0,
                'area_distortion': float('inf'),
                'overall_area_distortion': float('inf'),
                'time_seconds': elapsed,
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
                        default='/home/user/data/downloads/common_shapes',
                        help='Directory containing mesh files')
    parser.add_argument('--output-dir', type=str,
                        default='/home/user/checkpoints',
                        help='Output directory for results')
    parser.add_argument('--method', type=str, default='partuv',
                        choices=['partuv', 'xatlas', 'both'],
                        help='Method to evaluate')
    parser.add_argument('--distortion-threshold', type=float, default=1.5,
                        help='Distortion threshold tau')
    parser.add_argument('--use-merge', action='store_true', default=False,
                        help='Use Merge heuristic')
    parser.add_argument('--max-candidates', type=int, default=3,
                        help='Max chart candidates from Normal heuristic')
    parser.add_argument('--n-threads', type=int, default=1,
                        help='Number of threads')
    parser.add_argument('--name', type=str, default='run1',
                        help='Name for this run')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\n=== Loading meshes from {args.data_dir} ===")
    meshes = load_all_common_shapes(args.data_dir)
    print(f"Loaded {len(meshes)} meshes\n")

    if not meshes:
        print("ERROR: No meshes found.")
        sys.exit(1)

    results = {}

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
        print(f"  Overall Area Dist: {result['overall_area_distortion']:.4f}")
        print(f"  Success Rate: {result['success_rate']:.1f}%")
        print(f"  Avg Time: {result['avg_time']:.1f}s")

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
        print(f"  Overall Area Dist: {result['overall_area_distortion']:.4f}")
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
