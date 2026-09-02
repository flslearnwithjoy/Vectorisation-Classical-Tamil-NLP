# Source map and acquisition record

This repository contains no source text, downloaded pages, or derived JSONL.
The table below identifies the public sources used to prepare v3 and the code
that can be used after independently obtaining the source material.

| v3 component | Public source used | Reproduction material |
| --- | --- | --- |
| Naaladiyar (393 pairs) | [Project Madurai, *Naaladiyar Nayavurai* Unicode edition (pmuni0778)](https://www.projectmadurai.org/pm_etexts/utf8/pmuni0778.html). Its header identifies Tamil Virtual Academy as the source of the scan. | `scripts/parse_naaladiyar_pm.py` parses a local text copy into records. Retain the original Project Madurai header with that copy. |
| Thirukadukam (100 pairs) | [Tamil Virtual University, Thirukadukam verse page, book 43](https://www.tamilvu.org/slet/l2800/l2800are.jsp?song_no=1&book_id=43). The parser follows each verse page's linked urai page; change `song_no` to reach another verse. | `scripts/parse_thirukadukam_tamilvu.py` is a cached, rate-limited parser for these public pages. |
| Tholkappiyam Ezhuthathikaram, Sollathikaram, and Porulathikaram (379, 287, and 103 pairs) | [Tamil Virtual University catalogue: Prof. K. Vellaivaranar](https://www.tamilvu.org/ta/library-nationalized-html-naauthor-89-235746). | These texts were manually collected and aligned for v3. No automated parser is supplied because the final section selection and alignment were manual rather than a repeatable page-level crawl. |

The Naaladiyar Project Madurai edition acknowledges Tamil Virtual Academy as the
scan source. The Tamil Virtual University permission note in this release
authorizes the stated academic use; it does not grant redistribution rights.
Accordingly, users must obtain all text themselves, respect each source's
current terms, and seek permission before redistributing source or derived
text.

The source catalogue is retained as a stable landing page for the manually
collected Tholkappiyam material. It is not a claim that every v3 row can be
reconstructed automatically from the current catalogue without manual review.
