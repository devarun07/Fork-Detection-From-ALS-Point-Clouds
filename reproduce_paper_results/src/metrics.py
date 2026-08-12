"""
All metrics are functions of the per-tree records produced by runner.py.
No paths, no I/O, easy to test.
"""

import numpy as np


# ----------------------------------------------- fork detection -------------
def fork_detection_table(records):
    """
    Given a list of per-tree records (each with 'label' and 'is_forked_pred'),
    returns a dict with TP/FP/TN/FN counts and per-class + overall accuracies.
    Trees with status != 'ok' are excluded (and counted under n_failed).
    """
    ok = [r for r in records if r["status"] == "ok" and r["is_forked_pred"] is not None]
    n_failed = len(records) - len(ok)

    tp = sum(1 for r in ok if r["label"] == 1 and r["is_forked_pred"] == 1)
    fn = sum(1 for r in ok if r["label"] == 1 and r["is_forked_pred"] == 0)
    tn = sum(1 for r in ok if r["label"] == 0 and r["is_forked_pred"] == 0)
    fp = sum(1 for r in ok if r["label"] == 0 and r["is_forked_pred"] == 1)

    n_forked     = tp + fn
    n_unforked   = tn + fp
    n_total      = n_forked + n_unforked

    return {
        "n_total":      n_total,
        "n_forked":     n_forked,
        "n_unforked":   n_unforked,
        "n_failed":     n_failed,
        "tp": tp, "fn": fn, "tn": tn, "fp": fp,
        "acc_forked":   tp / n_forked   if n_forked   else float("nan"),
        "acc_unforked": tn / n_unforked if n_unforked else float("nan"),
        "acc_overall":  (tp + tn) / n_total if n_total else float("nan"),
    }


def print_fork_detection(table, title=""):
    if title:
        print(f"\n=== {title} ===")
    t = table
    print(f"  forked   : {t['tp']:>4} / {t['n_forked']:>4}   ({100*t['acc_forked']:.1f}%)")
    print(f"  unforked : {t['tn']:>4} / {t['n_unforked']:>4}   ({100*t['acc_unforked']:.1f}%)")
    print(f"  overall  : {t['tp']+t['tn']:>4} / {t['n_total']:>4}   ({100*t['acc_overall']:.1f}%)")
    if t["n_failed"]:
        print(f"  (failed runs: {t['n_failed']})")


# ----------------------------------------------- base-trunk height ----------
def pair_estimates_with_reference(records, lookup, mls_heights,
                                  height_field="height_minmax"):
    paired = []
    for r in records:
        if r["status"] != "ok" or r["is_forked_pred"] != 1:
            continue
        h_pred = r.get(height_field)
        if h_pred is None or not np.isfinite(h_pred):
            continue
        mls_name = lookup(r["name"])
        if mls_name is None:
            continue
        h_ref = (mls_heights.get(mls_name)
                 or mls_heights.get(mls_name.replace(".las", "")))
        if h_ref is None:
            continue
        paired.append((r["name"], float(h_pred), float(h_ref)))
    return paired


def height_metrics(paired):
    """
    Returns RMSE, bias (pred-ref), MAE, R^2, relative RMSE, and n.
    """
    if len(paired) == 0:
        return {"n": 0, "rmse": float("nan"), "bias": float("nan"),
                "mae": float("nan"), "r2": float("nan"), "rel_rmse": float("nan")}
    a = np.array([(p, r) for _, p, r in paired], dtype=float)
    pred, ref = a[:, 0], a[:, 1]
    err = pred - ref
    rmse = float(np.sqrt(np.mean(err ** 2)))
    bias = float(err.mean())
    mae  = float(np.abs(err).mean())
    ss_res = float(np.sum((ref - pred) ** 2))
    ss_tot = float(np.sum((ref - ref.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rel_rmse = rmse / ref.mean() if ref.mean() > 0 else float("nan")
    return {"n": len(paired), "rmse": rmse, "bias": bias, "mae": mae,
            "r2": r2, "rel_rmse": rel_rmse}


def print_height_metrics(m, title=""):
    if title:
        print(f"\n=== {title} ===")
    print(f"  n        = {m['n']}")
    print(f"  RMSE     = {m['rmse']:.3f} m  ({100*m['rel_rmse']:.1f}%)")
    print(f"  bias     = {m['bias']:+.3f} m")
    print(f"  MAE      = {m['mae']:.3f} m")
    print(f"  R^2      = {m['r2']:.3f}")


def funnel_row(cls, inst_table, sem_table, total):
    """
    One row of the Version-2 funnel (per pipeline, per class).
      instance% = instance-correct / total
      stem%     = stem-correct / instance-correct          (nested)
      det|inst  = TP / instance-correct
      det|stem  = TP / stem-correct                        (from sem-stage run)
    `cls` is 'forked' or 'unforked'.
    """
    if cls == "forked":
        n_inst, det_inst = inst_table["n_forked"], inst_table["tp"]
        n_sem,  det_sem  = sem_table["n_forked"],  sem_table["tp"]
    elif cls == "unforked":
        n_inst, det_inst = inst_table["n_unforked"], inst_table["tn"]
        n_sem,  det_sem  = sem_table["n_unforked"],  sem_table["tn"]
    else:
        raise ValueError(f"cls must be 'forked' or 'unforked', got {cls!r}")

    def safe_div(a, b):
        return a / b if b else float("nan")

    return {
        "class":            cls,
        "total":            total,
        "instance_correct": n_inst,
        "instance_pct":     safe_div(n_inst, total),
        "det_given_inst":   det_inst,
        "det_inst_pct":     safe_div(det_inst, n_inst),
        "stem_correct":     n_sem,
        "stem_pct":         safe_div(n_sem, n_inst),
        "det_given_stem":   det_sem,
        "det_stem_pct":     safe_div(det_sem, n_sem),
    }


def print_funnel_row(row, pipeline=""):
    if pipeline:
        print(f"  [{pipeline}]")
    r = row
    print(f"    {r['class']:9s}  total={r['total']}  "
          f"inst={r['instance_correct']} ({100*r['instance_pct']:.1f}%)  "
          f"det|inst={r['det_given_inst']} ({100*r['det_inst_pct']:.1f}%)  "
          f"stem={r['stem_correct']} ({100*r['stem_pct']:.1f}%)  "
          f"det|stem={r['det_given_stem']} ({100*r['det_stem_pct']:.1f}%)")
