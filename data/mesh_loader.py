#!/usr/bin/env python3
"""Mesh loader for Common Shapes dataset.

Loads .obj mesh files and provides a unified interface.
"""

import os
import numpy as np
from typing import Tuple, List, Dict, Any


def load_obj_mesh(filepath: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load a .obj mesh file.

    Args:
        filepath: Path to .obj file

    Returns:
        vertices: (N, 3) array of vertex positions
        faces: (M, 3) array of vertex indices (triangles)
    """
    vertices = []
    faces = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if parts[0] == 'v':
                vertices.append([float(x) for x in parts[1:4]])
            elif parts[0] == 'f':
                # Handle face definitions (v, v/t, v/t/n, v//n)
                face_verts = []
                for p in parts[1:]:
                    v_data = p.split('/')
                    face_verts.append(int(v_data[0]) - 1)  # OBJ is 1-indexed
                if len(face_verts) >= 3:
                    # Triangulate if more than 3 vertices (fan triangulation)
                    for i in range(1, len(face_verts) - 1):
                        faces.append([face_verts[0], face_verts[i], face_verts[i + 1]])

    vertices = np.array(vertices, dtype=np.float64)
    faces = np.array(faces, dtype=np.int32)
    return vertices, faces


def compute_face_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Compute normal for each face.

    Args:
        vertices: (N, 3) vertex positions
        faces: (M, 3) triangle indices

    Returns:
        normals: (M, 3) face normals (normalized)
    """
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]

    # Cross product of two edges
    e1 = v1 - v0
    e2 = v2 - v0
    cross = np.cross(e1, e2)

    # Normalize
    norms = np.linalg.norm(cross, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-10)
    normals = cross / norms

    return normals


def compute_face_areas(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Compute area of each face.

    Args:
        vertices: (N, 3) vertex positions
        faces: (M, 3) triangle indices

    Returns:
        areas: (M,) face areas
    """
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]

    e1 = v1 - v0
    e2 = v2 - v0
    cross = np.cross(e1, e2)
    areas = 0.5 * np.linalg.norm(cross, axis=1)
    return areas


def get_connected_components(faces: np.ndarray, n_vertices: int) -> List[np.ndarray]:
    """Find connected components in the mesh.

    Args:
        faces: (M, 3) triangle indices
        n_vertices: total number of vertices

    Returns:
        List of arrays, each containing vertex indices for a component
    """
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components

    rows = []
    cols = []

    for f in faces:
        for i in range(3):
            rows.append(f[i])
            cols.append(f[(i + 1) % 3])
            rows.append(f[(i + 1) % 3])
            cols.append(f[i])

    adj = sp.coo_matrix((np.ones(len(rows)), (rows, cols)),
                          shape=(n_vertices, n_vertices)).tocsr()
    n_components, labels = connected_components(adj, directed=False)

    components = []
    for i in range(n_components):
        mask = labels == i
        vert_indices = np.where(mask)[0]
        components.append(vert_indices)

    return components


def get_face_connectivity(faces: np.ndarray, n_faces: int) -> List[List[int]]:
    """Build adjacency list for faces (shared edge -> adjacent).

    Args:
        faces: (M, 3) triangle indices
        n_faces: number of faces

    Returns:
        adjacency: list of n_faces lists, each containing neighboring face indices
    """
    edge_to_face = {}
    for fi, f in enumerate(faces):
        for i in range(3):
            a, b = f[i], f[(i + 1) % 3]
            edge = (min(a, b), max(a, b))
            if edge not in edge_to_face:
                edge_to_face[edge] = []
            edge_to_face[edge].append(fi)

    adj = [[] for _ in range(n_faces)]
    for faces_list in edge_to_face.values():
        if len(faces_list) == 2:
            adj[faces_list[0]].append(faces_list[1])
            adj[faces_list[1]].append(faces_list[0])

    return adj


def find_boundary_edges(faces: np.ndarray) -> List[Tuple[int, int]]:
    """Find boundary edges (edges shared by only one face).

    Returns:
        List of (v1, v2) tuples for boundary edges
    """
    edge_count = {}
    for f in faces:
        for i in range(3):
            a, b = f[i], f[(i + 1) % 3]
            edge = (min(a, b), max(a, b))
            edge_count[edge] = edge_count.get(edge, 0) + 1

    boundary = [e for e, c in edge_count.items() if c == 1]
    return boundary


class Mesh:
    """Represents a 3D mesh with computed properties."""

    def __init__(self, vertices: np.ndarray, faces: np.ndarray, name: str = ""):
        self.name = name
        self.vertices = vertices
        self.faces = faces
        self.n_vertices = len(vertices)
        self.n_faces = len(faces)
        self._normals = None
        self._areas = None
        self._face_adj = None

    def normals(self) -> np.ndarray:
        if self._normals is None:
            self._normals = compute_face_normals(self.vertices, self.faces)
        return self._normals

    def areas(self) -> np.ndarray:
        if self._areas is None:
            self._areas = compute_face_areas(self.vertices, self.faces)
        return self._areas

    def face_adjacency(self) -> List[List[int]]:
        if self._face_adj is None:
            self._face_adj = get_face_connectivity(self.faces, self.n_faces)
        return self._face_adj


def load_dataset(data_dir: str) -> List[Mesh]:
    """Load all .obj meshes from a directory.

    Args:
        data_dir: Directory containing .obj files

    Returns:
        List of Mesh objects
    """
    meshes = []
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} does not exist")
        return meshes

    for filename in sorted(os.listdir(data_dir)):
        if filename.endswith('.obj'):
            filepath = os.path.join(data_dir, filename)
            try:
                verts, faces = load_obj_mesh(filepath)
                if len(verts) > 0 and len(faces) > 0:
                    name = os.path.splitext(filename)[0]
                    mesh = Mesh(verts, faces, name)
                    meshes.append(mesh)
                    print(f"  Loaded {filename}: {len(verts)} vertices, {len(faces)} faces")
                else:
                    print(f"  Warning: Empty mesh {filename}")
            except Exception as e:
                print(f"  Error loading {filename}: {e}")

    return meshes


def load_all_common_shapes(base_dir: str = None) -> List[Mesh]:
    """Convenience function to load Common Shapes dataset.

    Args:
        base_dir: Base directory (defaults to data/common_shapes)

    Returns:
        List of Mesh objects
    """
    if base_dir is None:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "common_shapes")
    return load_dataset(base_dir)
