#!/usr/bin/env python3
"""PartUV: Part-Based UV Unwrapping of 3D Meshes.

This module implements the PartUV pipeline for UV unwrapping of 3D meshes.
The pipeline combines part priors with geometry-based heuristics
in a top-down recursive tree search.

Key components:
1. Hierarchical part tree construction (agglomerative clustering)
2. Top-down recursive tree search (PartTreeSearch algorithm)
3. Normal heuristic (face normal clustering)
4. Merge heuristic (OBB-based merging)
5. LSCM flattening
"""

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from data.mesh_loader import Mesh, compute_face_normals, compute_face_areas
from method.lscm_flattening import lscm_flatten


@dataclass
class UVChart:
    """Represents a UV chart (a set of mesh faces with UV coordinates."""
    face_indices: np.ndarray  # Indices of faces in this chart
    uv_coords: np.ndarray     # (n_vertices, 2) UV coordinates
    distortion: float        # Area distortion of this chart
    vertex_indices: np.ndarray  # Unique vertex indices in this chart


@dataclass
class ChartSet:
    """A set of UV charts forming a complete UV mapping."""
    charts: List[UVChart]
    chart_count: int
    max_distortion: float
    total_distortion: float

    @classmethod
    def from_charts(cls, charts: List[UVChart]):
        if not charts:
            return cls(charts=[], chart_count=0, max_distortion=999.0, total_distortion=999.0)
        max_d = max(c.distortion for c in charts)
        total_d = np.mean([c.distortion for c in charts])
        return cls(charts=charts, chart_count=len(charts),
                   max_distortion=max_d, total_distortion=total_d)


@dataclass
class TreeNode:
    """A node in the hierarchical part tree."""
    face_indices: np.ndarray  # Faces in this node's submesh
    left: Optional['TreeNode']
    right: Optional['TreeNode']
    depth: int


def build_part_tree(vertices: np.ndarray, faces: np.ndarray,
                   face_features: np.ndarray, max_depth: int = 15) -> TreeNode:
    """Build a hierarchical binary tree using agglomerative clustering.

    Each node stores its face set. Internal nodes have left/right children
    representing a binary split. Leaf nodes have no children.
    """
    all_indices = np.arange(len(faces))

    def build(indices: np.ndarray, depth: int) -> TreeNode:
        if len(indices) <= 1 or depth >= max_depth:
            return TreeNode(face_indices=indices, left=None, right=None, depth=depth)

        # Split using agglomerative clustering
        feats = face_features[indices]
        if len(feats) <= 2:
            return TreeNode(face_indices=indices, left=None, right=None, depth=depth)

        n_split = 2
        try:
            clustering = AgglomerativeClustering(
                n_clusters=n_split, linkage='ward', metric='euclidean'
            )
            labels = clustering.fit_predict(feats)
        except Exception:
            return TreeNode(face_indices=indices, left=None, right=None, depth=depth)

        mask1 = labels == 0
        mask2 = labels == 1
        idx1 = indices[mask1]
        idx2 = indices[mask2]

        if len(idx1) == 0 or len(idx2) == 0:
            return TreeNode(face_indices=indices, left=None, right=None, depth=depth)

        left = build(idx1, depth + 1)
        right = build(idx2, depth + 1)

        return TreeNode(face_indices=indices, left=left, right=right, depth=depth)

    return build(all_indices, 0)


class PartUV:
    """PartUV: Part-Based UV Unwrapping pipeline."""

    def __init__(self, distortion_threshold: float = 1.25,
                 use_merge_heuristic: bool = True,
                 max_candidates: int = 10,
                 max_depth: int = 15,
                 n_threads: int = 1):
        self.tau = distortion_threshold
        self.use_merge = use_merge_heuristic
        self.max_candidates = max_candidates
        self.max_depth = max_depth
        self.n_threads = n_threads

    def unwrap(self, mesh: Mesh) -> ChartSet:
        """Unwrap a mesh and return UV charts."""
        # Compute face features: use normals as the primary geometric feature
        normals = compute_face_normals(mesh.vertices, mesh.faces)

        # Build hierarchical part tree using face normals
        tree = build_part_tree(mesh.vertices, mesh.faces, normals, self.max_depth)

        # Run recursive tree search
        result = self._search(tree, mesh, float('inf'))

        if result is None or result.chart_count == 0:
            # Fallback: single chart with all faces
            all_faces = np.arange(mesh.n_faces)
            uv, dist = lscm_flatten(mesh.vertices, mesh.faces, all_faces)
            chart = UVChart(
                face_indices=all_faces,
                uv_coords=uv,
                distortion=dist,
                vertex_indices=np.unique(mesh.faces)
            )
            return ChartSet.from_charts([chart])

        return result

    def _search(self, node: TreeNode, mesh: Mesh, budget: float) -> Optional[ChartSet]:
        """Top-down recursive tree search (Algorithm 1 from paper)."""
        if budget < 1:
            return None

        face_indices = node.face_indices
        if len(face_indices) <= 2:
            uv, dist = lscm_flatten(mesh.vertices, mesh.faces, face_indices)
            unique_verts = np.unique(mesh.faces[face_indices])
            chart = UVChart(face_indices=face_indices, uv_coords=uv,
                           distortion=dist, vertex_indices=unique_verts)
            return ChartSet.from_charts([chart])

        # Generate candidates using Normal heuristic
        chart_sets = self._gen_candidates_h1(mesh, face_indices)

        valid_sets = []
        for charts_faces in chart_sets:
            # Evaluate: flatten all charts together
            total_distortion = 0.0
            valid_charts = []
            for cf in charts_faces:
                if len(cf) == 0:
                    continue
                uv, dist = lscm_flatten(mesh.vertices, mesh.faces, cf)
                unique_verts = np.unique(mesh.faces[cf])
                chart = UVChart(face_indices=cf, uv_coords=uv,
                              distortion=dist, vertex_indices=unique_verts)
                valid_charts.append(chart)
                total_distortion = max(total_distortion, dist)

            if total_distortion <= self.tau:
                valid_sets.append((valid_charts, total_distortion))

        if not valid_sets:
            # No valid candidate from Normal heuristic -> recurse to children
            if node.left is None or node.right is None:
                # Leaf node but no valid candidate
                uv, dist = lscm_flatten(mesh.vertices, mesh.faces, face_indices)
                unique_verts = np.unique(mesh.faces[face_indices])
                chart = UVChart(face_indices=face_indices, uv_coords=uv,
                               distortion=dist, vertex_indices=unique_verts)
                return ChartSet.from_charts([chart])

            left_result = None
            right_result = None

            if self.n_threads > 1:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    f1 = executor.submit(self._search, node.left, mesh, float('inf'))
                    f2 = executor.submit(self._search, node.right, mesh, float('inf'))
                    left_result = f1.result()
                    right_result = f2.result()
            else:
                left_result = self._search(node.left, mesh, float('inf'))
                right_result = self._search(node.right, mesh, float('inf'))

            merged_charts = []
            if left_result:
                merged_charts.extend(left_result.charts)
            if right_result:
                merged_charts.extend(right_result.charts)

            if not merged_charts:
                return None
            return ChartSet.from_charts(merged_charts)

        # Select best: minimum chart count among valid sets
        best_charts, best_dist = min(valid_sets, key=lambda x: len(x[0]))
        best_set = ChartSet.from_charts(best_charts)

        # Try to find better solution via recursion
        if node.left is not None and node.right is not None:
            budget_prime = max(1, len(best_charts) - 1)

            left_result = None
            right_result = None

            if self.n_threads > 1:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    f1 = executor.submit(self._search, node.left, mesh, budget_prime - 1)
                    f2 = executor.submit(self._search, node.right, mesh,
                                         budget_prime - (left_result.chart_count if left_result else 0))
                    left_result = f1.result()
                    right_result = f2.result()
            else:
                left_result = self._search(node.left, mesh, budget_prime - 1)
                right_count = left_result.chart_count if left_result else 0
                right_result = self._search(node.right, mesh, budget_prime - right_count)

            if left_result and right_result:
                combined_charts = left_result.charts + right_result.charts
                combined = ChartSet.from_charts(combined_charts)
                if combined.max_distortion <= self.tau and combined.chart_count < best_set.chart_count:
                    best_set = combined

        return best_set

    def _gen_candidates_h1(self, mesh: Mesh,
                           face_indices: np.ndarray) -> List[List[np.ndarray]]:
        """Normal heuristic: generate chart decomposition candidates.

        For each n_clusters from 1 to max_candidates:
        - Cluster faces by normal similarity
        - Get connected components per cluster
        - Return as a list of chart decompositions (each is a list of face arrays)

        Returns:
            List of chart decompositions, where each decomposition is a list
            of face index arrays (one array per chart).
        """
        if len(face_indices) <= 1:
            return [[face_indices]]

        sub_normals = compute_face_normals(mesh.vertices, mesh.faces[face_indices])

        if len(face_indices) <= self.max_candidates:
            # Return all faces as one chart
            return [[face_indices]]

        candidates = []
        n_to_test = min(self.max_candidates, len(face_indices) - 1)

        for n_clusters in range(1, n_to_test + 1):
            try:
                clustering = AgglomerativeClustering(
                    n_clusters=n_clusters,
                    linkage='ward',
                    metric='euclidean'
                )
                labels = clustering.fit_predict(sub_normals)
            except Exception:
                continue

            # For each cluster, get connected components (each becomes a chart)
            charts_faces = []
            for label in range(n_clusters):
                mask = labels == label
                cluster_indices = face_indices[mask]
                if len(cluster_indices) == 0:
                    continue
                # Get connected components within this cluster
                connected = self._get_connected_faces(mesh.faces, cluster_indices)
                charts_faces.extend(connected)

            if charts_faces:
                candidates.append(charts_faces)

        if not candidates:
            candidates = [[face_indices]]

        return candidates

    def _gen_candidate_h2(self, mesh: Mesh,
                          face_indices: np.ndarray) -> List[np.ndarray]:
        """Merge heuristic: OBB-based chart decomposition."""
        if len(face_indices) <= 1:
            return [face_indices]

        sub_verts = mesh.vertices[np.unique(mesh.faces[face_indices])]
        sub_normals = compute_face_normals(mesh.vertices, mesh.faces[face_indices])

        # Compute PCA for OBB
        centered = sub_verts - sub_verts.mean(axis=0)
        cov = np.dot(centered.T, centered) / (len(sub_verts) + 1e-10)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvectors = eigenvectors[:, idx]

        # Assign each face to one of 6 OBB sides
        face_labels = np.zeros(len(face_indices), dtype=np.int32)
        for i, fi in enumerate(face_indices):
            normal = sub_normals[i]
            best_dot = -2.0
            best_axis = 0
            for ax in range(3):
                dot = np.abs(np.dot(normal, eigenvectors[:, ax]))
                if dot > best_dot:
                    best_dot = dot
                    best_axis = ax
            face_centroid = mesh.vertices[mesh.faces[fi]].mean(axis=0)
            proj_c = np.dot(face_centroid - sub_verts.mean(axis=0), eigenvectors[:, best_axis])
            sign = 0 if proj_c >= 0 else 3
            face_labels[i] = sign + best_axis

        # Group faces by label
        groups = {}
        for i, fi in enumerate(face_indices):
            label = face_labels[i]
            if label not in groups:
                groups[label] = []
            groups[label].append(fi)

        # Get connected components within each group
        all_charts = []
        for label, group_faces in groups.items():
            if len(group_faces) > 0:
                conn = self._get_connected_faces(mesh.faces, np.array(group_faces))
                all_charts.extend(conn)

        if not all_charts:
            return [face_indices]

        # Iteratively merge adjacent charts if distortion stays below threshold
        merged = True
        while merged and len(all_charts) > 1:
            merged = False
            best_merge = None
            best_distortion = float('inf')

            for i in range(len(all_charts)):
                for j in range(i + 1, len(all_charts)):
                    combined = np.concatenate([all_charts[i], all_charts[j]])
                    try:
                        uv, dist = lscm_flatten(mesh.vertices, mesh.faces, combined)
                        if dist <= self.tau and dist < best_distortion:
                            best_distortion = dist
                            best_merge = (i, j)
                    except Exception:
                        continue

            if best_merge is not None:
                i, j = best_merge
                all_charts[i] = np.concatenate([all_charts[i], all_charts[j]])
                del all_charts[j]
                merged = True

        return all_charts if all_charts else [face_indices]

    def _get_connected_faces(self, all_faces: np.ndarray,
                              face_indices: np.ndarray) -> List[np.ndarray]:
        """Find connected components of faces."""
        if len(face_indices) == 0:
            return []

        face_to_local = {fi: i for i, fi in enumerate(face_indices)}
        n_local = len(face_indices)
        adj = [[] for _ in range(n_local)]

        # Build adjacency from shared edges
        edge_map = {}
        for li, fi in enumerate(face_indices):
            for k in range(3):
                a, b = all_faces[fi, k], all_faces[fi, (k + 1) % 3]
                edge = (min(a, b), max(a, b))
                if edge not in edge_map:
                    edge_map[edge] = []
                edge_map[edge].append(li)

        for edge, faces_list in edge_map.items():
            if len(faces_list) == 2:
                adj[faces_list[0]].append(faces_list[1])
                adj[faces_list[1]].append(faces_list[0])

        # BFS to find connected components
        visited = np.zeros(n_local, dtype=bool)
        components = []

        for i in range(n_local):
            if visited[i]:
                continue
            component = []
            queue = [i]
            visited[i] = True
            while queue:
                curr = queue.pop(0)
                component.append(face_indices[curr])
                for neighbor in adj[curr]:
                    if not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)
            components.append(np.array(component, dtype=np.int32))

        return components
