# Datasheet: kk-photos

**Purpose.** Synthetic photographs of fictional family-card (KK) and ID-card layouts, clean and with controlled capture defects. They are for testing capture-quality gates (blur, glare, low light, noise, compression, perspective, orientation) before OCR. Built for the paper "A Lightweight Capture-Quality Gate for Photographed Indonesian Identity Documents".

**Composition.** Per seed and document type there are 22 conditions:
- clean;
- Gaussian blur, sigma 1, 2 and 4;
- motion blur, 9 and 25 px;
- glare spots on the document, given as (radius as a fraction of the document, intensity): (0.06, 0.7), (0.15, 1.0) and (0.3, 1.0);
- JPEG quality 20 and 5;
- low light, x0.4 and x0.15;
- sensor noise, sigma 20 and 45;
- perspective jitter, 0.08 and 0.16;
- quarter turns `rot90` k = 1, 2, 3 (counter-clockwise);
- skew, -7 and 12 degrees.

Each photo places the card on a textured background with mild lighting. The default run has 3 seeds x 2 document types (132 images, JPEG quality 95). The sample has 1 seed, KK only, at JPEG quality 80, 22 images.

**Labels.** `labels.csv` has these columns:
- `file`
- `mask`: a binary PNG of the document region, rotated with the image for `rot90`
- `doc_type`
- `seed`
- `condition`
- `param`
- `param2`
- `truth_tokens`: the printed value strings, for OCR scoring

**Generation.** The code is in `generator/synth.py` and `generator/make.py`. Everything uses seeded NumPy, names and numbers come from syllable and digit tables, and the font is DejaVu Sans. To regenerate, run `python make.py out --seeds 3`.

**Known limits.**
- The layouts are KK-like and ID-card-like, not official designs.
- Glare is a smooth synthetic highlight. Real flash glare on glossy or laminated cards has sharper edges and colour shifts.
- Backgrounds are darker than a white desk. White-on-white scenes are not in this set; `kk-warps` has white backgrounds.

**Licence.** MIT (see `LICENSE` at the repository root).
