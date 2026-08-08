#!/usr/bin/env python3
"""Reproduce the paper's fork-detection numbers.

Reports the standalone accuracy on the manually corrected stems (the upper
bound on detector quality), and for each end-to-end pipeline the survival
funnel: how many trees are correctly segmented at the instance and semantic
stages, and how many of those are then given the correct fork/non-fork label.

Outputs
-------
    results/fork_detection.csv          manually corrected summary
    results/fork_detection_funnel.csv   per-pipeline, per-class funnel

Usage
-----
    python paper_reproduction/reproduce_fork_detection.py
    python paper_reproduction/reproduce_fork_detection.py --rerun
"""

import sys
import csv
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402

from runner import run_dataset                       # noqa: E402
from metrics import (fork_detection_table, print_fork_detection,  # noqa: E402
                     funnel_row, print_funnel_row)


PIPELINES = {
    "ForestFormer3D (FOR-instanceV2)": {
        "inst": ("p1_INST_forked", "p1_INST_unforked"),
        "sem":  ("p1_SEM_forked",  "p1_SEM_unforked"),
    },
    "ForestFormer3D (FGI-EMIT) + ResNet16FPN": {
        "inst": ("p2_INST_forked", "p2_INST_unforked"),
        "sem":  ("p2_SEM_forked",  "p2_SEM_unforked"),
    },
}
STANDALONE = ("Manually corrected", "manual_forked", "manual_unforked")


def _stage_table(forked_ds, unforked_ds, force_rerun):
    forked = run_dataset(forked_ds, force_rerun=force_rerun)
    unforked = run_dataset(unforked_ds, force_rerun=force_rerun)
    return fork_detection_table(forked + unforked)


def main(force_rerun=False):
    rows = []

    name, fds, uds = STANDALONE
    try:
        tab = _stage_table(fds, uds, force_rerun)
        print_fork_detection(tab, title=name)
        rows.append({"pipeline": name, "class": "forked",
                     "n": tab["n_forked"], "correct": tab["tp"],
                     "accuracy": tab["acc_forked"]})
        rows.append({"pipeline": name, "class": "unforked",
                     "n": tab["n_unforked"], "correct": tab["tn"],
                     "accuracy": tab["acc_unforked"]})
        rows.append({"pipeline": name, "class": "overall",
                     "n": tab["n_total"], "correct": tab["tp"] + tab["tn"],
                     "accuracy": tab["acc_overall"]})
    except FileNotFoundError as e:
        print(f"[{name}] skipped: {e}")

    funnel_rows = []
    for pipeline, stages in PIPELINES.items():
        try:
            inst_tab = _stage_table(*stages["inst"], force_rerun=force_rerun)
            sem_tab = _stage_table(*stages["sem"], force_rerun=force_rerun)
        except FileNotFoundError as e:
            print(f"[{pipeline}] skipped: {e}")
            continue
        print(f"\n=== {pipeline} ===")
        for cls, total in (("forked", config.TOTAL_FORKED),
                           ("unforked", config.TOTAL_UNFORKED)):
            r = funnel_row(cls, inst_tab, sem_tab, total)
            print_funnel_row(r, pipeline=pipeline)
            funnel_rows.append({"pipeline": pipeline, **r})

    if rows:
        out_main = config.RESULTS_DIR / "fork_detection.csv"
        with open(out_main, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"\nSaved standalone summary: {out_main}")

    if funnel_rows:
        out_funnel = config.RESULTS_DIR / "fork_detection_funnel.csv"
        with open(out_funnel, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(funnel_rows[0].keys()))
            w.writeheader(); w.writerows(funnel_rows)
        print(f"Saved funnel: {out_funnel}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rerun", action="store_true",
                    help="recompute cached per-tree records")
    args = ap.parse_args()
    main(force_rerun=args.rerun)
