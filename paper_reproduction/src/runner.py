"""
Batch runner.

``run_dataset("manual_forked")`` runs every tree in the dataset and returns a
list of per-tree records, each carrying its ground-truth ``label``.
"""

from pathlib import Path
import time

import config
from core import run_one_tree


def _list_skeletons(skeleton_dir: Path):
    return sorted(p for p in Path(skeleton_dir).iterdir() if p.suffix == ".ply")


def run_dataset(dataset_name: str, only_names: set = None):
    ds = config.DATASETS[dataset_name]
    skel_dir, label = ds["skeleton"], ds["label"]
    files = _list_skeletons(skel_dir)
    if config.VERBOSE:
        print(f"[{dataset_name}] running {len(files)} skeletons from {skel_dir}")

    results = []
    t0 = time.time()
    for i, f in enumerate(files, 1):
        rec = run_one_tree(f, fork_params=config.FORK_DETECT_PARAMS)
        rec["label"] = label
        rec["dataset"] = dataset_name
        results.append(rec)
        if config.VERBOSE and i % 10 == 0:
            print(f"  [{i}/{len(files)}]  last={f.name}  status={rec['status']}")
    if config.VERBOSE:
        print(f"[{dataset_name}] done in {time.time()-t0:.1f}s")

    if only_names is not None:
        only = set(only_names)
        results = [r for r in results if r["name"] in only]
    return results


def run_many(dataset_names):
    return {name: run_dataset(name) for name in dataset_names}