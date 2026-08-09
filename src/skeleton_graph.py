"""
Skeleton-graph construction from an AdTree PLY.

Reads the binary AdTree skeleton, merges coincident vertices, builds an
undirected graph weighted by edge length, picks the lowest node as the root,
and orients every edge from tips toward the root so that a node's children are
its predecessors. This is the graph consumed by fork detection and base-trunk
extraction.
"""

import numpy as np
import networkx as nx
import warnings


def read_adtree_skeleton_ply(path: str):
    """
    Read a binary little-endian AdTree skeleton PLY.

    The expected header declares a vertex element with x, y, z, radius and an
    edge element with a ``vertex_indices`` list. Polyline edges (list length
    > 2) are split into consecutive segments.

    Returns
    -------
    xyz : (N, 3) float32
    radius : (N,) float32
    edges : (K, 2) int32   zero-based vertex indices
    """
    with open(path, "rb") as f:
        header = []
        while True:
            line = f.readline()
            if not line:
                raise ValueError("EOF before end_header")
            header.append(line)
            if line.strip() == b"end_header":
                break

        header_text = b"".join(header).decode("ascii", errors="replace")
        n_verts = n_edges = None
        for ln in header_text.splitlines():
            if ln.startswith("element vertex"):
                n_verts = int(ln.split()[-1])
            elif ln.startswith("element edge"):
                n_edges = int(ln.split()[-1])
        if n_verts is None or n_edges is None:
            raise ValueError("Could not parse element vertex/edge counts")

        v = np.fromfile(f, dtype="<f4", count=n_verts * 4).reshape(n_verts, 4)
        xyz = v[:, :3].astype(np.float32)
        radius = v[:, 3].astype(np.float32)

        edge_pairs = []
        for _ in range(n_edges):
            k = np.fromfile(f, dtype="<u4", count=1)[0]
            idx = np.fromfile(f, dtype="<i4", count=int(k))
            if k == 2:
                edge_pairs.append(idx)
            elif k > 2:
                edge_pairs.extend(np.stack([idx[:-1], idx[1:]], axis=1))

        edges = np.asarray(edge_pairs, dtype=np.int32)
        return xyz, radius, edges


def merge_identical_xyz(xyz, rad, edges, atol=1e-8):
    """
    Merge vertices with identical coordinates. When merged vertices carry
    different radii, the maximum is kept and a warning is printed.

    Returns
    -------
    xyz_u, rad_u, edges_u, inv
        Unique vertices, their radii, remapped undirected edges, and the
        old-index -> new-index mapping.
    """
    xyz = np.asarray(xyz)
    rad = np.asarray(rad, dtype=float)
    edges = np.asarray(edges, dtype=np.int32)
    if len(xyz) != len(rad):
        raise ValueError("xyz and rad must have the same length")

    xyz_u, inv = np.unique(xyz, axis=0, return_inverse=True)
    inv = inv.ravel()
    n_unique = len(xyz_u)

    rad_u = np.full(n_unique, np.nan, dtype=float)
    for new_idx in range(n_unique):
        vals = rad[np.where(inv == new_idx)[0]]
        if not np.allclose(vals, vals[0], atol=atol, rtol=0.0):
            warnings.warn(
                f"duplicate XYZ merged at new_idx={new_idx}, "
                f"radii differ: {vals}, keeping max",
                stacklevel=2,
            )
        rad_u[new_idx] = np.max(vals)

    e = inv[edges]
    e = e[e[:, 0] != e[:, 1]]      # drop self-loops from merges
    e = np.sort(e, axis=1)         # canonical undirected ordering
    edges_u = np.unique(e, axis=0)  # drop duplicate edges
    return xyz_u, rad_u, edges_u, inv


def build_undirected_skeleton_graph(xyz, radius, edges) -> nx.Graph:
    """Undirected graph with per-node position/radius and per-edge length."""
    G = nx.Graph()
    for i in range(xyz.shape[0]):
        G.add_node(
            int(i),
            x=float(xyz[i, 0]), y=float(xyz[i, 1]), z=float(xyz[i, 2]),
            radius=float(radius[i]),
            pos=(float(xyz[i, 0]), float(xyz[i, 1]), float(xyz[i, 2])),
        )
    p0, p1 = xyz[edges[:, 0]], xyz[edges[:, 1]]
    lengths = np.linalg.norm(p1 - p0, axis=1)
    for (u, v), length in zip(edges, lengths):
        G.add_edge(int(u), int(v), length=float(length))
    return G


def choose_root(G: nx.Graph, axis: str = "z") -> int:
    """Root is the node with the smallest coordinate along ``axis`` (ground)."""
    return min(G.nodes, key=lambda n: G.nodes[n][axis])


def orient_toward_root(G: nx.Graph, root: int, weight: str = "length") -> nx.DiGraph:
    """
    Orient every edge from the farther-from-root endpoint to the nearer one
    (tips -> root), using geodesic distance along the skeleton. A node's
    predecessors are therefore its children (farther from the root).
    """
    dist = nx.single_source_dijkstra_path_length(G, root, weight=weight)

    D = nx.DiGraph()
    D.add_nodes_from(G.nodes(data=True))

    eps = 1e-12
    for u, v, attr in G.edges(data=True):
        du, dv = dist.get(u), dist.get(v)
        if du is None or dv is None:
            continue  # different component
        if du + eps < dv:
            D.add_edge(v, u, **attr)   # v farther -> u nearer
        elif dv + eps < du:
            D.add_edge(u, v, **attr)
        else:
            D.add_edge(max(u, v), min(u, v), **attr)  # deterministic tie-break

    nx.set_node_attributes(D, dist, "root_dist")
    D.nodes[root]["root_dist"] = 0.0
    return D
