# Datasheet: kk-warps

**Purpose.** Fictional KK pages warped by known 3D surfaces, each with exact ground-truth maps. Use them to evaluate document dewarping (rectification) by pixel error, not only by visual judgement. Built for the paper "Dewarping Photographed Indonesian Identity Documents Before OCR".

**Composition.**
- Each flat page (1200 x 800) is placed on one of four surface families:
  - `perspective`: a plane under tilt;
  - `curl`: a cylinder-like bend;
  - `fold`: a crease;
  - `mesh`: a smooth random field.
- Strength runs from 0 (flat) to 1 (strong).
- The page is projected by a pinhole camera and framed like a padded crop.
- Backgrounds: `table`, `white`, `white_textured`, `clutter`.
- Default run: 2 pages x 4 families x 3 strengths, on a table background.
- Sample: 1 page x 4 families at strength 1.0.

**Files per page.**
- `flat.png`: the ground truth.
- `<family>_<strength>_<background>.jpg`: the warped frame.
- `..._maps.npz`, holding:
  - `inv_u`, `inv_v`: the flat x and y of each warped pixel, i.e. the backward map a dewarper should predict;
  - `fx`, `fy`: the warped x and y of each flat pixel;
  - `corners`: the warped positions of the flat TL, TR, BR and BL corners.
  - Maps are int16 in 1/16-pixel units; divide by `scale` (16). Maximum quantisation error is 1/32 px.
- `labels.csv`: lists every sample.

**Generation.**
- Code: `generator/synth.py`, `generator/make.py`.
- The forward map is analytic; the backward map is its numerical inverse on an extended grid.
- Photometric shading and noise are added to the warped frame only.
- Regenerate with `python make.py out --levels 0.4 0.8 1.0 --backgrounds table white`.

**Known limits.**
- Smooth analytic surfaces only. Real crumples, tears and multi-fold creases are absent.
- Text and fonts are simplified.
- The camera has no lens distortion.

**Licence.** MIT (see `LICENSE` at the repository root).
