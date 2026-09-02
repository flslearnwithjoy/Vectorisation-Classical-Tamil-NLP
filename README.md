# Reproducibility materials

This directory contains source code and documentation for the experiments in
the paper. It deliberately does **not** contain the original source texts,
their extracted JSONL records, trained weights, or executed notebook outputs.

## Contents

- `notebooks/`: output-stripped source notebooks for the reported v3 controls,
  representation analysis, Siamese matching, encoder--decoder, and
  decoder-only grammar-probe experiments.
- `scripts/parse_naaladiyar_pm.py`: parser for the locally obtained Project
  Madurai Naaladiyar Unicode text.
- `scripts/parse_thirukadukam_tamilvu.py`: rate-limited parser for the
  Thirukadukam Tamil Virtual University verse and urai pages.
- `data/`: source attribution, Project Madurai header-preservation notice, and
  the Tamil Virtual University academic-use permission note.

The encoder--decoder values reported in the paper come from the executed Kaggle
run. The notebook included here is source-only, so it can be inspected and
rerun after the user has independently obtained the source texts and prepared
the same JSONL schema (`verse`, `urai`, and `dataset`).

## Data access and redistribution

`data/SOURCES.md` records the direct source pages, what each parser can
reproduce, and the manual collection boundary for Tholkappiyam. Obtain source
texts directly from Project Madurai and the Tamil Virtual University, and check
their current terms before downloading, extracting, or redistributing material.
In particular, do not treat this repository as a redistribution of either
source corpus. See `data/HEADER.txt` for the required credit notice. The
Tholkappiyam material was manually collected from the Tamil Virtual University
rather than fetched with an automated crawler.
