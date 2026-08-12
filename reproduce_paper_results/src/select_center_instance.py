#!/usr/bin/env python3
"""Select the tree instance in a segmented ALS crop that matches a reference
tree, and write only that instance.

The segmented file carries a per-point instance id (default field `tree_pred`)
from ForestFormer3D. The reference file is the manually cropped single tree; its
bounding box selects which predicted instance to keep.
"""

import argparse
from copy import deepcopy
from pathlib import Path

import numpy as np
import laspy
from laspy import ExtraBytesParams


def write_instance_subset(seg_las, mask, output_file):
    """Write the masked points to a fresh LAS 1.2 / point format 1 file,
    preserving standard fields and all extra dimensions."""
    header = laspy.LasHeader(point_format=1, version="1.2")
    header.scales = seg_las.header.scales.copy()
    header.offsets = seg_las.header.offsets.copy()

    out = laspy.LasData(header)

    for dim in seg_las.point_format.extra_dimensions:
        out.add_extra_dim(ExtraBytesParams(
            name=dim.name, type=dim.dtype, description=dim.description,
            scales=dim.scales, offsets=dim.offsets))

    out.X = seg_las.X[mask]
    out.Y = seg_las.Y[mask]
    out.Z = seg_las.Z[mask]

    standard = ["intensity", "return_number", "number_of_returns",
                "scan_direction_flag", "edge_of_flight_line", "classification",
                "scan_angle_rank", "user_data", "point_source_id", "gps_time"]
    src = set(seg_las.point_format.dimension_names)
    dst = set(out.point_format.dimension_names)
    for name in standard:
        if name in src and name in dst:
            out[name] = seg_las[name][mask]

    for name in seg_las.point_format.extra_dimension_names:
        out[name] = seg_las[name][mask]

    for vlr in seg_las.header.vlrs:
        if vlr.__class__.__name__ != "ExtraBytesVlr":
            out.header.vlrs.append(deepcopy(vlr))

    out.write(output_file)


def select_centre_instance(seg_file, ref_file, output_file,
                           field="tree_pred", margin=0.25):
    seg = laspy.read(seg_file)
    ref = laspy.read(ref_file)

    xyz = np.column_stack((seg.x, seg.y, seg.z))
    ids = np.asarray(seg[field])
    valid = np.unique(ids[ids > 0])
    if len(valid) == 0:
        print(f"[skip] no valid instance ids in {Path(seg_file).name}")
        return

    minx, miny, minz = ref.header.mins
    maxx, maxy, maxz = ref.header.maxs
    minx -= margin; miny -= margin; minz -= margin
    maxx += margin; maxy += margin; maxz += margin

    best_id, best_count, best_ratio = None, -1, -1.0
    for inst in valid:
        pts = xyz[ids == inst]
        inside = ((pts[:, 0] >= minx) & (pts[:, 0] <= maxx) &
                  (pts[:, 1] >= miny) & (pts[:, 1] <= maxy) &
                  (pts[:, 2] >= minz) & (pts[:, 2] <= maxz))
        count = int(inside.sum())
        ratio = count / len(pts)
        if count > best_count or (count == best_count and ratio > best_ratio):
            best_id, best_count, best_ratio = inst, count, ratio

    print(f"selected instance {best_id}  ({best_count} points inside bbox)")
    write_instance_subset(seg, ids == best_id, output_file)
    print(f"saved: {output_file}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("segmented", help="segmented ALS crop with instance ids (.las/.laz)")
    ap.add_argument("reference", help="manually cropped reference tree (.las/.laz)")
    ap.add_argument("output", help="output .las for the selected instance")
    ap.add_argument("--field", default="tree_pred", help="instance-id field name")
    ap.add_argument("--margin", type=float, default=0.25, help="bbox margin (m)")
    args = ap.parse_args()

    select_centre_instance(args.segmented, args.reference, args.output,
                           field=args.field, margin=args.margin)