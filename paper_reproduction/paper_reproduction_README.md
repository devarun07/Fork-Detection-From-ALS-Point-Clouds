# Paper reproduction
Information needed to reproduce the numbers in the manuscript, from raw ALS
crops to the tables and figures. Divided into two parts:

- **Upstream pipeline**: the segmentation, centre-instance selection, stem
  extraction, and skeletonisation steps that take raw ALS crops to the
  AdTree skeleton PLYs consumed by `../scripts/fork_detect.py`. Uses external
  tools that must be installed separately.
- **Evaluation**: the fork-detection accuracy figures, the survival funnel,
  and the base-trunk RMSE against the MLS reference. Runs on the outputs of
  the upstream pipeline (or on cached per-tree records shipped with the
  notebook).

## Upstream pipeline

The manuscript reports two end-to-end pipelines that differ only in which
segmentation/classification models are used. Both share the same
denoising, centre-instance selection, stem-extraction and skeletonisation
steps.

### Pipeline 1 — FOR-instanceV2 (fully public)

Uses ForestFormer3D with the FOR-instanceV2 weights released by the original
authors. Semantic (wood/leaf) predictions come from the same model, so no
separate classifier is needed.

Prerequisites:

- **ForestFormer3D** with FOR-instanceV2 weights — instance segmentation and
  wood-leaf semantic prediction.
  https://github.com/bxiang233/ForestFormer3D
- **AdTree** — skeletonisation of stem points.
  https://github.com/tudelft3d/AdTree

Follow each project's installation instructions before running the steps
below.

### Pipeline 2 — FGI-EMIT + ResNet16FPN (weights on request)

Uses ForestFormer3D with FGI-EMIT weights and a separate ResNet16FPN
classifier for wood/leaf segmentation. Neither is publicly released; contact
the corresponding author.

Prerequisites:

- **ForestFormer3D with FGI-EMIT weights** — instance segmentation.
- **ResNet16FPN wood-leaf classifier** — semantic segmentation.
- **AdTree** — skeletonisation.

### Steps

Both pipelines follow the same seven steps.

1. **Denoise** the raw ALS crops (statistical outlier removal).
2. **Instance segmentation** with ForestFormer3D (weights differ by
   pipeline).
3. **Pick the centre instance** for each plot. Each crop covers multiple
   trees; only the one at the plot centre is used for evaluation.
4. **Wood-leaf classification** — for pipeline 1 this is already produced by
   ForestFormer3D; for pipeline 2 run ResNet16FPN.
5. **Prepare AdTree input** by keeping only stem points and writing them to
   `.xyz`.
6. **Skeletonisation** with AdTree, producing one `<name>_skeleton.ply` per
   tree.
7. **Fork detection** with `../scripts/fork_detect.py` on the skeleton
   folder.

Steps 1, 3, 5 and 7 have small Python scripts in this repository (once the
release-ready versions are added). Steps 2, 4 and 6 are external tools; run
them per each project's documentation.

A bash orchestrator that runs the in-repo steps and prompts you to run the
external ones at the right points will be added under `upstream/` once the
Python scripts are cleaned up for release.

## Evaluation

Runs on either the outputs of the upstream pipeline or the cached per-tree
records shipped with the notebook.

Set the data root to the folder holding the AdTree skeletons and the MLS
reference:

```bash
export EVO_DATA_ROOT=/path/to/EvoForkedTrees
```

The dataset layout expected under that root is defined in `config.DATASETS`.

Then either open the notebook or run the CLI scripts:

```bash
jupyter notebook reproduce.ipynb
# or
python reproduce_fork_detection.py
python reproduce_base_trunk_eval.py
```

The runner caches per-tree records to `results/*.pkl` on the first run. After
changing any parameter in `config.py`, rerun with `--rerun` (or delete the
cache), otherwise stale records are returned.

## Notebook

The notebook is intended to be checked in with all cells already executed, so
the tables and figures are visible on GitHub without running anything. Cached
`results/*.pkl` records are small enough to ship alongside it, so re-executing
cells does not need the raw dataset.

The valid/invalid instance-quality labels (from manual inspection at the
instance and semantic stages) are loaded from a CSV inside the notebook,
which makes the survival-funnel counts transparent without hiding the manual
step in folder names.

## Contents

```
config.py                        dataset layout, MLS paths, funnel totals
src/
  runner.py                      batch runner with per-dataset .pkl caching
  reference.py                   MLS reference loading and matching
  metrics.py                     fork accuracy, survival funnel, height metrics
reproduce_fork_detection.py      CLI: fork accuracy + funnel -> results/*.csv
reproduce_base_trunk_eval.py     CLI: base-trunk RMSE -> results/base_trunk_height.csv
reproduce.ipynb                  the same evaluation, with figures, in a notebook
results/                         cached .pkl records and generated .csv (git-ignored)
```
