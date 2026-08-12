#!/usr/bin/env python3
"""Statistical outlier removal on a single ALS crop."""

import argparse
import numpy as np
import laspy
import open3d as o3d


def denoise(in_path, out_path, nb_neighbors=6, std_ratio=2.0):
    las = laspy.read(in_path)
    xyz = np.column_stack((las.x, las.y, las.z))

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz)
    _, ind = pcd.remove_statistical_outlier(nb_neighbors=nb_neighbors,
                                            std_ratio=std_ratio)

    las.points = las.points[ind]
    las.write(out_path)
    print(f"kept {len(ind)} / {len(xyz)} points -> {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="input .las/.laz file")
    ap.add_argument("output", help="output .las/.laz file")
    ap.add_argument("--nb-neighbors", type=int, default=6)
    ap.add_argument("--std-ratio", type=float, default=2.0)
    args = ap.parse_args()

    denoise(args.input, args.output,
            nb_neighbors=args.nb_neighbors, std_ratio=args.std_ratio)