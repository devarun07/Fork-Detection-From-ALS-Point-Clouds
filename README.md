# Detection of forked trees from airborne laser scanning point clouds for stem-quality assessment in thinning operations

Code accompanying the manuscript on automated detection of forked trees and their
base-trunk height estimation from airborne laser scanning (ALS) point clouds,
Evo study site, southern Finland.

Given an AdTree skeleton PLY, the tool builds a directed skeleton graph,
detects forks by a topology test (Algorithm 1 in the paper), and reports the
base-trunk height as the vertical span of the trunk path from the base to the
lowest fork.

## Overview

The repository has two parts.

The first is the fork-detection tool itself. It takes AdTree skeleton PLY files
as input, either a single skeleton or a folder of them, builds a directed
skeleton graph for each, applies the topology-based fork test (Algorithm 1 in
the paper), and reports the fork decision together with the base-trunk height.
This is the reusable component and is described under **Usage** below. It has no
dependency on the study data or the upstream processing stages.

The second is `paper_reproduction/`, which regenerates the numbers reported in
the manuscript. This part wraps the tool with the study's reference data and
evaluation scripts, and assumes the upstream stages (instance segmentation,
wood-leaf classification, and skeletonisation) have already produced the input
skeletons. See `paper_reproduction/README.md` for the data layout and the
commands that reproduce each table and figure.

<!-- ## Scope

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
numbers using all upstream stages, see `paper_reproduction/`. -->

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The code was tested on Ubuntu 24.04 LTS. The code requires Python 3.10 or newer.

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

In folder mode, the tool picks up every file ending in `_skeleton.ply` and
writes one row per tree to the output CSV. Trees that fail (unreadable PLY,
disconnected skeleton, and so on) are recorded with `status=failed` and the run
continues, so one bad tree does not stop the batch.

The CSV has the following columns:

| Column | Description |
|---|---|
| `name` | Tree identifier, taken from the skeleton filename. |
| `is_forked` | Fork decision: `True` if a fork was detected, `False` otherwise. |
| `base_trunk_height_m` | Base-trunk height in metres: the vertical span of the trunk path from the base to the lowest fork. Empty for non-forked trees. |
| `n_forks` | Number of forks detected in the tree. |
| `status` | `ok` if the tree was processed successfully, `failed` if it could not be. |
| `error` | Failure reason when `status=failed`; empty otherwise. |

## Parameters

The three fork-detection thresholds are in `config.py`; values match the
manuscript.

| Parameter | config key | Default Value | Role |
|---|---|---|---|
| Child branches for a fork | `n_child_nodes_needed_for_fork` | 2 | Minimum child branches a node needs to be considered a fork candidate |
| Path-length threshold `T_L` | `min_path_length_threshold` | 4.0 m | Minimum cumulative length of a branch's longest outward path. Rejects short twigs and spurious skeleton segments. |
| Vertical-gain threshold `T_H` | `min_vertical_gain_threshold` | 3.0 m | Minimum height a branch must rise above the candidate node. Rejects near-horizontal branches that do not represent a competing stem. |

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
