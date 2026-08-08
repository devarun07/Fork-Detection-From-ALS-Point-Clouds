"""
End-to-end single-tree pipeline.

Given an AdTree skeleton PLY, ``run_tree`` builds the directed skeleton graph,
detects forks (Algorithm 1 in the paper), and traces the base-trunk path from
the root to the lowest fork. The base-trunk height is derived from that path in
core.py.

Fork-detection parameters default to the values in ``config`` (which match the
manuscript), so editing ``config`` changes the applied computation.
"""


import numpy as np

from skeleton_graph import (
    read_adtree_skeleton_ply, merge_identical_xyz,
    build_undirected_skeleton_graph, choose_root, orient_toward_root,
)
from fork_detection import find_real_fork_nodes_length_and_vertical_gain
from base_trunk import find_base_trunk


def run_tree(ply_path, fork_params):
    """
    Run fork detection and base-trunk path extraction on one tree.

    Parameters
    ----------
    ply_path : str or pathlib.Path
        AdTree skeleton PLY.
    fork_params : dict
        Keys: n_child_nodes_needed_for_fork, min_path_length_threshold,
        min_vertical_gain_threshold.  Typically config.FORK_DETECT_PARAMS.

    Returns
    -------
    forks : list[int]
    trunk_path : list[int]
        Skeleton node ids from base to fork.
    node_positions : dict[int, numpy.ndarray]
    """
    
    xyz, rad, edges = read_adtree_skeleton_ply(str(ply_path))
    xyz_u, rad_u, edges_u, _ = merge_identical_xyz(xyz, rad, edges)

    G = build_undirected_skeleton_graph(xyz_u, rad_u, edges_u)
    root = choose_root(G, axis="z")
    D = orient_toward_root(G, root)
    node_positions = {n: np.array(D.nodes[n]["pos"], dtype=float) for n in D.nodes}

    forks, _ = find_real_fork_nodes_length_and_vertical_gain(
        D, node_positions, **fork_params
    )
    trunk_path = find_base_trunk(D, node_positions, root, forks)

    return forks, trunk_path, node_positions