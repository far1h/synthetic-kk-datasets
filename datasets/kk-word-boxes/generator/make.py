"""Write synthetic Kartu Keluarga (KK) documents: OCR-like word boxes, ground truth and images.

Usage: python make.py <out dir> [--per-scenario 40] [--images 2] [--seed 20261020]
                      [--sigmas 0 1 2 3] [--angles 0 1 2 5 10]
docs.jsonl holds one document per line: word boxes (text, quadrilateral, tag)
and the true header and member table. For the first ``--images`` clean
documents, images/ holds the rendered page at every blur sigma x rotation
angle, as JPEG quality 90, with the 2x3 rotation matrix in images.csv.
"""

import argparse
import csv
import json
from pathlib import Path

import cv2

from render_kk import render
from synth_kk import dataset

SIGMAS = [0.0, 1.0, 2.0, 3.0]
ANGLES = [0.0, 1.0, 2.0, 5.0, 10.0]
QUALITY = 90


def degrade(img, sigma, angle):
    """Blur, rotate about the centre on an expanded white canvas; return the image and 2x3 matrix."""
    out = cv2.GaussianBlur(img, (0, 0), sigma) if sigma > 0 else img
    hh, ww = out.shape[:2]
    m = cv2.getRotationMatrix2D((ww / 2, hh / 2), angle, 1.0)
    c, s = abs(m[0, 0]), abs(m[0, 1])
    nw, nh = int(hh * s + ww * c), int(hh * c + ww * s)
    m[0, 2] += nw / 2 - ww / 2
    m[1, 2] += nh / 2 - hh / 2
    if angle:
        out = cv2.warpAffine(out, m, (nw, nh), borderValue=(255, 255, 255))
    return out, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--per-scenario", type=int, default=40)
    ap.add_argument("--images", type=int, default=2)
    ap.add_argument("--seed", type=int, default=20261020)
    ap.add_argument("--sigmas", type=float, nargs="+", default=SIGMAS)
    ap.add_argument("--angles", type=float, nargs="+", default=ANGLES)
    a = ap.parse_args()
    out = Path(a.out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    docs = dataset(a.per_scenario, a.seed)
    with open(out / "docs.jsonl", "w") as f:
        for d in docs:
            f.write(json.dumps(d) + "\n")
    rows = []
    for d in [d for d in docs if d["scenario"] == "clean"][:a.images]:
        page = render(d, grid=True)
        for sigma in a.sigmas:
            for angle in a.angles:
                img, m = degrade(page, sigma, angle)
                name = f"{d['id']}_s{sigma:g}_r{angle:g}.jpg"
                cv2.imwrite(str(out / "images" / name), img, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])
                rows.append({"file": f"images/{name}", "doc_id": d["id"], "sigma": sigma, "angle": angle,
                             "matrix": json.dumps(m.round(6).tolist())})
    with open(out / "images.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file", "doc_id", "sigma", "angle", "matrix"])
        w.writeheader()
        w.writerows(rows)
    print(len(docs), "documents,", len(rows), "images")


if __name__ == "__main__":
    main()
