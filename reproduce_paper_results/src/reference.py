"""
MLS reference loading and matching for base-trunk evaluation.

Builds a lookup that maps an ALS tree name to its MLS reference by
(gridID, plotID, treeID). When a queried name has plotID == 'na', the match
relaxes to (gridID, treeID), but only when that is unambiguous; otherwise the
match is skipped to avoid a wrong pairing.

Reads:
    config.MLS_REFERENCE_DICT_PKL   the ALS->MLS name dictionary
    config.MLS_BASE_TRUNK_FOLDER    the MLS base-stem clouds (for heights)
"""

import pickle
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import laspy

import config


_GRID_RE = re.compile(r"gridID_(\d+_\d+)")
_PLOT_RE = re.compile(r"plotID_([^_]+)")
_TREE_RE = re.compile(r"treeID_(\d+(?:_\d+)?)")


def _strip_extension(name: str) -> str:
    return name.replace(".las", "").replace(".laz", "")


def tree_key(name: str):
    """Parse (gridID, plotID, treeID); plotID is 'na' if absent. None if grid or tree missing."""
    g = _GRID_RE.search(name)
    t = _TREE_RE.search(name)
    p = _PLOT_RE.search(name)
    if not g or not t:
        return None
    plot = p.group(1) if p else "na"
    return (g.group(1), plot, t.group(1))


def load_mls_reference():
    """
    Returns
    -------
    lookup : callable(name) -> mls_name or None
    mls_heights : dict[str, float]   mls_name -> reference base-trunk height (m)
    als_to_mls : dict[str, str]      original ALS name -> mls_name
    """
    with open(config.MLS_REFERENCE_DICT_PKL, "rb") as f:
        d = pickle.load(f)

    raw_map = d["ALS_to_MLS_dict"]
    als_to_mls = {k: _strip_extension(v) for k, v in raw_map.items()}

    full_key_to_mls = {}                  # (grid, plot, tree) -> mls
    grid_tree_to_mls = defaultdict(list)  # (grid, tree)       -> [mls, ...]
    for ref_name, mls_name in als_to_mls.items():
        k = tree_key(ref_name)
        if k is None:
            continue
        full_key_to_mls[k] = mls_name
        grid_tree_to_mls[(k[0], k[2])].append(mls_name)

    def lookup(name: str):
        k = tree_key(name)
        if k is None:
            return None
        if k in full_key_to_mls:
            return full_key_to_mls[k]
        if k[1] == "na":
            candidates = grid_tree_to_mls.get((k[0], k[2]), [])
            if len(candidates) == 1:
                return candidates[0]
        return None

    mls_heights = {}
    for f in Path(config.MLS_BASE_TRUNK_FOLDER).iterdir():
        if f.suffix not in (".las", ".laz"):
            continue
        las = laspy.read(f)
        pts = np.vstack([las.x, las.y, las.z]).T
        h = float(pts[:, 2].max() - pts[:, 2].min())
        mls_heights[_strip_extension(f.name)] = round(h, 3)

    return lookup, mls_heights, als_to_mls
