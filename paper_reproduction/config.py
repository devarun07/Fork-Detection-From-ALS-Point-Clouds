"""Paths and dataset definitions for reproducing the paper's evaluation.

Data is read from $EVO_DATA_ROOT.
"""

import os
import sys
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PAPER_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Put the reproduction-only modules (runner, reference, metrics) and the main
# tool's modules (core, ...) on the path. Reproduction modules take priority.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(PAPER_DIR / "src"))

# Share the fork-detection parameters with the main tool. The tool's config.py
# is loaded by file path under a distinct module name so the two config.py
# files never collide in sys.modules; this module stays the one named `config`.
def _load_main_config():
    spec = importlib.util.spec_from_file_location(
        "fork_tool_config", REPO_ROOT / "config.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

FORK_DETECT_PARAMS = _load_main_config().FORK_DETECT_PARAMS

EVO_DATA_ROOT = Path(os.environ.get("EVO_DATA_ROOT", REPO_ROOT / "sample_data"))

MLS_REFERENCE_DICT_PKL = EVO_DATA_ROOT / "base_trunk_reference_dict.pkl"
MLS_BASE_TRUNK_FOLDER  = EVO_DATA_ROOT / "forked_reference_base_stem"

TOTAL_FORKED   = 174
TOTAL_UNFORKED = 159


def _ds(skeleton_rel, label):
    return {"skeleton": EVO_DATA_ROOT / skeleton_rel, "label": label}


DATASETS = {
    "manual_forked":   _ds("ManuallyCorrectedStems/Forked_ALS_AdTree_Output", 1),
    "manual_unforked": _ds("ManuallyCorrectedStems/Unforked_ALS_AdTree_Output", 0),

    "p1_INST_forked":   _ds("ForInstanceV2/ValidInstances/Forked", 1),
    "p1_INST_unforked": _ds("ForInstanceV2/ValidInstances/Unforked", 0),
    "p1_SEM_forked":    _ds("ForInstanceV2/ValidSemantic/Forked", 1),
    "p1_SEM_unforked":  _ds("ForInstanceV2/ValidSemantic/Unforked", 0),

    "p2_INST_forked":   _ds("FGI-EMIT/ValidInstances/Forked", 1),
    "p2_INST_unforked": _ds("FGI-EMIT/ValidInstances/Unforked", 0),
    "p2_SEM_forked":    _ds("FGI-EMIT/ValidSemantic/Forked", 1),
    "p2_SEM_unforked":  _ds("FGI-EMIT/ValidSemantic/Unforked", 0),
}

VERBOSE = False