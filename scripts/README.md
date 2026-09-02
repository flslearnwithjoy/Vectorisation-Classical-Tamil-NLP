# Parsing and figure scripts

`parse_naaladiyar_pm.py` parses a locally obtained copy of the Project Madurai
Naaladiyar Unicode edition into verse--urai JSONL records. Preserve the
Project Madurai header with any local copy of the source text.

`parse_thirukadukam_tamilvu.py` obtains the Thirukadukam verse and linked urai
pages from Tamil Virtual University. It is deliberately rate-limited, caches
responses, and does not include cached pages in this repository.

No automated Tholkappiyam parser is supplied: the three Tholkappiyam components
in v3 were manually collected from Tamil Virtual University. See
`../data/SOURCES.md` for exact landing pages and the boundary of what can be
reproduced from code alone.

`create_paper_figures.py` recreates the register-length and final grammar-probe
figures from audited aggregate values reported in the paper. It does not read or
write corpus text.
