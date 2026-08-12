# Paper results

This folder has two independent parts, with different inputs and different
purposes.

- **Reproduce the reported results.** Reads the shared AdTree skeletons and the
  MLS reference and reproduces every result in the manuscript. It is
  self-contained: no external tools or model weights are needed, only the
  released data. 
- **Upstream pipeline (optional).** Turns raw ALS crops into the AdTree
  skeletons that the evaluation reads. It documents how the shared skeletons
  were produced, and it is the route to apply the method to new ALS data. It
  relies on external tools that must be installed separately.

The two do not depend on each other. To reproduce the paper's numbers, only the
first part is required.

## Reproducing the results

The evaluation is contained in `reproduce_results.ipynb` and runs on the
released data alone.

Set the data root to the folder holding the skeletons and the MLS reference:

```bash
export EVO_DATA_ROOT=/path/to/ExperimentData
```

The layout the notebook reads under `$EVO_DATA_ROOT` is:

```text
ExperimentData/
├── base_trunk_reference_dict.pkl       # ALS-to-MLS mapping and reference heights
├── forked_reference/                   # full MLS reference trees
│   └── MLS_treeID_1.las
├── forked_reference_base_stem/         # MLS base-stem crops used for the base-trunk RMSE
│   └── MLS_treeID_1.las
├── ManuallyCorrectedStems/             # manually corrected stems (detector reference setting)
│   ├── Forked_ALS_AdTree_Output/
│   │   └── ALS_treeID_1.ply
│   └── Unforked_ALS_AdTree_Output/
├── ForInstanceV2/                      # pipeline 1 skeletons
│   ├── ValidInstances/                 # trees passing instance segmentation
│   │   ├── Forked/
│   │   └── Unforked/
│   └── ValidSemantic/                  # trees also passing wood-leaf classification
│       ├── Forked/
│       └── Unforked/
└── FGI-EMIT/                           # pipeline 2 skeletons
    ├── ValidInstances/
    │   ├── Forked/
    │   └── Unforked/
    └── ValidSemantic/
        ├── Forked/
        └── Unforked/
```

The exact paths are defined in `config.DATASETS` and at the top of `config.py`,
so edit them there if your folder names differ.

The notebook produces three results:

- **Standalone fork detection**: fork and non-fork accuracy on the manually
  corrected stems.
- **End-to-end pipelines**: For each end-to-end pipeline, this reports how many trees are correctly segmented at the instance and semantic stages, and, among those, how many are
then given the correct fork/non-fork label.
- **Base-trunk height**: predicted `height_minmax` against the MLS reference for
  all three settings, reported as RMSE, bias, MAE, R² and relative RMSE, with
  the scatter and error-distribution plots.

Open it to view or regenerate these:

```bash
jupyter notebook reproduce_results.ipynb
```

The notebook is checked in with all cells already executed, so the tables and
figures are visible on GitHub without running anything.


## Upstream pipeline (optional)

This part is not needed to reproduce the reported numbers. It documents how the
shared skeletons were produced from the ALS crops, and it is the route to apply
the method to new ALS data. It relies on external tools that must be installed
separately.

<img title="upstream" src="figures/upstream_image.png">

The manuscript reports two end-to-end pipelines. They differ only in the
segmentation and classification models used, and share the same denoising,
centre-instance selection, stem-extraction and skeletonisation steps.

### Pipeline 1 — FOR-instanceV2 + AdTree (fully public)

ForestFormer3D with the FOR-instanceV2 weights released by the original authors.
The wood and leaf semantic predictions come from the same model, so no separate
classifier is needed.

Prerequisites:

- **ForestFormer3D** with FOR-instanceV2 weights, for instance segmentation and
  wood-leaf semantic prediction.
  https://github.com/bxiang233/ForestFormer3D
- **AdTree**, for skeletonisation of the stem points.
  https://github.com/tudelft3d/AdTree

Follow each project's installation instructions before running the steps below.

### Pipeline 2 — FGI-EMIT + ResNet16FPN (weights on request) + AdTree

ForestFormer3D with FGI-EMIT weights and a separate ResNet16FPN classifier for
wood-leaf segmentation. Neither is publicly released; contact the corresponding
author for the code and model weights.

Prerequisites:

- **ForestFormer3D with FGI-EMIT weights**, for instance segmentation.
  https://doi.org/10.1016/j.isprsjprs.2026.04.021
- **ResNet16FPN wood-leaf classifier**, for semantic segmentation.
  https://doi.org/10.1016/j.isprsjprs.2025.07.038
- **AdTree**, for skeletonisation.
  https://github.com/tudelft3d/AdTree


### Steps

Both pipelines follow the same seven steps, starting from a raw ALS crop (an
example `.las` crop is provided in `sample_data/`). Steps 1, 3, 5 and 7 have
small Python scripts in this repository. Steps 2, 4 and 6 use the external tools
listed above; run them per each project's documentation.

**1. Denoise the raw ALS crop** with statistical outlier removal:

```bash
python src/denoise_sor.py sample_data/<tree>.las sample_data/<tree>_filtered.las
```

`--nb-neighbors` (default 6) sets how many neighbours estimate each point's
local mean distance. `--std-ratio` (default 2.0) is the cut-off in standard
deviations, with lower values removing more points.

**2. Instance segmentation with ForestFormer3D.** Pipeline 1 uses the public
FOR-instanceV2 weights; pipeline 2 uses the FGI-EMIT weights available on
request. Follow the ForestFormer3D repository for run instructions.

**3. Select the centre instance for each plot.** Each crop covers several trees,
so one instance must be singled out; only the tree at the plot centre is
evaluated. This step takes the manually cropped reference tree as a second
input. Its bounding box defines the region of interest, and the largest
predicted instance whose points fall inside that box is kept:

```bash
python src/select_centre_instance.py \
    <segmented_crop>.laz <reference_tree>.las <selected_instance>.las
```

**4. Stem-point extraction.** For pipeline 1 the stem points are already produced
by ForestFormer3D in step 2, so no separate step is needed. For pipeline 2, run
the ResNet16FPN classifier.

**5. Prepare the AdTree input.** The stem points are written to a min-normalised
XYZ text file, the input format AdTree reads:

```bash
python src/las_to_xyz.py <stem_points>.las <tree>.xyz
```

**6. Skeletonisation with AdTree.** Run its command-line binary on the `.xyz`
from step 5, writing one `<name>_skeleton.ply` per tree to an output folder:

```bash
./AdTree <tree>.xyz <output_folder>/ -s
```

**7. Fork detection.** The skeletons from step 6 are the input to the
fork-detection tool. Run it on the folder of skeletons:

```bash
python ../scripts/fork_detect.py --folder <skeletons_folder>/ --out results.csv
```

This writes the fork decision and base-trunk height for each tree. See the
top-level `README.md` for the tool's options and output columns.