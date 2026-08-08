"""
Batch runner with per-dataset caching.

``run_dataset("manual_forked")`` runs every tree on the first call and pickles
the records to ``results/<dataset>.pkl``; later calls return the pickle. Pass
``force_rerun=True`` to recompute.

IMPORTANT: the cache is keyed only by dataset name, not by parameter values.
If you change a threshold in config.py, rerun with force_rerun=True (or delete
results/*.pkl), otherwise stale records will be returned.
"""

from pathlib import Path
import pickle
import time

import config
from core import run_one_tree


def _cache_path(dataset_name: str) -> Path:
    return config.RESULTS_DIR / f"{dataset_name}.pkl"


def _list_skeletons(skeleton_dir: Path):
    return sorted(p for p in Path(skeleton_dir).iterdir() if p.suffix == ".ply")


def run_dataset(dataset_name: str, force_rerun: bool = False,
                only_names: set = None, save: bool = True):
    """
    Return a list of per-tree records for a dataset. Each record carries its
    ground-truth ``label`` so downstream metrics need not inspect the dataset.
    """
    cache = _cache_path(dataset_name)

    if cache.exists() and not force_rerun:
        with open(cache, "rb") as f:
            results = pickle.load(f)
        if config.VERBOSE:
            print(f"[{dataset_name}] loaded {len(results)} cached records "
                  f"from {cache}  (use --rerun after changing parameters)")
    else:
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

        if save:
            with open(cache, "wb") as f:
                pickle.dump(results, f)
            if config.VERBOSE:
                print(f"[{dataset_name}] cached to {cache}")

    if only_names is not None:
        only = set(only_names)
        results = [r for r in results if r["name"] in only]
        if config.VERBOSE:
            print(f"[{dataset_name}] filtered to {len(results)} trees by subset")
    return results


def run_many(dataset_names, **kwargs):
    return {name: run_dataset(name, **kwargs) for name in dataset_names}
