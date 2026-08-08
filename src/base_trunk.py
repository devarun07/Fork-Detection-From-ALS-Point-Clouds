"""
Base-trunk path extraction.

Given the skeleton graph and the detected forks, trace the trunk path from the
root (base) up to the lowest fork. The base-trunk height is then the vertical
span of the nodes along this path (see core.base_trunk_height_minmax).
"""

import networkx as nx


def find_trunk_path(G, lowest_fork, base_node):
    """
    Ordered node ids from base -> fork.

    On a skeleton (a tree) the path between two nodes is unique, so the
    shortest path by edge ``length`` is that unique path.
    """
    if lowest_fork is None:
        return [base_node]
    path_fork_to_base = nx.shortest_path(
        G, source=lowest_fork, target=base_node, weight="length"
    )
    return list(reversed(path_fork_to_base))  # base -> fork


def find_base_trunk(G, node_positions, root, forks):
    """
    Return the trunk path (list of node ids) from the base to the lowest fork.
    If no forks are present, the path is just the base node.
    """
    lowest_fork = None
    if forks:
        lowest_fork = min(forks, key=lambda n: node_positions[n][2])
    return find_trunk_path(G, lowest_fork, root)
