"""Fork-detection parameters and the src/ path setup."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
_SRC = REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Passed to the fork detector; values match the manuscript.
FORK_DETECT_PARAMS = {
    "n_child_nodes_needed_for_fork": 2,
    "min_path_length_threshold":     4.0,   # T_L, metres
    "min_vertical_gain_threshold":   3.0,   # T_H, metres
}
