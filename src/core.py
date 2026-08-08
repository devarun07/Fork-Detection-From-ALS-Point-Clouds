"""
Per-tree wrapper used by the CLI.
"""

from pathlib import Path
import numpy as np
from pipeline import run_tree


def base_trunk_height_minmax(trunk_path, node_positions):
    """Base-trunk height: z-span of the trunk-path skeleton nodes (base -> fork)."""
    if trunk_path is None or len(trunk_path) == 0:
        return float("nan")
    zs = np.array([node_positions[n][2] for n in trunk_path], dtype=float)
    return float(zs.max() - zs.min())


def run_one_tree(skeleton_path, fork_params):
    """
    Run one tree and return a picklable record. Never raises; failures are
    recorded with status='failed'.
    """
    name = Path(skeleton_path).name.split("_skeleton")[0]
    out = {
        "name": name,
        "skeleton_path": str(skeleton_path),
        "status": "ok",
        "error": "",
        "is_forked_pred": None,
        "n_forks": 0,
        "height_minmax": None,     # base-trunk height, z-span of trunk-path nodes
    }

    try:
        forks, trunk_path, node_positions = run_tree(
            skeleton_path, fork_params=fork_params)
        is_forked = int(len(forks) > 0)
        out["is_forked_pred"] = is_forked
        out["n_forks"] = int(len(forks))
        if is_forked:
            out["height_minmax"] = base_trunk_height_minmax(trunk_path, node_positions)
    except Exception as e:
        out["status"] = "failed"
        out["error"] = f"{type(e).__name__}: {e}"

    return out
