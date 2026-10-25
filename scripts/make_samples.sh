#!/usr/bin/env bash
# Regenerate every committed sample from its generator (run from the repository root).
# The committed samples were then screened against a private list of real names,
# identity numbers and institution names; records that matched by coincidence were removed
# (see each DATASHEET.md), so a fresh run can contain a few more records than the sample.
set -euo pipefail
PY=${PY:-python}
cd datasets/kk-word-boxes/generator && $PY make.py ../sample --per-scenario 5 --images 1 --sigmas 0 2 --angles 0 5 && cd -
cd datasets/kk-photos/generator && $PY make.py ../sample --seeds 1 --doc-types kk --quality 80 && cd -
cd datasets/kk-warps/generator && $PY make.py ../sample --seeds 1 --levels 1.0 && cd -
