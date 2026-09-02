#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["beautifulsoup4", "requests"]
# ///

"""Scrape Thirukadukam verses and urai from Tamil Virtual Academy.

TamilVU uses two separate pages per verse:
  Verse page: https://www.tamilvu.org/slet/l2800/l2800are.jsp?song_no=N&book_id=43
  Urai page:  https://www.tamilvu.org/slet/l2800/l2800aru.jsp?song_no=N&book_id=43&head_id=43&sub_id=XXXX

The verse page contains a link to the urai page with a sub_id that must be
extracted (it is not predictable from the verse number alone).

The scraper is deliberately resumable and slow by default. Each fetched page is
cached before parsing, so an interrupted run can continue without downloading
successful pages again.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup, Tag


BOOK_ID = 43
VERSE_URL = (
    "https://www.tamilvu.org/slet/l2800/"
    "l2800are.jsp?song_no={verse_number}&book_id={book_id}"
)
URAI_BASE_URL = "https://www.tamilvu.org/slet/l2800/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36"
)
DEFAULT_DELAY_SECONDS = 5.0
DEFAULT_RETRIES = 5


@dataclass(frozen=True)
class VerseRecord:
    verse_number: int
    verse: str
    urai: str
    source_url: str
    book_id: int = BOOK_ID
    work: str = "திரிகடுகம்"
    author: str = "நல்லாதனார்"


def normalize_line(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\ufeff", " ").replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


def normalized_lines(text: str) -> list[str]:
    return [
        line
        for raw_line in text.splitlines()
        if (line := normalize_line(raw_line))
    ]


def tamil_score(text: str) -> int:
    return sum("\u0b80" <= char <= "\u0bff" for char in text)


def mojibake_penalty(text: str) -> int:
    markers = ("à®", "à¯", "â€", "ðŸ", "Ã", "Â")
    return sum(text.count(marker) for marker in markers)


def repair_mojibake(text: str) -> str:
    """Repair common UTF-8-as-Latin-1/CP1252 corruption when it improves Tamil."""

    best = text
    best_quality = (tamil_score(best), -mojibake_penalty(best))

    for _ in range(2):
        candidates: list[str] = []
        for encoding in ("latin-1", "cp1252"):
            try:
                candidates.append(best.encode(encoding).decode("utf-8"))
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass

        if not candidates:
            break

        candidate = max(
            candidates,
            key=lambda value: (tamil_score(value), -mojibake_penalty(value)),
        )
        quality = (tamil_score(candidate), -mojibake_penalty(candidate))
        if quality <= best_quality:
            break
        best = candidate
        best_quality = quality

    return unicodedata.normalize("NFC", best)


def decode_html_bytes(content: bytes, declared_encoding: str | None = None) -> str:
    encodings: list[str] = []
    if declared_encoding:
        encodings.append(declared_encoding)
    encodings.extend(["utf-8", "cp1252", "latin-1"])

    candidates: list[str] = []
    for encoding in dict.fromkeys(encodings):
        try:
            candidates.append(repair_mojibake(content.decode(encoding)))
        except (LookupError, UnicodeDecodeError):
            pass

    if not candidates:
        return repair_mojibake(content.decode("utf-8", errors="replace"))

    return max(
        candidates,
        key=lambda value: (
            tamil_score(value),
            -mojibake_penalty(value),
            -value.count("\ufffd"),
        ),
    )


def element_text(element: Tag, separator: str = "\n") -> str:
    return "\n".join(normalized_lines(element.get_text(separator, strip=True)))


def parse_verse_page(
    html: str,
    expected_verse_number: int,
) -> tuple[str, str]:
    """Return (verse_text, urai_page_url) from the verse listing page."""
    html = repair_mojibake(html)
    soup = BeautifulSoup(html, "html.parser")

    # The verse text lives in the innermost td.poem (nested table inside outer td.poem)
    poem_cells = soup.select("td.poem")
    if not poem_cells:
        raise ValueError("TamilVU verse page has no td.poem cell")
    # The inner-most td.poem carries the actual verse text
    inner_poem = poem_cells[-1]
    verse = element_text(inner_poem)
    if not verse:
        raise ValueError("Verse text is empty")

    # Optional: verify verse number from the adjacent pno cell
    number_cell = inner_poem.find_previous_sibling("td")
    if number_cell is not None:
        number_match = re.search(r"\d+", number_cell.get_text(" ", strip=True))
        if number_match and int(number_match.group()) != expected_verse_number:
            raise ValueError(
                f"Expected verse {expected_verse_number}, "
                f"but page shows verse {number_match.group()}"
            )

    # Find the link to the urai page (l2800aru.jsp?...)
    urai_link = soup.find("a", href=re.compile(r"l2800aru\.jsp"))
    if urai_link is None:
        raise ValueError("No urai link found on verse page")
    href = urai_link["href"]
    urai_url = href if href.startswith("http") else URAI_BASE_URL + href

    return verse, urai_url


def parse_urai_page(html: str, expected_verse_number: int) -> str:
    """Extract urai text from the dedicated urai page (l2800aru.jsp)."""
    html = repair_mojibake(html)
    soup = BeautifulSoup(html, "html.parser")

    list_cell = soup.select_one("td.list")
    if list_cell is None:
        raise ValueError("Urai page has no td.list cell")

    paras = list_cell.find_all("p")
    if len(paras) < 3:
        raise ValueError("Urai page has too few paragraphs")

    # Para 0: "நூல்" label; para 1: verse text — skip both
    urai_parts: list[str] = []
    for p in paras[2:]:
        t = element_text(p)
        # Drop the trailing verse-number paragraph, e.g. "(1)"
        if re.match(r"^\s*\(\d+\)\s*$", t):
            continue
        if t:
            urai_parts.append(t)

    urai = "\n\n".join(urai_parts)
    if not urai:
        raise ValueError("Urai text is empty after parsing")
    return urai


def is_verse_error_page(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    text = normalize_line(soup.get_text(" "))
    lowered = text.lower()
    return (
        len(text) < 100
        or "bad gateway" in lowered
        or "internal server error" in lowered
        or "nullpointerexception" in lowered
        or "try error" in lowered
        or soup.select_one("td.poem") is None
    )


def is_urai_error_page(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    text = normalize_line(soup.get_text(" "))
    lowered = text.lower()
    return (
        len(text) < 100
        or "bad gateway" in lowered
        or "internal server error" in lowered
        or "nullpointerexception" in lowered
        or "try error" in lowered
        or soup.select_one("td.list") is None
    )


def fetch_html(
    session: requests.Session,
    url: str,
    delay_seconds: float,
    retries: int,
    error_check=None,
) -> str:
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=(20, 90))
            if response.status_code in {429, 500, 502, 503, 504}:
                raise requests.HTTPError(
                    f"temporary HTTP {response.status_code}", response=response
                )
            response.raise_for_status()
            html = decode_html_bytes(response.content, response.encoding)
            if error_check is not None and error_check(html):
                raise ValueError("TamilVU returned an incomplete/error page")

            time.sleep(delay_seconds + random.uniform(0, min(1.0, delay_seconds / 4)))
            return html
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt == retries:
                break
            wait = max(delay_seconds, min(60.0, 2 ** (attempt - 1) * delay_seconds))
            print(
                f"    Attempt {attempt}/{retries} failed: {exc}; "
                f"retrying in {wait:.1f}s",
                file=sys.stderr,
            )
            time.sleep(wait)

    raise RuntimeError(f"Failed after {retries} attempts: {url}") from last_error


def load_records(path: Path) -> dict[int, VerseRecord]:
    if not path.exists():
        return {}

    records: dict[int, VerseRecord] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        record = VerseRecord(
            verse_number=int(item["verse_number"]),
            verse=item["verse"],
            urai=item["urai"],
            source_url=item["source_url"],
            book_id=int(item.get("book_id", BOOK_ID)),
            work=item.get("work", "திரிகடுகம்"),
            author=item.get("author", "நல்லாதனார்"),
        )
        records[record.verse_number] = record
    return records


def write_outputs(
    records: Iterable[VerseRecord],
    jsonl_path: Path,
    json_path: Path,
) -> None:
    payload = [asdict(record) for record in records]
    jsonl_path.write_text(
        "".join(
            json.dumps(item, ensure_ascii=False) + "\n"
            for item in payload
        ),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Scrape all 100 Thirukadukam verses and urai from TamilVU."
    )
    parser.add_argument("--start", type=int, default=1, help="First verse (default: 1)")
    parser.add_argument("--end", type=int, default=100, help="Last verse (default: 100)")
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help="Minimum pause after requests (default: 5)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help="Attempts per page (default: 5)",
    )
    parser.add_argument(
        "--cache-dir",
        default="thirukadukam_tamilvu_html",
        help="Directory for cached HTML",
    )
    parser.add_argument(
        "--jsonl-output",
        default="thirukadukam_tamilvu.jsonl",
        help="JSONL output path",
    )
    parser.add_argument(
        "--json-output",
        default="thirukadukam_tamilvu.json",
        help="JSON output path",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refetch pages even when a valid cached copy exists",
    )
    args = parser.parse_args()

    if not 1 <= args.start <= args.end <= 100:
        parser.error("--start and --end must satisfy 1 <= start <= end <= 100")
    if args.delay_seconds < 0:
        parser.error("--delay-seconds cannot be negative")
    if args.retries < 1:
        parser.error("--retries must be at least 1")

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = Path(args.jsonl_output)
    json_path = Path(args.json_output)

    records = load_records(jsonl_path)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ta,en-US;q=0.8,en;q=0.6",
            "Referer": "https://www.tamilvu.org/",
        }
    )

    requested_numbers = range(args.start, args.end + 1)
    for verse_number in requested_numbers:
        verse_url = VERSE_URL.format(verse_number=verse_number, book_id=BOOK_ID)
        verse_cache = cache_dir / f"verse-{verse_number:03d}.html"
        urai_cache  = cache_dir / f"urai-{verse_number:03d}.html"

        if verse_number in records and verse_cache.exists() and urai_cache.exists() and not args.refresh:
            print(f"[{verse_number:03d}] already complete")
            continue

        # ── Verse page ──────────────────────────────────────────────────────
        verse_html: str
        if verse_cache.exists() and not args.refresh:
            verse_html = repair_mojibake(verse_cache.read_text(encoding="utf-8"))
            try:
                verse_text, urai_url = parse_verse_page(verse_html, verse_number)
                print(f"[{verse_number:03d}] reused cached verse HTML")
            except ValueError:
                print(f"[{verse_number:03d}] cached verse HTML invalid; refetching")
                verse_html = fetch_html(session, verse_url, args.delay_seconds, args.retries, is_verse_error_page)
                verse_cache.write_text(verse_html, encoding="utf-8")
                verse_text, urai_url = parse_verse_page(verse_html, verse_number)
        else:
            print(f"[{verse_number:03d}] fetching {verse_url}")
            verse_html = fetch_html(session, verse_url, args.delay_seconds, args.retries, is_verse_error_page)
            verse_cache.write_text(verse_html, encoding="utf-8")
            verse_text, urai_url = parse_verse_page(verse_html, verse_number)

        # ── Urai page ───────────────────────────────────────────────────────
        urai_html: str
        if urai_cache.exists() and not args.refresh:
            urai_html = repair_mojibake(urai_cache.read_text(encoding="utf-8"))
            try:
                urai_text = parse_urai_page(urai_html, verse_number)
                print(f"[{verse_number:03d}] reused cached urai HTML")
            except ValueError:
                print(f"[{verse_number:03d}] cached urai HTML invalid; refetching")
                urai_html = fetch_html(session, urai_url, args.delay_seconds, args.retries, is_urai_error_page)
                urai_cache.write_text(urai_html, encoding="utf-8")
                urai_text = parse_urai_page(urai_html, verse_number)
        else:
            print(f"[{verse_number:03d}] fetching urai {urai_url}")
            urai_html = fetch_html(session, urai_url, args.delay_seconds, args.retries, is_urai_error_page)
            urai_cache.write_text(urai_html, encoding="utf-8")
            urai_text = parse_urai_page(urai_html, verse_number)

        records[verse_number] = VerseRecord(
            verse_number=verse_number,
            verse=verse_text,
            urai=urai_text,
            source_url=verse_url,
        )
        write_outputs(
            (records[number] for number in sorted(records)),
            jsonl_path,
            json_path,
        )

    selected = [
        records[number]
        for number in requested_numbers
        if number in records
    ]
    missing = [
        number
        for number in requested_numbers
        if number not in records
    ]
    if missing:
        raise RuntimeError(f"Missing requested verses: {missing}")

    write_outputs(
        (records[number] for number in sorted(records)),
        jsonl_path,
        json_path,
    )
    print(
        f"Saved {len(selected)} requested records "
        f"({len(records)} total cached records) to {jsonl_path} and {json_path}"
    )


if __name__ == "__main__":
    main()
