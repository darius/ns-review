#!/usr/bin/env python3
"""Extract a chapter (or a section range) of Nanosystems from the upstream Markdown as text.

Usage:
  python tools/extract_chapter.py 9            -> source/ch09.txt
  python tools/extract_chapter.py 7 7.4 7.5    -> source/ch07-s7.4.txt  (from heading '7.4.' up to '7.5.')

Source: full_book.md from github.com/Mihonarium/nanosystems (the file the EPUB and the site are
built from). Expected at source/full_book.md; downloaded from the repo's main branch if absent.

Why Markdown and not the EPUB: the EPUB renders every equation as a MathJax SVG of glyph outlines
with no MathML or TeX annotation, so no text extractor can recover them. The Markdown has display
equations as $$ ... \\tag{N.NN} $$ blocks carrying the book's own equation numbers, inline math as
$...$, and tables as Markdown tables. All of that is kept verbatim here.

Chapters are located by heading: chapter N is the '## ' section that contains the first
'### N.1. ' heading (part-divider pages are their own '## ' sections). Figure image links become
'[figure]'; HTML comments are dropped. The Markdown is an OCR+math-recognition transcription, so
check load-bearing equations against the print scan.
"""
import re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "source" / "full_book.md"
BOOK_URL = "https://raw.githubusercontent.com/Mihonarium/nanosystems/main/full_book.md"


def book_text() -> str:
    if not BOOK.exists():
        print(f"downloading {BOOK_URL} -> {BOOK}", file=sys.stderr)
        BOOK.parent.mkdir(exist_ok=True)
        urllib.request.urlretrieve(BOOK_URL, BOOK)
    return BOOK.read_text(encoding="utf-8")


def _clean(s: str) -> str:
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$", "[figure]", s, flags=re.M)
    s = re.sub(r"<p[^>]*>\s*!\[[^\]]*\]\([^)]*\)\s*</p>", "[figure]", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() + "\n"


def chapter_spans(text: str) -> dict:
    """Map book chapter number -> (start, end) offsets of its '## ' section."""
    heads = [m.start() for m in re.finditer(r"^## ", text, flags=re.M)] + [len(text)]
    spans = {}
    for a, b in zip(heads, heads[1:]):
        h = re.search(r"^### (\d+)\.1\. ", text[a:b], flags=re.M)
        if h:
            spans.setdefault(int(h.group(1)), (a, b))
    return spans


def chapter_text(n: int) -> str:
    text = book_text()
    span = chapter_spans(text).get(n)
    if not span:
        sys.exit(f"chapter {n} not found in {BOOK}")
    return _clean(text[span[0]:span[1]])


def main():
    n = int(sys.argv[1])
    text = chapter_text(n)
    out = ROOT / "source" / f"ch{n:02d}.txt"
    if len(sys.argv) >= 4:
        a, b = sys.argv[2], sys.argv[3]
        i, j = text.find(f"### {a}. "), text.find(f"### {b}. ")
        if i < 0 or j < 0:
            sys.exit(f"could not find section headings {a}. / {b}.")
        text = text[i:j]
        out = ROOT / "source" / f"ch{n:02d}-s{a}.txt"
    out.write_text(text)
    print(f"wrote {out} ({len(text.split())} words)")


if __name__ == "__main__":
    main()
