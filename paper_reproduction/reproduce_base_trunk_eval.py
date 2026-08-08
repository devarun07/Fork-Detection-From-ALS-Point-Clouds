#!/usr/bin/env python3
"""
Base-trunk height against the MLS reference.

For each of the three settings (manually corrected, FOR-instanceV2,
FGI-EMIT + ResNet16FPN), restrict to trees with an MLS reference, keep those
the pipeline detected as forked, pair the predicted base-trunk height against
the reference, and report RMSE, bias, MAE, R^2 and relative RMSE.

Runs whichever settings are present under the data directory; missing ones are
skipped.

Output
------
    results/base_trunk_height.csv

Usage
-----
    python paper_reproduction/reproduce_base_trunk_eval.py
    python paper_reproduction/reproduce_base_trunk_eval.py --rerun
"""

import sys
import csv
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402

from runner import run_dataset                       # noqa: E402
from reference import load_mls_reference             # noqa: E402
from metrics import (pair_estimates_with_reference,  # noqa: E402
                     height_metrics, print_height_metrics)


SETTINGS = {
    "Manually corrected":                       "manual_forked",
    "ForestFormer3D (FOR-instanceV2)":          "p1_INST_forked",
    "ForestFormer3D (FGI-EMIT) + ResNet16FPN":  "p2_INST_forked",
}


def main(force_rerun=False):
    lookup, mls_heights, _ = load_mls_reference()

    rows = []
    for setting, ds in SETTINGS.items():
        try:
            recs = run_dataset(ds, force_rerun=force_rerun)
        except FileNotFoundError as e:
            print(f"[{setting}] skipped: {e}")
            continue

        recs = [r for r in recs if lookup(r["name"]) is not None]
        print(f"[{setting}] records with MLS reference: {len(recs)}")

        paired = pair_estimates_with_reference(recs, lookup, mls_heights,
                                               height_field="height_minmax")
        m = height_metrics(paired)
        print_height_metrics(m, title=setting)
        rows.append({"setting": setting, **m})

    if rows:
        out = config.RESULTS_DIR / "base_trunk_height.csv"
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"\nSaved summary: {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args()
    main(force_rerun=args.rerun)
