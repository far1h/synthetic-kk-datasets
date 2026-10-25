"""Write warped photos of fictional KK pages with exact ground-truth maps.

Usage: python make.py <out dir> [--seeds 2] [--levels 0.4 0.8 1.0] [--families perspective curl fold mesh]
                      [--backgrounds table] [--seed 0]
Per sample: the flat page (PNG), the warped frame (JPEG 95) and maps.npz with
the backward map (inv_u, inv_v: flat x/y of each warped pixel), the forward
map (fx, fy: warped x/y of each flat pixel) and the four page corners in the
warped frame. Maps are stored as int16 in 1/16-pixel units; divide by
``scale`` (16) to get pixels. labels.csv lists family, strength and background.
"""

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

from synth import BACKGROUNDS, FAMILIES, make_warp, render_flat

SCALE = 16


def fixed(a):
    """Return a map in int16 1/16-pixel units."""
    return np.round(a * SCALE).astype(np.int16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--levels", type=float, nargs="+", default=[0.4, 0.8, 1.0])
    ap.add_argument("--families", nargs="+", default=list(FAMILIES), choices=FAMILIES)
    ap.add_argument("--backgrounds", nargs="+", default=["table"], choices=BACKGROUNDS)
    a = ap.parse_args()
    out, rows = Path(a.out), []
    for seed in range(a.seed, a.seed + a.seeds):
        flat = render_flat(seed)
        sub = out / f"page{seed:04d}"
        sub.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(sub / "flat.png"), flat.image)
        for fam in a.families:
            for s in a.levels:
                for bg in a.backgrounds:
                    w = make_warp(flat, fam, s, seed, background=bg)
                    stem = f"{fam}_{s:g}_{bg}"
                    cv2.imwrite(str(sub / f"{stem}.jpg"), w.image, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    np.savez_compressed(sub / f"{stem}_maps.npz", scale=SCALE, corners=w.corners,
                                        **{k: fixed(getattr(w, k)) for k in ("inv_u", "inv_v", "fx", "fy")})
                    rows.append({"image": f"{sub.name}/{stem}.jpg", "flat": f"{sub.name}/flat.png",
                                 "maps": f"{sub.name}/{stem}_maps.npz", "seed": seed, "family": fam,
                                 "strength": s, "background": bg, "height": w.image.shape[0],
                                 "width": w.image.shape[1]})
    with open(out / "labels.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    print(len(rows), "warped samples")


if __name__ == "__main__":
    main()
