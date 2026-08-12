# Detection of forked trees from airborne laser scanning point clouds for stem-quality assessment in thinning operations

Code accompanying the manuscript on automated detection of forked trees and their
base-trunk height estimation from airborne laser scanning (ALS) point clouds,
Evo study site, southern Finland.

Given an AdTree skeleton PLY, the tool builds a directed skeleton graph,
detects forks by a topology test (Algorithm 1 in the paper), and reports the
base-trunk height.

## Overview

The repository has two parts.

1. **Fork-detection tool**: It takes AdTree skeleton PLY files
as input, either a single skeleton or a folder of them, builds a directed
skeleton graph for each, applies the topology-based fork test (Algorithm 1 in
the paper), and reports the fork decision together with the base-trunk height.
This is the reusable component and is described under the **Usage** section below. It has no
dependency on the study data or the upstream processing stages.

2. **Reproduce paper-results**: The `reproduce_paper_results` folder reproduces the results reported in the paper for the full fork detection pipeline. It explains the upstream stages (instance segmentation, wood-leaf classification, and skeletonisation) and provides the necessary instructions for setup and running (see `reproduce_paper_results/README.md`). The upstream stages are pre-run for the data and the skeletons are generated. The `reproduce_results.ipynb` notebook runs the whole pipeline step by step and displays the results for the pre-run skeletons that are reported in the paper.



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
continues, so one failure does not stop the batch.

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
  skeleton_graph.py       AdTree PLY reader, build graph
  fork_detection.py       topology-based fork detection (Algorithm 1)
  base_trunk.py           trunk-path extraction (base to lowest fork)
  pipeline.py             run_tree(): single-tree pipeline
  core.py                 per-tree record + base-trunk height
scripts/
  fork_detect.py          the CLI
sample_data/              sample skeleton data
reproduce_paper_results/  information and code to reproduce paper results
```

## License and citation

<!-- License is not yet chosen; see `LICENSE.txt`. Citation metadata is in
`CITATION.cff`; both need completing before the repository is made public. -->
