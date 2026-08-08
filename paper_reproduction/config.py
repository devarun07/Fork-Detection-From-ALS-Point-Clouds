"""Paths and dataset definitions for reproducing the paper's evaluation.

Data is read from $EVO_DATA_ROOT.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PAPER_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Import the main config so fork-detection parameters are shared, and put
# both src trees on the path (main src/ for the pipeline, this src/ for the
# reproduction-only modules: runner, reference, metrics).
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PAPER_DIR / "src"))
from config import FORK_DETECT_PARAMS  # noqa: F401,E402  (re-exported)

EVO_DATA_ROOT = Path(os.environ.get("EVO_DATA_ROOT", REPO_ROOT / "sample_data"))

MLS_REFERENCE_DICT_PKL = EVO_DATA_ROOT / "base_trunk_reference_dict.pkl"
MLS_BASE_TRUNK_FOLDER  = EVO_DATA_ROOT / "forked_reference_base_stem"

TOTAL_FORKED   = 174
TOTAL_UNFORKED = 159


def _ds(skeleton_rel, label):
    return {"skeleton": EVO_DATA_ROOT / skeleton_rel, "label": label}


# Three evaluation settings from the paper:
#   manual_*  manually corrected stems (upper bound on detector quality)
#   p1_*      ForestFormer3D with FOR-instanceV2 weights
#   p2_*      ForestFormer3D (FGI-EMIT) + ResNet16FPN
# For each end-to-end setting, INST = valid-instance stage, SEM = valid-
# semantic stage.
DATASETS = {
    "manual_forked":   _ds("ManuallyCorrectedStems/Forked_AdTree_Output", 1),
    "manual_unforked": _ds("ManuallyCorrectedStems/Unforked_AdTree_Output", 0),

    "p1_INST_forked":   _ds("ForInstanceV2/ValidInstances/Forked", 1),
    "p1_INST_unforked": _ds("ForInstanceV2/ValidInstances/Unforked", 0),
    "p1_SEM_forked":    _ds("ForInstanceV2/ValidSemantic/Forked", 1),
    "p1_SEM_unforked":  _ds("ForInstanceV2/ValidSemantic/Unforked", 0),

    "p2_INST_forked":   _ds("FGI-EMIT/ValidInstances/Forked", 1),
    "p2_INST_unforked": _ds("FGI-EMIT/ValidInstances/Unforked", 0),
    "p2_SEM_forked":    _ds("FGI-EMIT/ValidSemantic/Forked", 1),
    "p2_SEM_unforked":  _ds("FGI-EMIT/ValidSemantic/Unforked", 0),
}

VERBOSE = True
