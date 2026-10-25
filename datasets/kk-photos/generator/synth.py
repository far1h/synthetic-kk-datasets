"""Seeded synthetic document photos: fictional family-card and ID-card layouts.

Every name, number, date and address is generated from syllable and digit
tables with a seeded RNG. Nothing is copied from a real document.
"""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib

FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
REG, BOLD = FONT_DIR / "DejaVuSans.ttf", FONT_DIR / "DejaVuSans-Bold.ttf"

SYL = ["ra", "di", "ta", "su", "wi", "na", "ko", "me", "lan", "sa", "ri", "an", "to",
       "pu", "ja", "ya", "ma", "ha", "ni", "dar", "gu", "le", "bu", "ka", "si", "no"]
PLACES = ["KOTA ARUNA", "SELAWANGI", "TIRTAMULYA", "BUKIT RANA", "PADANGSARI", "KALIJATI"]
RELIGION = ["ISLAM", "KRISTEN", "KATOLIK", "HINDU", "BUDDHA"]
EDU = ["SLTA/SEDERAJAT", "DIPLOMA IV/STRATA I", "SLTP/SEDERAJAT", "TAMAT SD/SEDERAJAT"]
JOB = ["KARYAWAN SWASTA", "WIRASWASTA", "PELAJAR/MAHASISWA", "MENGURUS RUMAH TANGGA"]
REL = ["KEPALA KELUARGA", "ISTRI", "ANAK", "ANAK", "ANAK", "FAMILI LAIN"]
KK_COLS1 = ["No", "Nama Lengkap", "NIK", "Jenis Kelamin", "Tempat Lahir", "Tanggal Lahir",
            "Agama", "Pendidikan", "Jenis Pekerjaan", "Golongan Darah"]
KK_W1 = [0.03, 0.17, 0.14, 0.08, 0.10, 0.09, 0.07, 0.13, 0.13, 0.06]
KK_COLS2 = ["No", "Status Perkawinan", "Tanggal Perkawinan", "Status Hubungan Dalam Keluarga",
            "Kewarganegaraan", "No. Paspor", "No. KITAP", "Nama Ayah", "Nama Ibu"]
KK_W2 = [0.03, 0.11, 0.10, 0.15, 0.10, 0.08, 0.08, 0.175, 0.175]


def font(size, bold=False):
    """Load a DejaVu font shipped with matplotlib."""
    return ImageFont.truetype(str(BOLD if bold else REG), size)


def name(rng, words=2):
    """Fictional upper-case personal name built from random syllables."""
    return " ".join("".join(rng.choice(SYL, rng.integers(2, 4))).upper() for _ in range(words))


def digits(rng, n):
    return "".join(str(d) for d in rng.integers(0, 10, n))


def date(rng, lo=1955, hi=2020):
    return f"{rng.integers(1, 29):02d}-{rng.integers(1, 13):02d}-{rng.integers(lo, hi)}"


def _cell(draw, box, text, size, bold=False, center=False, tokens=None):
    """Draw text inside a cell box and record it as a ground-truth token."""
    x0, y0, x1, y1 = box
    f = font(size, bold)
    while size > 9 and draw.textlength(text, font=f) > (x1 - x0 - 8):
        size -= 1
        f = font(size, bold)
    w = draw.textlength(text, font=f)
    x = x0 + (x1 - x0 - w) / 2 if center else x0 + 5
    draw.text((x, y0 + (y1 - y0 - size) / 2 - 2), text, fill=(20, 20, 25), font=f)
    if tokens is not None and text.strip():
        tokens.extend(text.split())


def _table(draw, x0, y0, width, cols, widths, rows, row_h, size, tokens):
    """Ruled table with a header row and len(rows) body rows."""
    xs = [x0]
    for w in widths:
        xs.append(xs[-1] + w * width)
    head_h = int(row_h * 1.6)
    y_end = y0 + head_h + row_h * len(rows)
    for x in xs:
        draw.line([(x, y0), (x, y_end)], fill=(40, 40, 40), width=2)
    for y in [y0, y0 + head_h] + [y0 + head_h + row_h * (i + 1) for i in range(len(rows))]:
        draw.line([(x0, y), (xs[-1], y)], fill=(40, 40, 40), width=2)
    for i, c in enumerate(cols):
        _cell(draw, (xs[i], y0, xs[i + 1], y0 + head_h), c, size, bold=True, center=True)
    for r, row in enumerate(rows):
        yy = y0 + head_h + r * row_h
        for i, v in enumerate(row):
            _cell(draw, (xs[i], yy, xs[i + 1], yy + row_h), v, size - 2, center=(i == 0), tokens=tokens)
    return y_end


def render_family_card(seed, members=None, width=2339, height=1654):
    """Fictional family-card-like page (landscape A4 at 200 dpi) and its value tokens."""
    rng = np.random.default_rng(seed)
    n = int(members or rng.integers(3, 7))
    tint = tuple(int(v) for v in rng.integers(236, 252, 3))
    img = Image.new("RGB", (width, height), tint)
    d = ImageDraw.Draw(img)
    tokens = []
    for y in range(0, height, 6):  # faint guilloche-like background lines
        d.line([(0, y), (width, y + 40 * np.sin(y / 90))], fill=tuple(max(0, t - 8) for t in tint), width=1)
    d.text((width / 2 - 260, 60), "KARTU KELUARGA", fill=(20, 20, 25), font=font(58, True))
    no_kk = digits(rng, 16)
    d.text((width / 2 - 170, 135), f"No. {no_kk}", fill=(20, 20, 25), font=font(36, True))
    tokens.append(no_kk)
    head = name(rng)
    left = [("Nama Kepala Keluarga", head), ("Alamat", f"JL. {name(rng, 1)} NO. {rng.integers(1, 99)}"),
            ("RT/RW", f"{rng.integers(1, 20):03d}/{rng.integers(1, 15):03d}"), ("Kode Pos", digits(rng, 5))]
    right = [("Desa/Kelurahan", name(rng, 1)), ("Kecamatan", name(rng, 1)),
             ("Kabupaten/Kota", rng.choice(PLACES)), ("Provinsi", "PROVINSI " + name(rng, 1))]
    for col, items in ((90, left), (1290, right)):
        for i, (k, v) in enumerate(items):
            y = 215 + i * 44
            d.text((col, y), k, fill=(20, 20, 25), font=font(26))
            d.text((col + 330, y), f": {v}", fill=(20, 20, 25), font=font(26))
            tokens.extend(v.split())
    people = [head] + [name(rng) for _ in range(n - 1)]
    rows1, rows2 = [], []
    for i in range(10):
        if i < n:
            sex = "LAKI-LAKI" if (i == 0 or rng.random() < 0.5) else "PEREMPUAN"
            rows1.append([str(i + 1), people[i], digits(rng, 16), sex, rng.choice(PLACES), date(rng),
                          rng.choice(RELIGION), rng.choice(EDU), rng.choice(JOB), rng.choice(["A", "B", "O", "AB"])])
            rows2.append([str(i + 1), "KAWIN" if i < 2 else "BELUM KAWIN", date(rng, 1980) if i < 2 else "-",
                          REL[min(i, 5)], "WNI", "-", "-", name(rng), name(rng)])
        else:
            rows1.append([str(i + 1)] + [""] * 9)
            rows2.append([str(i + 1)] + [""] * 8)
    y = _table(d, 70, 420, width - 140, KK_COLS1, KK_W1, rows1, 40, 22, tokens)
    y = _table(d, 70, y + 40, width - 140, KK_COLS2, KK_W2, rows2, 40, 22, tokens)
    issued = date(rng, 2015, 2025)
    d.text((90, y + 40), f"Dikeluarkan Tanggal : {issued}", fill=(20, 20, 25), font=font(26))
    d.text((180, y + 90), "KEPALA KELUARGA", fill=(20, 20, 25), font=font(24, True))
    d.text((180, y + 190), head, fill=(20, 20, 25), font=font(24))
    d.text((width - 700, y + 90), "PEJABAT PENCATATAN SIPIL", fill=(20, 20, 25), font=font(24, True))
    d.text((width - 700, y + 190), name(rng), fill=(20, 20, 25), font=font(24))
    d.text((width - 420, height - 50), "SYNTHETIC SAMPLE", fill=(150, 150, 150), font=font(20))
    tokens.append(issued)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR), tokens


def render_id_card(seed, scale=2):
    """Fictional ID-card-like layout (85.6 x 54 mm; scale 2 is about 600 dpi) and its value tokens."""
    S = lambda v: int(round(v * scale))
    width, height = S(1012), S(638)
    rng = np.random.default_rng(seed + 10_000)
    img = Image.new("RGB", (width, height), (196, 222, 240))
    d = ImageDraw.Draw(img)
    tokens = []
    d.text((width / 2 - S(200), S(18)), "PROVINSI " + name(rng, 1), fill=(10, 10, 10), font=font(S(30), True))
    d.text((width / 2 - S(140), S(56)), str(rng.choice(PLACES)), fill=(10, 10, 10), font=font(S(28), True))
    nik = digits(rng, 16)
    d.text((S(40), S(100)), "NIK", fill=(10, 10, 10), font=font(S(32), True))
    d.text((S(170), S(100)), f": {nik}", fill=(10, 10, 10), font=font(S(32), True))
    fields = [("Nama", name(rng)), ("Tempat/Tgl Lahir", f"{rng.choice(PLACES)}, {date(rng)}"),
              ("Jenis Kelamin", "LAKI-LAKI"), ("Alamat", f"JL. {name(rng, 1)} {rng.integers(1, 99)}"),
              ("RT/RW", f"{rng.integers(1, 20):03d}/{rng.integers(1, 15):03d}"), ("Kel/Desa", name(rng, 1)),
              ("Kecamatan", name(rng, 1)), ("Agama", str(rng.choice(RELIGION))),
              ("Status Perkawinan", "KAWIN"), ("Pekerjaan", str(rng.choice(JOB))),
              ("Kewarganegaraan", "WNI"), ("Berlaku Hingga", "SEUMUR HIDUP")]
    for i, (k, v) in enumerate(fields):
        y = S(150 + i * 37)
        d.text((S(40), y), k, fill=(10, 10, 10), font=font(S(22)))
        d.text((S(270), y), f": {v}", fill=(10, 10, 10), font=font(S(22)))
        tokens.extend(v.replace(",", "").split())
    d.rectangle([S(770), S(150), S(960), S(400)], fill=(150, 170, 190))
    d.text((S(800), S(520)), date(rng, 2015, 2025), fill=(10, 10, 10), font=font(S(20)))
    tokens.append(nik)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR), tokens


def photograph(doc, seed, out_w=2000, out_h=1500, fill=0.86, jitter=0.02):
    """Place a document on a textured background with mild perspective and lighting."""
    rng = np.random.default_rng(seed + 20_000)
    base = rng.integers(60, 140, 3).astype(np.float32)
    bg = np.ones((out_h, out_w, 3), np.float32) * base
    bg += cv2.GaussianBlur(rng.normal(0, 18, (out_h, out_w)).astype(np.float32), (0, 0), 6)[..., None]
    h, w = doc.shape[:2]
    s = fill * min(out_w / w, out_h / h)
    dw, dh = w * s, h * s
    cx, cy = out_w / 2 + rng.uniform(-0.03, 0.03) * out_w, out_h / 2 + rng.uniform(-0.03, 0.03) * out_h
    dst = np.float32([[cx - dw / 2, cy - dh / 2], [cx + dw / 2, cy - dh / 2],
                      [cx + dw / 2, cy + dh / 2], [cx - dw / 2, cy + dh / 2]])
    dst += rng.uniform(-jitter, jitter, (4, 2)).astype(np.float32) * np.float32([dw, dh])
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    m = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(doc.astype(np.float32), m, (out_w, out_h))
    mask = cv2.warpPerspective(np.ones((h, w), np.float32), m, (out_w, out_h))[..., None]
    shadow = cv2.GaussianBlur(np.roll(mask[..., 0], (12, 12), (0, 1)), (0, 0), 10)[..., None]
    img = bg * (1 - 0.35 * shadow * (1 - mask)) * (1 - mask) + warped * mask
    yy, xx = np.mgrid[0:out_h, 0:out_w].astype(np.float32)
    ang = rng.uniform(0, 2 * np.pi)
    grad = 1 + 0.06 * ((xx / out_w - 0.5) * np.cos(ang) + (yy / out_h - 0.5) * np.sin(ang))
    img = img * grad[..., None] + rng.normal(0, 2.0, img.shape)
    img = np.clip(img, 0, 255).astype(np.uint8)
    return jpeg(img, 92)


def jpeg(img, quality):
    """Round-trip through JPEG at the given quality."""
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def doc_mask(photo_seed, doc, out_w=2000, out_h=1500, fill=0.86, jitter=0.02):
    """Binary mask of where photograph() placed the document (same RNG draws)."""
    rng = np.random.default_rng(photo_seed + 20_000)
    rng.integers(60, 140, 3)
    rng.normal(0, 18, (out_h, out_w))
    h, w = doc.shape[:2]
    s = fill * min(out_w / w, out_h / h)
    dw, dh = w * s, h * s
    cx, cy = out_w / 2 + rng.uniform(-0.03, 0.03) * out_w, out_h / 2 + rng.uniform(-0.03, 0.03) * out_h
    dst = np.float32([[cx - dw / 2, cy - dh / 2], [cx + dw / 2, cy - dh / 2],
                      [cx + dw / 2, cy + dh / 2], [cx - dw / 2, cy + dh / 2]])
    dst += rng.uniform(-jitter, jitter, (4, 2)).astype(np.float32) * np.float32([dw, dh])
    mask = np.zeros((out_h, out_w), np.uint8)
    cv2.fillConvexPoly(mask, dst.astype(np.int32), 1)
    return mask, dst


def gaussian_blur(img, sigma):
    return img if sigma <= 0 else cv2.GaussianBlur(img, (0, 0), sigma)


def motion_blur(img, length, angle_deg):
    """Linear motion blur with a line kernel of the given length and angle."""
    if length <= 1:
        return img
    k = np.zeros((length, length), np.float32)
    k[length // 2, :] = 1
    rot = cv2.getRotationMatrix2D((length / 2 - 0.5, length / 2 - 0.5), angle_deg, 1.0)
    k = cv2.warpAffine(k, rot, (length, length))
    return cv2.filter2D(img, -1, k / k.sum())


def glare(img, mask, rng, radius_frac, intensity):
    """Specular flash spot: Gaussian highlight with a clipped (saturated) core inside the document."""
    if radius_frac <= 0:
        return img
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = np.percentile(xs, 20), np.percentile(xs, 80), np.percentile(ys, 20), np.percentile(ys, 80)
    cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
    short = min(xs.max() - xs.min(), ys.max() - ys.min())
    r = radius_frac * short
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]].astype(np.float32)
    aspect = rng.uniform(0.6, 1.0)
    d2 = ((xx - cx) / r) ** 2 + ((yy - cy) / (r * aspect)) ** 2
    bump = np.clip(1.6 * np.exp(-d2 * 1.4), 0, 1)
    out = img.astype(np.float32) + intensity * 255 * bump[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def low_light(img, scale, rng):
    """Darker exposure with matching shot noise."""
    out = img.astype(np.float32) * scale
    out += rng.normal(0, 3.0 / max(scale, 0.1), out.shape)
    return np.clip(out, 0, 255).astype(np.uint8)


def noise(img, sigma, rng):
    return np.clip(img.astype(np.float32) + rng.normal(0, sigma, img.shape), 0, 255).astype(np.uint8)


def skew(img, angle_deg):
    """Small in-plane rotation that keeps the whole frame (reflected border)."""
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle_deg, 1.0)
    return cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REFLECT)
