# Datasheet: kk-word-boxes

**Purpose.** Fictional Indonesian family cards (Kartu Keluarga, KK) given as OCR-like word boxes with full ground truth, plus rendered page images. Use them to test KK field extractors without real documents. Built for the paper "Reading the Indonesian Family Card from Word Boxes: A Line-and-Column Extractor".

**Composition.** Every document is generated once per scenario from the same family, so the scenarios are paired:
- `clean`
- `skew`
- `jitter`
- `merged`: neighbouring cells merged into one word box
- `split`: words split in two
- `missing_anchor`
- `typos`: OCR confusions
- `wrap`: wrapped long values
- `empty`: empty cells
- `combined`

The default run has 40 families x 10 scenarios = 400 documents. The sample has 49 documents.

**Fields.**
- `docs.jsonl` has one document per line:
  - `words`: `text`; `quad`, four integer vertices TL, TR, BR, BL; `conf`; and `tag`, the field each word belongs to;
  - `angle`;
  - `truth.header`: KK number, head of family, address, RT/RW, postcode, village, district, regency, province, issue date;
  - `truth.members`: one row per member with name, NIK, sex, place and date of birth, religion, education, occupation, marital status, relationship, nationality, father, mother.
- `images/` and `images.csv` hold rendered pages with table rules for the first clean documents. They are blurred at sigma {0, 1, 2, 3} and rotated by {0, 1, 2, 5, 10} degrees, saved as JPEG at quality 90. Each row includes the 2x3 rotation matrix that maps page coordinates into the image.

**Generation.**
- `generator/synth_kk.py` and `generator/render_kk.py`, seeded with `random.Random`.
- Names are joined from random syllables.
- NIKs follow the 16-digit structure (region code, birth date with +40 for women, serial) with random serials.
- Regenerate with `python make.py out --per-scenario 40 --images 2`.

**Known limits.**
- The layout is a simplified KK. Real cards have more columns, stamps, signatures, QR codes and printed backgrounds.
- The rendered font (OpenCV Hershey) is not the official one.
- Generated NIKs and names can coincide with real ones by chance. The sample was screened against a private reference list and one document was removed.

**Licence.** MIT (see `LICENSE` at the repository root).
