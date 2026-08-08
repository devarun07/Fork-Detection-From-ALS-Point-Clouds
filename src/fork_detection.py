"""
Topology-based fork detection on the directed skeleton graph.

This implements Algorithm 1 of the manuscript. The skeleton graph is directed
from tips toward the root, so the children of a candidate node are its
predecessors, and moving farther from the root also follows predecessors.

A node is accepted as a fork only if at least ``n_child_nodes_needed_for_fork``
of its child branches each satisfy both:

    * a minimum cumulative path length   (T_L, ``min_path_length_threshold``)
    * a minimum vertical gain above it   (T_H, ``min_vertical_gain_threshold``)

The default thresholds (4.0 m and 3.0 m) are the values reported in the paper.
They are set in ``config.FORK_DETECT_PARAMS``.
"""

import numpy as np


def find_real_fork_nodes_length_and_vertical_gain(
    D,
    node_positions,
    n_child_nodes_needed_for_fork=2,
    min_path_length_threshold=4.0,
    min_vertical_gain_threshold=3.0,
):
    """
    Detect fork nodes from a tip-to-root directed skeleton graph.

    Parameters
    ----------
    D : networkx.DiGraph
        Skeleton graph oriented from tips toward the root. Edges carry a
        ``length`` attribute (fallback: Euclidean distance between endpoints).
    node_positions : dict[int, numpy.ndarray]
        Mapping node id -> array([x, y, z]).
    n_child_nodes_needed_for_fork : int
        Minimum number of qualifying child branches for a node to be a fork.
    min_path_length_threshold : float
        T_L, minimum cumulative branch length from the fork outward (metres).
    min_vertical_gain_threshold : float
        T_H, minimum vertical rise above the fork node (metres).

    Returns
    -------
    real_forks : list[int]
        Node ids accepted as forks.
    fork_paths : dict[int, list[dict]]
        For each fork, the two qualifying child paths with the greatest
        length, each stored as {"length", "vertical_gain", "path"}.
    """
    real_forks = []
    fork_paths = {}

    for node in D.nodes:
        if D.in_degree(node) < n_child_nodes_needed_for_fork:
            continue

        z_fork = node_positions[node][2]
        valid_child_paths = []

        for child in D.predecessors(node):
            # edge direction is child -> node
            start_len = float(
                D.edges[child, node].get(
                    "length",
                    np.linalg.norm(node_positions[node] - node_positions[child]),
                )
            )

            best_path = [node, child]
            best_length = start_len
            best_vertical_gain = (
                max(node_positions[node][2], node_positions[child][2]) - z_fork
            )

            # Depth-first walk away from the root, tracking the longest branch.
            stack = [(child, start_len, [node, child])]
            visited = set()

            while stack:
                current, cum_length, path = stack.pop()
                if current in visited:
                    continue
                visited.add(current)

                z_values = [node_positions[n][2] for n in path]
                vertical_gain = max(z_values) - z_fork

                # Keep the longest path; break ties by larger vertical gain.
                if cum_length > best_length or (
                    np.isclose(cum_length, best_length)
                    and vertical_gain > best_vertical_gain
                ):
                    best_length = cum_length
                    best_vertical_gain = vertical_gain
                    best_path = path

                for succ in D.predecessors(current):
                    edge_len = float(
                        D.edges[succ, current].get(
                            "length",
                            np.linalg.norm(
                                node_positions[current] - node_positions[succ]
                            ),
                        )
                    )
                    stack.append((succ, cum_length + edge_len, path + [succ]))

            if (
                best_length >= min_path_length_threshold
                and best_vertical_gain >= min_vertical_gain_threshold
            ):
                valid_child_paths.append(
                    {
                        "length": float(best_length),
                        "vertical_gain": float(best_vertical_gain),
                        "path": best_path,
                    }
                )

        if len(valid_child_paths) >= n_child_nodes_needed_for_fork:
            valid_child_paths.sort(
                key=lambda x: (x["length"], x["vertical_gain"]), reverse=True
            )
            fork_paths[node] = valid_child_paths[:2]
            real_forks.append(node)

    return real_forks, fork_paths
