"""Write synthetic photographs of fictional KK (family card) and ID-card layouts, clean and degraded.

Usage: python make.py <out dir> [--seeds 3] [--seed 0] [--quality 95]
                      [--doc-types kk id_card]
For every seed and condition: a JPEG photo, the document mask (PNG) and a row
in labels.csv with the condition, its parameters and the true value tokens.
Rotations are quarter turns (rot90 k) or small skews in degrees.
"""

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np

import synth

CONDITIONS = (
    [("clean", 0, 0)]
    + [("gaussian", v, 0) for v in (1, 2, 4)]
    + [("motion", v, 0) for v in (9, 25)]
    + [("glare", r, i) for r, i in ((0.06, 0.7), (0.15, 1.0), (0.3, 1.0))]
    + [("jpeg", v, 0) for v in (20, 5)]
    + [("lowlight", v, 0) for v in (0.4, 0.15)]
    + [("noise", v, 0) for v in (20, 45)]
    + [("perspective", v, 0) for v in (0.08, 0.16)]
    + [("rot90", k, 0) for k in (1, 2, 3)]
    + [("skew", a, 0) for a in (-7, 12)]
)


def make_image(doc, seed, kind, v, v2):
    """Return (image, mask) for one condition."""
    rng = np.random.default_rng(seed + 70_000)
    jitter = v if kind == "perspective" else 0.02
    photo = synth.photograph(doc, seed, jitter=jitter)
    mask, _ = synth.doc_mask(seed, doc, jitter=jitter)
    img = {
        "gaussian": lambda: synth.gaussian_blur(photo, v),
        "motion": lambda: synth.motion_blur(photo, int(v), rng.uniform(0, 180)),
        "glare": lambda: synth.glare(photo, mask, rng, v, v2),
        "jpeg": lambda: synth.jpeg(photo, int(v)),
        "lowlight": lambda: synth.low_light(photo, v, rng),
        "noise": lambda: synth.noise(photo, v, rng),
    }.get(kind, lambda: photo)()
    if kind == "rot90":
        img, mask = (np.ascontiguousarray(np.rot90(x, int(v))) for x in (img, mask))
    elif kind == "skew":
        img = synth.skew(img, v)
    return img, mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--quality", type=int, default=95)
    ap.add_argument("--doc-types", nargs="+", default=["kk", "id_card"])
    a = ap.parse_args()
    out = Path(a.out)
    for sub in ("images", "masks"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    rows = []
    for seed in range(a.seed, a.seed + a.seeds):
        for doc_type in a.doc_types:
            render = {"kk": synth.render_family_card, "id_card": synth.render_id_card}[doc_type]
            doc, truth = render(seed)
            for kind, v, v2 in CONDITIONS:
                img, mask = make_image(doc, seed, kind, v, v2)
                stem = f"{doc_type}_{seed:04d}_{kind}_{v:g}" + (f"_{v2:g}" if v2 else "")
                cv2.imwrite(str(out / "images" / f"{stem}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, a.quality])
                cv2.imwrite(str(out / "masks" / f"{stem}.png"), (mask > 0).astype(np.uint8) * 255)
                rows.append({"file": f"images/{stem}.jpg", "mask": f"masks/{stem}.png", "doc_type": doc_type,
                             "seed": seed, "condition": kind, "param": v, "param2": v2,
                             "truth_tokens": json.dumps(truth, ensure_ascii=False)})
    with open(out / "labels.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "images")


if __name__ == "__main__":
    main()
