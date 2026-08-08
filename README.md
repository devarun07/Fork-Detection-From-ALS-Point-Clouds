# Fork detection and base-trunk height from ALS skeletons

Code accompanying the manuscript on automated detection of forked trees and
base-trunk height estimation from airborne laser scanning (ALS) point clouds,
Evo study site, southern Finland.

Given an AdTree skeleton PLY, the tool builds a directed skeleton graph,
detects forks by a topology test (Algorithm 1 in the paper), and reports the
base-trunk height as the vertical span of the trunk path from the base to the
lowest fork.

## Scope

The input to this tool is one AdTree skeleton PLY per tree; the output is the
fork decision and the base-trunk height. Producing the skeletons is done by
external tools, which have their own documentation and installation:

- **AdTree** (TU Delft) — builds the skeleton PLY from a stem point cloud.
  https://github.com/tudelft3d/AdTree
- **ForestFormer3D** — tree instance segmentation upstream of AdTree.
  https://github.com/bxiang233/ForestFormer3D
- **ResNet16FPN** — wood-leaf classifier used in one of the paper's two
  pipelines. Not publicly available; contact the corresponding author.

Follow each tool's own instructions to install it. To reproduce the paper's
numbers using all upstream stages, see `paper_reproduction/`.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.10 or newer.

## Usage

One tree:

```bash
python scripts/fork_detect.py --tree path/to/TREE_skeleton.ply
```

A folder of skeletons:

```bash
python scripts/fork_detect.py --folder path/to/skeletons/
python scripts/fork_detect.py --folder path/to/skeletons/ --out results.csv
```

The folder mode picks up files ending in `_skeleton.ply` and writes one row
per tree to a CSV with columns `name, is_forked, base_trunk_height_m,
n_forks, status, error`. Trees that fail (unreadable PLY, disconnected
skeleton, and so on) are recorded with `status=failed` and the run continues.

## Parameters

The three fork-detection thresholds are in `config.py`; values match the
manuscript.

| Parameter | config key | Value |
|---|---|---|
| Path-length threshold `T_L` | `min_path_length_threshold` | 4.0 m |
| Vertical-gain threshold `T_H` | `min_vertical_gain_threshold` | 3.0 m |
| Child branches for a fork | `n_child_nodes_needed_for_fork` | 2 |

## Repository layout

```
config.py                 fork-detection parameters
src/
  skeleton_graph.py       AdTree PLY reader, graph build, tip->root orient
  fork_detection.py       topology-based fork detection (Algorithm 1)
  base_trunk.py           trunk-path extraction (base to lowest fork)
  pipeline.py             run_tree(): single-tree pipeline
  core.py                 per-tree record + base-trunk height
scripts/
  fork_detect.py          the CLI
sample_data/              one example skeleton
paper_reproduction/       everything needed to reproduce the paper's numbers
```

## License and citation

License is not yet chosen; see `LICENSE.txt`. Citation metadata is in
`CITATION.cff`; both need completing before the repository is made public.
