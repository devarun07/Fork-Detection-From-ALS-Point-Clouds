#!/usr/bin/env python3
"""Convert a LAS/LAZ tree to a min-normalised XYZ text file for AdTree.

Coordinates are shifted so the minimum XYZ sits at the origin, which is the
local frame AdTree expects.
"""

import argparse
from pathlib import Path

import numpy as np
import laspy


def las_to_xyz(input_file, output_file):
    las = laspy.read(input_file)
    pts = np.column_stack([np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)])

    if pts.shape[0] == 0:
        print(f"skipping empty file: {Path(input_file).name}")
        return

    pts_norm = pts - pts.min(axis=0)
    np.savetxt(output_file, pts_norm, fmt="%.6f %.6f %.6f")
    print(f"saved {output_file}  ({pts.shape[0]} points)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="input .las/.laz file")
    ap.add_argument("output", help="output .xyz file")
    args = ap.parse_args()

    las_to_xyz(args.input, args.output)