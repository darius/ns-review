#!/usr/bin/env python3
"""Extract a chapter (or a section range) of Nanosystems from the EPUB as plain text.

Usage:
  python tools/extract_chapter.py 9            -> source/ch09.txt
  python tools/extract_chapter.py 7 7.4 7.5    -> source/ch07-s7.4.txt  (from heading '7.4.' up to '7.5.')

The EPUB (github.com/Mihonarium/nanosystems, release 'ebook') is expected at source/nanosystems.epub.
Chapter files are located by scanning each file for its first 'N.1.' heading; the EPUB's own
numbering is not a constant offset (part-divider pages intervene).

Math is replaced by [M]; figures and tables are dropped. This is for reading and extraction, not for
quoting equations — check equations against the EPUB or the print book.
"""
import html, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPUB = ROOT / "source" / "nanosystems.epub"


def _clean(s: str) -> str:
    s = re.sub(r"<math.*?</math>", " [M] ", s, flags=re.S)
    s = re.sub(r"<(script|style).*?</\1>", "", s, flags=re.S)
    s = re.sub(r"<h([1-6])[^>]*>", r"\n\n### ", s)
    s = re.sub(r"</h[1-6]>", "\n", s)
    s = re.sub(r"</p>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s


def chapter_map() -> dict:
    """Map book chapter number -> EPUB member name, by the first 'N.1.' heading in each file.
    The EPUB's chNNN numbering is not a constant offset (part dividers intervene)."""
    m = {}
    with zipfile.ZipFile(EPUB) as z:
        for name in z.namelist():
            if not re.match(r"EPUB/text/ch\d+\.xhtml$", name):
                continue
            t = _clean(z.read(name).decode("utf-8"))
            h = re.search(r"### (\d+)\.1\. ", t)
            if h:
                m.setdefault(int(h.group(1)), name)
    return m


def chapter_text(n: int) -> str:
    name = chapter_map().get(n)
    if not name:
        sys.exit(f"chapter {n} not found in EPUB")
    with zipfile.ZipFile(EPUB) as z:
        return _clean(z.read(name).decode("utf-8"))


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
