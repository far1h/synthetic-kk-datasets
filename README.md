# Synthetic Kartu Keluarga (KK) Datasets

Three seeded synthetic datasets for testing OCR, capture-quality checks and dewarping on Indonesian family cards (Kartu Keluarga, KK) without real documents. Every name and number is fictional, and no real image was used.

| Dataset | What it contains | Sample |
|---|---|---|
| `kk-word-boxes` | KK documents as OCR word boxes with full ground truth, plus rendered pages | 49 documents, 4 images |
| `kk-photos` | Photos of KK-like and ID-card-like layouts with capture defects (blur, glare, low light, rotation) | 22 images |
| `kk-warps` | Warped KK pages with exact forward and backward maps for dewarping | 4 warps |

## File structure

```
datasets/<name>/
  DATASHEET.md     purpose, composition, labels, generation, limits
  generator/       seeded generator scripts (run from this folder)
  sample/          small committed sample
scripts/
  make_samples.sh      regenerate every sample
  check_fictional.py   scan outputs against private lists of real names, IDs and institutions
requirements.txt
LICENSE
```

## Regenerate

```
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
PY=$PWD/.venv/bin/python scripts/make_samples.sh
```

Each `DATASHEET.md` gives the command for the full-size set. Generators are deterministic for a given seed.

## Privacy screen

Names are built from common Indonesian names or random syllables, and NIK-like numbers follow the 16-digit structure but are random, so a value can match a real person by chance. Every committed sample was scanned with `scripts/check_fictional.py` against private lists kept outside this repository; matching records were removed, and each datasheet gives the count.

## Licence

MIT, see `LICENSE`.
