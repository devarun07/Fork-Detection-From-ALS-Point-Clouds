#!/usr/bin/env python3
"""Fork detection and base-trunk height from AdTree skeletons.

Examples
--------
    python scripts/fork_detect.py --tree path/to/TREE_skeleton.ply
    python scripts/fork_detect.py --folder path/to/skeletons/
    python scripts/fork_detect.py --folder path/to/skeletons/ --out results.csv
"""

import sys
import csv
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402 
from core import run_one_tree  # noqa: E402


# CSV columns for both modes.
COLUMNS = ["name", "is_forked", "base_trunk_height_m", "n_forks",
           "status", "error"]


def _row_from_record(rec):
    """Turn a run_one_tree() record into a CSV-friendly row."""
    return {
        "name":                rec["name"],
        "is_forked":           rec["is_forked_pred"] if rec["is_forked_pred"] is not None else "",
        "base_trunk_height_m": f"{rec['height_minmax']:.3f}" if rec["height_minmax"] is not None else "",
        "n_forks":             rec["n_forks"],
        "status":              rec["status"],
        "error":               rec["error"],
    }


def _run_one(path):
    rec = run_one_tree(path, fork_params=config.FORK_DETECT_PARAMS)
    return _row_from_record(rec)


def _print_row(row):
    """One-line per-tree status printed to stdout."""
    if row["status"] != "ok":
        print(f"  {row['name']:<50}  FAILED: {row['error']}")
    elif row["is_forked"] == 1:
        print(f"  {row['name']:<50}  forked   height={row['base_trunk_height_m']} m")
    else:
        print(f"  {row['name']:<50}  not forked")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # --tree and --folder are mutually exclusive; one is required.
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--tree",   type=Path, help="a single AdTree skeleton PLY")
    mode.add_argument("--folder", type=Path, help="a folder of skeleton PLYs")
    ap.add_argument(
        "--out", type=Path, default=None,
        help="CSV output path. Folder mode defaults to 'fork_detect.csv' inside "
             "the given folder; tree mode prints to stdout only unless --out is set.",
    )
    args = ap.parse_args()

    # ---------------- tree mode: run on one skeleton ----------------
    if args.tree is not None:
        if not args.tree.exists():
            raise SystemExit(f"file not found: {args.tree}")

        row = _run_one(args.tree)
        _print_row(row)

        if args.out is not None:
            with open(args.out, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLUMNS)
                w.writeheader()
                w.writerow(row)
            print(f"\nsaved: {args.out}")
        return

    # ---------------- folder mode: run on every skeleton in the folder ----------------
    if not args.folder.is_dir():
        raise SystemExit(f"not a folder: {args.folder}")

    # Pick up files ending in '_skeleton.ply' at the top level of the folder;
    # this matches AdTree's naming convention and avoids picking up unrelated PLYs.
    files = sorted(p for p in args.folder.glob("*.ply")
                   if p.name.endswith("_skeleton.ply"))
    if not files:
        raise SystemExit(f"no *_skeleton.ply files found in {args.folder}")

    out_path = args.out or (args.folder / "fork_detect.csv")
    print(f"running on {len(files)} skeletons under {args.folder}")

    # Failures are recorded as status='failed' rows and the loop continues,
    # so one bad tree does not abort a batch.
    rows = []
    n_forked = n_unforked = n_failed = 0
    for p in files:
        row = _run_one(p)
        rows.append(row)
        _print_row(row)
        if row["status"] != "ok":
            n_failed += 1
        elif row["is_forked"] == 1:
            n_forked += 1
        else:
            n_unforked += 1

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(f"\nsummary: forked={n_forked}  not_forked={n_unforked}  failed={n_failed}")
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()