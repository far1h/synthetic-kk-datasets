"""Seeded synthetic Kartu Keluarga (KK) generator that emits OCR-like word boxes.

Every person, NIK, address and official in the output is fictional. Words are emitted in
reading order with integer quadrilateral vertices (TL, TR, BR, BL), like a word-level OCR
response, so they can be fed into the extractor through its own OCRDoc/OCRWord classes.
"""

import json
import math
import random
from dataclasses import dataclass, field

W, H = 2400, 1700
TH = 22            # table text height (px)
HH = 26            # header block text height (px)
CW = 0.55          # character width as a fraction of text height
PITCH = 1.45       # member row pitch in text heights

SCENARIOS = ["clean", "skew", "jitter", "merged", "split", "missing_anchor",
             "typos", "wrap", "empty", "combined"]

SYL = ["BU", "DI", "SAN", "TO", "SO", "RA", "NI", "WA", "TI", "AN", "DA", "RI", "YAN", "TO",
       "MAR", "LI", "NA", "SU", "KAR", "NO", "HAR", "JA", "DE", "WI", "YU", "LIA", "FA", "ZA",
       "GA", "LUH", "PU", "TRA", "SEP", "TIA", "MEL", "ATI", "IR", "MA", "KUS", "NUR", "HA"]
PROVINCES = [("11", "ACEH"), ("12", "SUMATERA UTARA"), ("13", "SUMATERA BARAT"), ("31", "DKI JAKARTA"),
             ("32", "JAWA BARAT"), ("33", "JAWA TENGAH"), ("34", "DI YOGYAKARTA"), ("35", "JAWA TIMUR"),
             ("36", "BANTEN"), ("51", "BALI"), ("61", "KALIMANTAN BARAT"), ("73", "SULAWESI SELATAN")]
CITIES = ["JAKARTA", "BANDUNG", "SURABAYA", "MEDAN", "SEMARANG", "MAKASSAR", "PALEMBANG", "BOGOR",
          "DEPOK", "TANGERANG", "BEKASI", "MALANG", "YOGYAKARTA", "SOLO", "DENPASAR", "PADANG",
          "PONTIANAK", "CIREBON", "TASIKMALAYA", "KEDIRI", "BANDA ACEH", "PEKALONGAN"]
AGAMA = ["ISLAM"] * 6 + ["KRISTEN", "KATOLIK", "HINDU", "BUDDHA", "KONGHUCU"]
PENDIDIKAN = ["TIDAK/BELUM SEKOLAH", "BELUM TAMAT SD/SEDERAJAT", "TAMAT SD/SEDERAJAT",
              "SLTP/SEDERAJAT", "SLTA/SEDERAJAT", "DIPLOMA I/II", "AKADEMI/DIPLOMA III/S. MUDA",
              "DIPLOMA IV/STRATA I", "STRATA II", "STRATA III"]
PEKERJAAN = ["WIRASWASTA", "PELAJAR/MAHASISWA", "MENGURUS RUMAH TANGGA", "BELUM/TIDAK BEKERJA",
             "KARYAWAN SWASTA", "PETANI/PEKEBUN", "PEGAWAI NEGERI SIPIL (PNS)", "GURU", "PEDAGANG",
             "BURUH HARIAN LEPAS", "SOPIR", "PENSIUNAN", "NELAYAN/PERIKANAN", "PERDAGANGAN"]
GOLDAR = ["TIDAK TAHU", "TIDAK TAHU", "A", "B", "O", "AB"]
STREETS = ["MAWAR", "MELATI", "KENANGA", "CEMPAKA", "ANGGREK", "FLAMBOYAN", "TERATAI", "DAHLIA"]
TYPO = {"I": "1", "O": "0", "S": "5", "B": "8", "E": "F", "A": "4", "L": "I", "N": "H",
        "0": "O", "1": "I", "5": "S", "8": "B", "U": "V", "G": "6"}


@dataclass
class Word:
    """One OCR word: text and an axis-aligned box before global perturbation."""
    text: str
    x: float
    y: float
    w: float
    h: float
    tag: str = ""                 # semantic tag used only by the figures

    def quad(self):
        """Return TL, TR, BR, BL vertices."""
        return [[self.x, self.y], [self.x + self.w, self.y],
                [self.x + self.w, self.y + self.h], [self.x, self.y + self.h]]


@dataclass
class Doc:
    """A synthetic KK with its words, ground truth and layout metadata."""
    words: list = field(default_factory=list)
    truth: dict = field(default_factory=dict)
    layout: dict = field(default_factory=dict)


def name(rng, parts=(2, 3)):
    """Fictional upper-case personal name built from syllables."""
    def one():
        return "".join(rng.choice(SYL) for _ in range(rng.choice([2, 2, 3])))
    return " ".join(one() for _ in range(rng.randint(*parts)))


def place(rng):
    """Fictional place name (kelurahan, kecamatan, kabupaten)."""
    return "".join(rng.choice(SYL) for _ in range(rng.choice([2, 3, 3])))


def nik(region, birth, female, rng):
    """Well-formed but fictional 16-digit NIK: region(6) + DDMMYY (+40 day if female) + serial(4)."""
    d, m, y = birth
    return f"{region}{d + (40 if female else 0):02d}{m:02d}{y % 100:02d}{rng.randint(1, 999):04d}"


def phrase(text, x, y, h, tag="", gap=1.0, rng=None):
    """Split a phrase into word boxes separated by about one space."""
    out, cx = [], x
    for tok in text.split(" "):
        if not tok:
            continue
        w = len(tok) * CW * h
        out.append(Word(tok, cx, y, w, h, tag))
        cx += w + gap * CW * h
    return out


def centered(text, x0, x1, y, h, tag=""):
    """Phrase centred between x0 and x1."""
    width = len(text) * CW * h
    return phrase(text, (x0 + x1) / 2 - width / 2, y, h, tag)


def columns(spec, x=60, sep=10):
    """Consecutive (label, x0, x1) table columns from (label, width) pairs."""
    out = []
    for label, width in spec:
        out.append((label, x, x + width))
        x += width + sep
    return out


T1 = columns([("No", 50), ("Nama Lengkap", 400), ("NIK", 230), ("Jenis Kelamin", 170), ("Tempat Lahir", 190),
              ("Tanggal Lahir", 165), ("Agama", 130), ("Pendidikan", 365), ("Jenis Pekerjaan", 355),
              ("Golongan Darah", 175)])
T2 = columns([("No", 50), ("Status Perkawinan", 290), ("Tanggal Perkawinan", 220), ("Status Hubungan", 240),
              ("Kewarganegaraan", 220), ("No. Paspor", 160), ("No. KITAP", 160), ("Ayah", 420), ("Ibu", 420)])
T1_Y, T2_Y = 400, 930


def make_truth(rng):
    """Draw a fictional family and the header fields."""
    pcode, prov = rng.choice(PROVINCES)
    region = f"{pcode}{rng.randint(1, 79):02d}{rng.randint(1, 40):02d}"
    issued = (rng.randint(1, 28), rng.randint(1, 12), rng.randint(2015, 2025))
    head_birth = (rng.randint(1, 28), rng.randint(1, 12), rng.randint(1955, 1990))
    n = rng.choice([1, 2, 3, 3, 4, 4, 4, 5, 5, 6, 7, 8])
    father_head, mother_head = name(rng), name(rng)
    spouse = n >= 2 and rng.random() < 0.85
    head = {"female": rng.random() < 0.12, "birth": head_birth, "rel": "KEPALA KELUARGA",
            "ayah": father_head, "ibu": mother_head}
    members = [head]
    if spouse:
        members.append({"female": not head["female"], "rel": "ISTRI" if not head["female"] else "SUAMI",
                        "birth": (rng.randint(1, 28), rng.randint(1, 12), head_birth[2] + rng.randint(-3, 6)),
                        "ayah": name(rng), "ibu": name(rng)})
    while len(members) < n:
        rel = rng.choice(["ANAK"] * 6 + ["FAMILI LAIN", "MERTUA", "CUCU"])
        by = head_birth[2] + rng.randint(20, 32) if rel != "MERTUA" else head_birth[2] - rng.randint(20, 30)
        by = min(by, 2024)
        members.append({"female": rng.random() < 0.5, "rel": rel,
                        "birth": (rng.randint(1, 28), rng.randint(1, 12), by), "ayah": None, "ibu": None})
    surname = name(rng, (1, 1))
    for m in members:
        m["nama"] = name(rng, (1, 2)) + " " + surname if m["rel"] == "ANAK" else name(rng)
    for m in members:
        if m["rel"] in ("ANAK", "CUCU"):
            dad = members[0] if not members[0]["female"] else (members[1] if spouse else None)
            mom = members[1] if spouse and not members[0]["female"] else members[0]
            m["ayah"] = dad["nama"] if dad else name(rng)
            m["ibu"] = mom["nama"]
        elif m["ayah"] is None:
            m["ayah"], m["ibu"] = name(rng), name(rng)
    rows = []
    for m in members:
        d, mo, y = m["birth"]
        age = issued[2] - y
        edu = rng.choice(PENDIDIKAN[3:]) if age > 22 else rng.choice(PENDIDIKAN[:5])
        job = rng.choice(PEKERJAAN) if age > 22 else rng.choice(["PELAJAR/MAHASISWA", "BELUM/TIDAK BEKERJA"])
        if m["rel"] in ("ISTRI",) and rng.random() < 0.5:
            job = "MENGURUS RUMAH TANGGA"
        kawin = "KAWIN" if m["rel"] in ("KEPALA KELUARGA", "ISTRI", "SUAMI") and spouse else (
            "BELUM KAWIN" if age < 25 else rng.choice(["BELUM KAWIN", "KAWIN", "CERAI HIDUP", "CERAI MATI"]))
        if kawin == "KAWIN" and rng.random() < 0.4:
            kawin = rng.choice(["KAWIN TERCATAT", "KAWIN BELUM TERCATAT"])
        rows.append({
            "NAMA": m["nama"], "NIK": nik(region, m["birth"], m["female"], rng),
            "JENIS_KELAMIN": "PEREMPUAN" if m["female"] else "LAKI-LAKI",
            "TEMPAT_LAHIR": rng.choice(CITIES), "TGL_LAHIR": f"{d:02d}-{mo:02d}-{y}",
            "AGAMA": rng.choice(AGAMA), "PENDIDIKAN": edu, "PEKERJAAN": job,
            "GOLDAR": rng.choice(GOLDAR), "STATUS_PERKAWINAN": kawin,
            "TGL_KAWIN": "-" if "KAWIN" not in kawin or kawin == "BELUM KAWIN" else
            f"{rng.randint(1, 28):02d}-{rng.randint(1, 12):02d}-{min(issued[2], y + rng.randint(20, 30))}",
            "STATUS_HUBUNGAN": m["rel"], "KEWARGANEGARAAN": "WNI" if rng.random() < 0.97 else "WNA",
            "AYAH": m["ayah"], "IBU": m["ibu"]})
    street = f"JL. {rng.choice(STREETS)} {place(rng)} NO. {rng.randint(1, 120)}"
    header = {
        "NOMOR_KK": f"{region}{issued[0]:02d}{issued[1]:02d}{issued[2] % 100:02d}{rng.randint(1, 9999):04d}",
        "NAMA": rows[0]["NAMA"], "ALAMAT": street,
        "RT_RW": f"{rng.randint(1, 20):03d}/{rng.randint(1, 15):03d}",
        "KODE_POS": f"{rng.randint(10000, 99999)}", "KEL_DESA_KELURAHAN": place(rng),
        "KECAMATAN": place(rng), "KABUPATEN_KOTA": rng.choice(["KOTA ", "KABUPATEN "]) + place(rng),
        "PROVINSI": prov, "DIKELUARKAN_TANGGAL": f"{issued[0]:02d}-{issued[1]:02d}-{issued[2]}"}
    return header, rows


def label_value(label, value, x, xc, y, h, tag):
    """Label, colon and value as on the KK header block."""
    return (phrase(label, x, y, h, "key") + phrase(":", xc, y, h, "colon") +
            phrase(value, xc + 1.4 * CW * h, y, h, tag))


def build_words(header, rows, rng, wrap=False):
    """Lay out the KK in reading order and return the word list."""
    words = []
    words += centered("KARTU KELUARGA", 0, W, 70, 44, "title")
    words += centered("No. " + header["NOMOR_KK"], 0, W, 130, 32, "NOMOR_KK")
    left = [("Nama Kepala Keluarga", "NAMA"), ("Alamat", "ALAMAT"), ("RT/RW", "RT_RW"),
            ("Desa/Kelurahan", "KEL_DESA_KELURAHAN")]
    right = [("Kecamatan", "KECAMATAN"), ("Kabupaten/Kota", "KABUPATEN_KOTA"), ("Kode Pos", "KODE_POS"),
             ("Provinsi", "PROVINSI")]
    for i in range(4):
        y = 205 + i * 42
        words += label_value(left[i][0], header[left[i][1]], 80, 460, y, HH, left[i][1])
        words += label_value(right[i][0], header[right[i][1]], 1380, 1640, y, HH, right[i][1])
    for lab, x0, x1 in T1:
        words += centered(lab, x0, x1, T1_Y, TH, "colkey")
    for i, (_, x0, x1) in enumerate(T1[1:], start=1):
        words += centered(f"({i})", x0, x1, T1_Y + 1.6 * TH, TH, "colnum")
    keys1 = ["NAMA", "NIK", "JENIS_KELAMIN", "TEMPAT_LAHIR", "TGL_LAHIR", "AGAMA", "PENDIDIKAN",
             "PEKERJAAN", "GOLDAR"]
    y0 = T1_Y + 3.4 * TH
    for r, row in enumerate(rows):
        y = y0 + r * PITCH * TH
        words += phrase(str(r + 1), 85, y, TH, "rownum")
        for k, (_, x0, x1) in zip(keys1, T1[1:]):
            text = row[k]
            if k == "NAMA":
                if wrap and len(text) > 22:
                    cut = text.rfind(" ", 0, 22)
                    words += phrase(text[:cut], x0 + 6, y - 0.28 * TH, TH * 0.72, "NAMA")
                    words += phrase(text[cut + 1:], x0 + 6, y + 0.48 * TH, TH * 0.72, "NAMA")
                    continue
                words += phrase(text, x0 + 6, y, TH, k)
            else:
                words += centered(text, x0, x1, y, TH, k)
    for lab, x0, x1 in T2:
        if lab in ("No. Paspor", "No. KITAP", "Ayah", "Ibu"):
            continue
        words += centered(lab, x0, x1, T2_Y, TH, "colkey")
    words += centered("Dokumen Imigrasi", T2[5][1], T2[6][2], T2_Y, TH, "colkey")
    words += centered("Nama Orang Tua", T2[7][1], T2[8][2], T2_Y, TH, "colkey")
    for lab, x0, x1 in T2:
        if lab == "Status Hubungan":
            words += centered("Dalam Keluarga", x0, x1, T2_Y + 1.4 * TH, TH, "colkey")
        if lab in ("No. Paspor", "No. KITAP", "Ayah", "Ibu"):
            words += centered(lab, x0, x1, T2_Y + 1.4 * TH, TH, "colkey")
    for i, (_, x0, x1) in enumerate(T2[1:], start=10):
        words += centered(f"({i})", x0, x1, T2_Y + 2.8 * TH, TH, "colnum")
    keys2 = ["STATUS_PERKAWINAN", "TGL_KAWIN", "STATUS_HUBUNGAN", "KEWARGANEGARAAN", "PASPOR", "KITAP",
             "AYAH", "IBU"]
    y0 = T2_Y + 4.6 * TH
    for r, row in enumerate(rows):
        y = y0 + r * PITCH * TH
        words += phrase(str(r + 1), 85, y, TH, "rownum")
        for k, (_, x0, x1) in zip(keys2, T2[1:]):
            text = row.get(k, "-")
            if text:
                words += centered(text, x0, x1, y, TH, k) if k not in ("AYAH", "IBU") else \
                    phrase(text, x0 + 6, y, TH, k)
    fy = 1450
    words += label_value("Dikeluarkan Tanggal", header["DIKELUARKAN_TANGGAL"], 80, 400, fy, HH,
                         "DIKELUARKAN_TANGGAL")
    for i, lab in enumerate(["Kepala Keluarga", "RT", "Desa/Kelurahan", "Kecamatan"]):
        words += phrase(f"LEMBAR {i + 1} : {lab}", 80, fy + 44 + i * 32, 22, "footer")
    words += centered("KEPALA KELUARGA", 900, 1400, fy, 24, "footer")
    words += centered(rows[0]["NAMA"], 900, 1400, fy + 170, 24, "footer")
    words += centered("KEPALA DINAS KEPENDUDUKAN DAN", 1500, 2350, fy, 22, "footer")
    words += centered("PENCATATAN SIPIL " + header["KABUPATEN_KOTA"], 1500, 2350, fy + 30, 22, "footer")
    words += centered(name(rng), 1500, 2350, fy + 200, 22, "footer")
    return words


def typo(text, rng, p):
    """Apply OCR-like character confusions with probability p per character."""
    return "".join(TYPO[c] if c in TYPO and rng.random() < p else c for c in text)


def perturb(words, scenario, rng):
    """Apply one perturbation family (or a mild mix for 'combined') to the word list."""
    out = [Word(w.text, w.x, w.y, w.w, w.h, w.tag) for w in words]
    mix = scenario == "combined"
    value_tags = {"NAMA", "NIK", "TEMPAT_LAHIR", "AGAMA", "PENDIDIKAN", "PEKERJAAN", "AYAH", "IBU",
                  "STATUS_PERKAWINAN", "STATUS_HUBUNGAN", "ALAMAT", "KECAMATAN", "KEL_DESA_KELURAHAN"}
    if scenario == "jitter" or mix:
        s = 0.18 if not mix else 0.08
        for w in out:
            w.y += rng.gauss(0, s * w.h)
            w.x += rng.gauss(0, s * w.h)
    if scenario == "typos" or mix:
        p = 0.05 if not mix else 0.02
        for w in out:
            if w.tag in value_tags or (w.tag == "key" and rng.random() < 0.3) or w.tag == "colkey":
                w.text = typo(w.text, rng, p if w.tag in value_tags else p / 2)
    if scenario == "missing_anchor" or mix:
        keys = [w for w in out if w.tag in ("key", "colkey")]
        k = rng.choice(keys)
        group = [w for w in keys if abs(w.y - k.y) < 2 and abs(w.x - k.x) < 400 and w.tag == k.tag]
        drop = {id(g) for g in group}
        out = [w for w in out if id(w) not in drop]
    if scenario == "merged" or mix:
        out = merge_cells(out, rng, 0.35 if not mix else 0.12)
    if scenario == "split" or mix:
        out = split_words(out, rng, 0.25 if not mix else 0.08)
    if scenario == "skew" or mix:
        ang = rng.uniform(0.6, 2.5) * rng.choice([-1, 1]) if not mix else rng.uniform(-1.0, 1.0)
        return out, ang
    return out, 0.0


def merge_cells(words, rng, p):
    """Fuse horizontally adjacent table cells into one OCR word (e.g. date and religion)."""
    pairs = [("TGL_LAHIR", "AGAMA"), ("JENIS_KELAMIN", "TEMPAT_LAHIR"), ("STATUS_HUBUNGAN", "KEWARGANEGARAAN"),
             ("PENDIDIKAN", "PEKERJAAN"), ("STATUS_PERKAWINAN", "TGL_KAWIN")]
    out = list(words)
    for a, b in pairs:
        rows = {}
        for w in out:
            if w.tag in (a, b):
                rows.setdefault(round(w.y / 10), []).append(w)
        for ws in rows.values():
            wa = [w for w in ws if w.tag == a]
            wb = [w for w in ws if w.tag == b]
            if wa and wb and rng.random() < p:
                last, first = wa[-1], wb[0]
                fused = Word(last.text + " " + first.text, last.x, last.y, first.x + first.w - last.x,
                             last.h, a)
                out = [fused if w is last else w for w in out if w is not first]
    return out


def split_words(words, rng, p):
    """Split long value tokens into two OCR words with a sub-space gap."""
    out = []
    for w in words:
        if len(w.text) >= 6 and w.tag not in ("key", "colkey", "colnum", "rownum", "title") and rng.random() < p:
            cut = rng.randint(2, len(w.text) - 2)
            cw = w.w / len(w.text)
            gap = rng.uniform(0.05, 0.35) * cw
            out.append(Word(w.text[:cut], w.x, w.y, cut * cw, w.h, w.tag))
            out.append(Word(w.text[cut:], w.x + cut * cw + gap, w.y, (len(w.text) - cut) * cw, w.h, w.tag))
        else:
            out.append(w)
    return out


def empty_cells(rows, rng, p):
    """Blank some optional cells; ground truth becomes empty."""
    for r in rows:
        for k in ("PEKERJAAN", "AYAH", "IBU", "PENDIDIKAN"):
            if rng.random() < p:
                r[k] = "-" if rng.random() < 0.6 else ""
    return rows


def rotate(words, ang):
    """Rotate every box about the page centre and return integer quads."""
    a = math.radians(ang)
    cx, cy = W / 2, H / 2
    quads = []
    for w in words:
        q = []
        for x, y in w.quad():
            dx, dy = x - cx, y - cy
            q.append([round(cx + dx * math.cos(a) - dy * math.sin(a)), round(cy + dx * math.sin(a) + dy * math.cos(a))])
        quads.append(q)
    return quads


def generate(seed, scenario):
    """Generate one document dictionary for a seed and scenario."""
    rng = random.Random(seed)
    header, rows = make_truth(rng)
    prng = random.Random(seed * 7919 + SCENARIOS.index(scenario))
    if scenario in ("empty", "combined"):
        rows = empty_cells(rows, prng, 0.25 if scenario == "empty" else 0.1)
    words = build_words(header, rows, prng, wrap=scenario in ("wrap", "combined"))
    words, ang = perturb(words, scenario, prng)
    quads = rotate(words, ang)
    truth_rows = [{k: v for k, v in r.items() if k not in ("GOLDAR", "TGL_KAWIN")} for r in rows]
    return {"id": f"{scenario}-{seed}", "seed": seed, "scenario": scenario, "width": W, "height": H,
            "angle": ang, "words": [{"text": w.text, "quad": q, "conf": 0.98, "tag": w.tag}
                                     for w, q in zip(words, quads)],
            "truth": {"header": header, "members": truth_rows}}


def dataset(n_per_scenario, base_seed=20261020):
    """All scenarios share the same base families (paired design)."""
    return [generate(base_seed + i, s) for s in SCENARIOS for i in range(n_per_scenario)]


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    path = sys.argv[2] if len(sys.argv) > 2 else "synthetic_kk.jsonl"
    with open(path, "w") as f:
        for d in dataset(n):
            f.write(json.dumps(d) + "\n")
    print(path)
