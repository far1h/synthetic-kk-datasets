"""Seeded synthetic family-card pages and known 3D warps with exact ground truth.

A flat page is rendered with fictional text. A warp places the page on a 3D
surface, projects it with a pinhole camera and frames it like a region crop
with padding. The forward map F (flat pixel -> warped pixel) is analytic and
its inverse is computed numerically, so every metric has an exact reference.
"""

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

import matplotlib

FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
WF, HF = 1200, 800          # flat page size in pixels
PAGE_W, PAGE_H = 1.5, 1.0   # physical page size in page units
PAD = 24                    # crop padding in the warped frame (config default)
LONG_SIDE = 1200            # long side of the warped frame
FAMILIES = ("perspective", "curl", "fold", "mesh")

SYL = ["BA", "DI", "SU", "RA", "NA", "TI", "WA", "MA", "KO", "LE", "SE", "PU", "GA", "RI", "YA", "HE"]
PLACES = ["KOTA ANDARA", "SELO MERAH", "TANJUNG BIRU", "PADANG LIMA", "BUKIT HIJAU", "LEMBAH SARI"]
RELIGION = ["ISLAM", "KRISTEN", "KATOLIK", "HINDU", "BUDDHA"]


def _font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), size)


def _name(rng, parts=2):
    """Fictional name built from random syllables."""
    return " ".join("".join(rng.choice(SYL, size=rng.integers(2, 4))) for _ in range(parts))


def _digits(rng, n):
    return "".join(str(d) for d in rng.integers(0, 10, size=n))


def _date(rng):
    return f"{rng.integers(1, 29):02d}-{rng.integers(1, 13):02d}-{rng.integers(1950, 2020)}"


@dataclass
class FlatPage:
    """Rendered flat page with its text lines and table rule positions."""
    image: np.ndarray                      # BGR uint8, HF x WF
    lines: list = field(default_factory=list)
    fields: list = field(default_factory=list)   # (text, (x0, y0, x1, y1)) of every drawn string
    rule_ys: list = field(default_factory=list)
    table_x: tuple = (0, WF)


def render_flat(seed: int) -> FlatPage:
    """Render a fictional family-card-like page (no real data)."""
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", (WF, HF), (246, 248, 240))
    d = ImageDraw.Draw(img)
    lines, fields = [], []
    draw = d.text

    def text(xy, s, font, fill):
        draw(xy, s, font=font, fill=fill)
        fields.append((s, tuple(float(v) for v in d.textbbox(xy, s, font=font))))
    title = "KARTU KELUARGA"
    f_t, f_h, f_b = _font(34, True), _font(20), _font(17)
    w = d.textlength(title, font=f_t)
    text(((WF - w) / 2, 28), title, f_t, (20, 20, 20))
    lines.append(title)
    no = f"No. {_digits(rng, 16)}"
    w = d.textlength(no, font=f_h)
    text(((WF - w) / 2, 76), no, f_h, (20, 20, 20))
    lines.append(no)
    head = [("NAMA KEPALA KELUARGA", _name(rng, 3)), ("ALAMAT", f"JL {_name(rng, 1)} NO {rng.integers(1, 99)}"),
            ("RT/RW", f"{rng.integers(1, 20):03d}/{rng.integers(1, 20):03d}"),
            ("KECAMATAN", str(rng.choice(PLACES))), ("PROVINSI", "PROVINSI FIKTIF")]
    y = 124
    for k, v in head:
        text((60, y), k, f_h, (25, 25, 25))
        text((380, y), f": {v}", f_h, (25, 25, 25))
        lines.append(f"{k} : {v}")
        y += 32
    cols = [("NO", 50), ("NAMA LENGKAP", 280), ("NIK", 230), ("JENIS KELAMIN", 170),
            ("TEMPAT LAHIR", 190), ("TANGGAL LAHIR", 170)]
    x0, ty, rh = 55, y + 18, 44
    xs = [x0]
    for _, cw in cols:
        xs.append(xs[-1] + cw)
    rows = [[c for c, _ in cols]]
    for i in range(6):
        rows.append([str(i + 1), _name(rng, 2), _digits(rng, 16), str(rng.choice(["LAKI-LAKI", "PEREMPUAN"])),
                     str(rng.choice(PLACES)), _date(rng)])
    rule_ys = []
    for r, row in enumerate(rows):
        yy = ty + r * rh
        rule_ys.append(yy)
        for c, cell in enumerate(row):
            text((xs[c] + 8, yy + 12), cell, f_b if r else _font(15, True), (20, 20, 20))
        lines.append(" ".join(row))
    rule_ys.append(ty + len(rows) * rh)
    for yy in rule_ys:
        d.line([(xs[0], yy), (xs[-1], yy)], fill=(30, 30, 30), width=2)
    for xx in xs:
        d.line([(xx, rule_ys[0]), (xx, rule_ys[-1])], fill=(30, 30, 30), width=2)
    foot = f"DIKELUARKAN TANGGAL {_date(rng)}   SPESIMEN FIKTIF"
    text((60, rule_ys[-1] + 22), foot, f_h, (25, 25, 25))
    lines.append(foot)
    bgr = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    return FlatPage(bgr, lines, fields, [float(v) for v in rule_ys], (xs[0], xs[-1]))


def _rot(axis, ang):
    """Rodrigues rotation matrix."""
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    k = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(ang) * k + (1 - np.cos(ang)) * k @ k


def _smooth_field(rng, shape, sigma):
    f = gaussian_filter(rng.standard_normal(shape), sigma)
    return f / (np.abs(f).max() + 1e-9)


def surface(family, s, rng, x, y):
    """3D points (X, Y, Z) of the page at page coordinates (x, y), plus camera tilt."""
    X, Y, Z = x.copy(), y.copy(), np.zeros_like(x)
    tilt_axis, tilt = (1.0, 0.0, 0.0), 0.0
    if family == "perspective":
        th = rng.uniform(0, 2 * np.pi)
        tilt_axis, tilt = (np.cos(th), np.sin(th), 0.0), np.deg2rad(35.0) * s
    elif family == "curl":
        k = 1.6 * s * rng.choice([-1, 1])
        horiz = rng.random() < 0.3
        t = y if horiz else x
        if abs(k) > 1e-6:
            along, depth = np.sin(k * t) / k, (1 - np.cos(k * t)) / k
        else:
            along, depth = t, np.zeros_like(t)
        if horiz:
            Y = along
        else:
            X = along
        Z = depth
        tilt_axis, tilt = (0.0, 1.0, 0.0), np.deg2rad(8.0) * s
    elif family == "fold":
        horiz = rng.random() < 0.4
        t = y if horiz else x
        t0 = rng.uniform(-0.2, 0.2) * (PAGE_H if horiz else PAGE_W)
        phi = np.deg2rad(50.0) * s * rng.choice([-1, 1])
        dt = t - t0
        h = np.sqrt(dt ** 2 + 0.02 ** 2) - 0.02
        along = t0 + np.sign(dt) * h * np.cos(phi)
        if horiz:
            Y = along
        else:
            X = along
        Z = h * np.sin(phi)
        tilt_axis, tilt = (1.0, 1.0, 0.0), np.deg2rad(6.0) * s
    elif family == "mesh":
        Z = np.zeros_like(x)
        for _ in range(4):
            cx, cy = rng.uniform(-0.6, 0.6), rng.uniform(-0.4, 0.4)
            sg = rng.uniform(0.2, 0.4)
            Z += rng.uniform(-1, 1) * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * sg ** 2))
        Z *= 0.14 * s
        # In-plane displacement: bilinear upsampling of a coarse random lattice.
        lat = rng.uniform(-1, 1, size=(2, 5, 7))
        u = (x + PAGE_W / 2) / PAGE_W * 6
        v = (y + PAGE_H / 2) / PAGE_H * 4
        for c, A in enumerate((X, Y)):
            fld = cv2.remap(lat[c].astype(np.float32), u.astype(np.float32), v.astype(np.float32),
                            cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            A += 0.025 * s * fld
        tilt_axis, tilt = (rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0), np.deg2rad(6.0) * s
    else:
        raise ValueError(family)
    return X, Y, Z, _rot(tilt_axis, tilt) if tilt else np.eye(3)


def flat_to_page(px, py):
    """Flat pixel centres to page coordinates."""
    return (px + 0.5) / WF * PAGE_W - PAGE_W / 2, (py + 0.5) / HF * PAGE_H - PAGE_H / 2


@dataclass
class Warp:
    """A warped sample: image, exact maps and corners."""
    image: np.ndarray       # warped BGR frame
    fx: np.ndarray          # forward map on the flat grid: warped x of each flat pixel
    fy: np.ndarray
    inv_u: np.ndarray       # inverse map on the warped grid: flat x of each warped pixel
    inv_v: np.ndarray
    corners: np.ndarray     # warped positions of the four flat corners (TL, TR, BR, BL)
    surf: tuple             # (X, Y, Z) coarse 3D surface for figures
    photometric: dict


class _Projector:
    """Pinhole camera: project page points and frame them like a padded crop."""

    def __init__(self, family, s, seed):
        self.family, self.s, self.seed = family, s, seed

    def points(self, px, py):
        rng = np.random.default_rng(self.seed)
        x, y = flat_to_page(px, py)
        X, Y, Z, R = surface(self.family, self.s, rng, x, y)
        P = np.stack([X, Y, Z], -1) @ R.T
        D = 3.0
        return P[..., 0] / (P[..., 2] + D) * D, P[..., 1] / (P[..., 2] + D) * D, (X, Y, Z)


def make_warp(flat: FlatPage, family: str, s: float, seed: int, photometric: bool = True,
              background: str = "table") -> Warp:
    """Warp a flat page with a known surface and return exact maps."""
    proj = _Projector(family, s, seed)
    py, px = np.mgrid[0:HF, 0:WF].astype(np.float64)
    xi, yi, _ = proj.points(px, py)
    x_min, x_max, y_min, y_max = xi.min(), xi.max(), yi.min(), yi.max()
    scale = (LONG_SIDE - 2 * PAD) / max(x_max - x_min, y_max - y_min)
    wi = int(round((x_max - x_min) * scale)) + 2 * PAD
    hi = int(round((y_max - y_min) * scale)) + 2 * PAD
    to_px = lambda a, lo: (a - lo) * scale + PAD - 0.5
    fx, fy = to_px(xi, x_min), to_px(yi, y_min)
    # Extended coarse grid (beyond the page) for a defined inverse everywhere.
    step = 4
    gy, gx = np.mgrid[-0.15 * HF:1.15 * HF:step, -0.15 * WF:1.15 * WF:step]
    exi, eyi, _ = proj.points(gx, gy)
    pts = np.stack([to_px(exi, x_min).ravel(), to_px(eyi, y_min).ravel()], 1)
    qy, qx = np.mgrid[0:hi, 0:wi]
    q = np.stack([qx.ravel(), qy.ravel()], 1).astype(np.float64)
    inv = griddata(pts, np.stack([gx.ravel(), gy.ravel()], 1), q, method="linear")
    bad = np.isnan(inv[:, 0])
    if bad.any():
        inv[bad] = griddata(pts, np.stack([gx.ravel(), gy.ravel()], 1), q[bad], method="nearest")
    inv_u = inv[:, 0].reshape(hi, wi).astype(np.float32)
    inv_v = inv[:, 1].reshape(hi, wi).astype(np.float32)
    rng = np.random.default_rng(seed + 7919)
    image, info = _render(flat.image, inv_u, inv_v, proj, rng, photometric, background)
    corners = np.array([[fx[0, 0], fy[0, 0]], [fx[0, -1], fy[0, -1]],
                        [fx[-1, -1], fy[-1, -1]], [fx[-1, 0], fy[-1, 0]]], np.float32)
    cy, cx = np.mgrid[0:HF:20, 0:WF:20].astype(np.float64)
    _, _, surf = proj.points(cx, cy)
    return Warp(image, fx.astype(np.float32), fy.astype(np.float32), inv_u, inv_v, corners, surf, info)


BACKGROUNDS = ("table", "white", "white_textured", "clutter")


def _background(kind, field, hi, wi):
    """Background behind the page: dark table (default), plain white, white with texture, or clutter."""
    if kind == "table":
        bg = np.full((hi, wi, 3), (92, 112, 128), np.float32)
        bg += 18 * field[..., None]
        return bg
    r = np.random.default_rng(hi * 7919 + wi)
    bg = np.full((hi, wi, 3), (232, 235, 232), np.float32)
    bg += 6 * field[..., None]
    if kind == "white_textured":
        bg += gaussian_filter(r.normal(0, 30, (hi, wi)), 1.2)[..., None]
        for y in range(int(r.integers(0, 60)), hi, 90):          # tile grout lines
            bg[y:y + 3] -= 60
    elif kind == "clutter":
        for _ in range(14):
            x0, y0 = int(r.integers(0, wi)), int(r.integers(0, hi))
            w, h = int(r.integers(60, 400)), int(r.integers(40, 300))
            bg[y0:y0 + h, x0:x0 + w] = r.uniform(120, 250, 3)
    elif kind != "white":
        raise ValueError(kind)
    return bg


def _render(flat_img, inv_u, inv_v, proj, rng, photometric, background="table"):
    """Sample the flat page into the warped frame over a background."""
    hi, wi = inv_u.shape
    bg = _background(background, _smooth_field(rng, (hi, wi), 25), hi, wi)
    page = cv2.remap(flat_img, inv_u, inv_v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    inside = ((inv_u >= 0) & (inv_u <= WF - 1) & (inv_v >= 0) & (inv_v <= HF - 1)).astype(np.float32)
    inside = cv2.GaussianBlur(inside, (3, 3), 0)[..., None]
    out = page * inside + bg * (1 - inside)
    info = {"blur_sigma": 0.0, "noise_sigma": 0.0, "jpeg_q": 100, "light": 0.0}
    if photometric:
        # Shading from surface slope plus a linear lighting gradient.
        u = np.clip(inv_u, 0, WF - 1)
        v = np.clip(inv_v, 0, HF - 1)
        sy, sx = np.mgrid[0:HF:8, 0:WF:8].astype(np.float64)
        _, _, (X, Y, Z) = proj.points(sx, sy)
        gz_y, gz_x = np.gradient(Z)
        shade = 1.0 - 0.9 * np.hypot(gz_x, gz_y) / 0.05
        shade = np.clip(shade, 0.65, 1.0).astype(np.float32)
        shade_w = cv2.remap(shade, u / 8, v / 8, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        light = rng.uniform(0.1, 0.3)
        ang = rng.uniform(0, 2 * np.pi)
        yy, xx = np.mgrid[0:hi, 0:wi]
        grad = 1 - light * (0.5 + 0.5 * (np.cos(ang) * (xx / wi - 0.5) + np.sin(ang) * (yy / hi - 0.5)) * 2) / 2
        out = out * (shade_w * inside[..., 0] + (1 - inside[..., 0]))[..., None] * grad[..., None]
        bs, ns, q = rng.uniform(0.0, 1.0), rng.uniform(0.0, 5.0), int(rng.integers(75, 96))
        if bs > 0.05:
            out = cv2.GaussianBlur(out, (0, 0), bs)
        out = out + rng.normal(0, ns, out.shape)
        out = np.clip(out, 0, 255).astype(np.uint8)
        ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, q])
        out = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        info = {"blur_sigma": bs, "noise_sigma": ns, "jpeg_q": q, "light": light}
    return np.clip(out, 0, 255).astype(np.uint8), info


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    fp = render_flat(1)
    cv2.imwrite(str(out / "flat.png"), fp.image)
    for i, fam in enumerate(FAMILIES):
        for s in (0.5, 1.0):
            w = make_warp(fp, fam, s, 100 + i)
            cv2.imwrite(str(out / f"{fam}_{s}.png"), w.image)
            print(fam, s, w.image.shape, w.photometric)
