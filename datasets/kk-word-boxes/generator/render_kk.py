"""Render a synthetic KK word list to an image (for figures, the YOLO check and the QR study)."""

import cv2
import numpy as np

FONT = cv2.FONT_HERSHEY_SIMPLEX


def _draw_word(img, text, quad, background):
    """Warp one rendered word into its quadrilateral, touching only the local bounding box."""
    q = np.array(quad, np.float32)
    h = float(np.linalg.norm(q[3] - q[0]))
    scale = h / 30.0
    (tw, _), _ = cv2.getTextSize(text, FONT, scale, 1)
    patch = np.full((int(h * 1.3) + 2, max(tw, 1) + int(h / 4) + 4, 3), background, np.uint8)
    cv2.putText(patch, text, (1, int(h)), FONT, scale, (20, 20, 20), max(1, int(h / 14)), cv2.LINE_AA)
    dst = np.float32([q[0], q[1], q[1] + (q[3] - q[0]) * 1.3, q[0] + (q[3] - q[0]) * 1.3])
    x0, y0 = np.floor(dst.min(axis=0)).astype(int)
    x1, y1 = np.ceil(dst.max(axis=0)).astype(int) + 1
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, img.shape[1]), min(y1, img.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    src = np.float32([[0, 0], [patch.shape[1], 0], [patch.shape[1], patch.shape[0]], [0, patch.shape[0]]])
    m = cv2.getPerspectiveTransform(src, dst - np.float32([x0, y0]))
    warped = cv2.warpPerspective(patch, m, (x1 - x0, y1 - y0), borderValue=(background,) * 3)
    roi = img[y0:y1, x0:x1]
    mask = warped.min(axis=2) < background - 40
    roi[mask] = warped[mask]


def draw_grid(img, angle=0.0):
    """Table rules of both KK tables (cell borders), rotated like the words."""
    from synth_kk import T1, T2, T1_Y, T2_Y, TH, PITCH
    lines = []
    for cols, top, first_row, rows in ((T1, T1_Y - 8, T1_Y + 3.4 * TH, 10), (T2, T2_Y - 8, T2_Y + 4.6 * TH, 10)):
        x0, x1 = cols[0][1] - 5, cols[-1][2] + 5
        bottom = first_row + rows * PITCH * TH
        ys = [top, first_row - 0.3 * TH] + [first_row + r * PITCH * TH - 0.3 * TH for r in range(1, rows + 1)]
        lines += [((x0, y), (x1, y)) for y in ys]
        lines += [((c[1] - 5, top), (c[1] - 5, bottom - 0.3 * TH)) for c in cols] + [((x1, top), (x1, bottom - 0.3 * TH))]
    a = np.radians(angle)
    cx, cy = img.shape[1] / 2, img.shape[0] / 2
    rot = lambda p: (int(cx + (p[0] - cx) * np.cos(a) - (p[1] - cy) * np.sin(a)),
                     int(cy + (p[0] - cx) * np.sin(a) + (p[1] - cy) * np.cos(a)))
    for p, q in lines:
        cv2.line(img, rot(p), rot(q), (60, 60, 60), 2)


def render(doc, qr=None, qr_box=None, background=245, grid=False):
    """Draw every word; optionally table rules and a QR image in qr_box = (x, y, size)."""
    img = np.full((doc["height"], doc["width"], 3), background, np.uint8)
    if grid:
        draw_grid(img, doc.get("angle", 0.0))
    for w in doc["words"]:
        _draw_word(img, w["text"], w["quad"], background)
    if qr is not None and qr_box is not None:
        x, y, s = qr_box
        img[y:y + s, x:x + s] = cv2.resize(qr, (s, s), interpolation=cv2.INTER_NEAREST)
    return img
