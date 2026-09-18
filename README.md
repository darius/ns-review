# Nanosystems audit

A technical audit of K. Eric Drexler, *Nanosystems: Molecular Machinery, Manufacturing, and
Computation* (Wiley, 1992), organised like a formalization project.

The book is an engineering argument with a real dependency structure, most of it implicit. The
approach here is to make that structure explicit first — one **interface file** per chapter
listing what the chapter imports, exports, and assumes — then generate the dependency graph, then
adjudicate claims in dependency order, weighted by how much depends on them.

## Status

Early. Chapters 7 and 9 in full, the bearing and drag sections of Chapter 10, and the
dissipation/error sections of Chapter 12 are extracted. One
edge has been adjudicated end to end as a spike (the §7.4.2 phonon-viscosity exception at its
Ch. 12 use site), with the calculation in `nsaudit/` under test. See `generated/INDEX.md` for
coverage, verdicts, and the priority set, and `CLAUDE.md` for what to do next.

## How it works

- `chapters/chNN.yaml` — the interface file for chapter NN. Each nontrivial claim is an
  **export** with an id like `9.3.3/bounded-continuum`, a type, the claim close to verbatim, the
  author's own hedge, its support (internal ref / external citation / none), its polarity, and —
  the important part — its **hypotheses**: the conditions under which it holds. Anything the
  chapter relies on from elsewhere is an **import**.
- `tools/build.py` validates the files and writes `generated/INDEX.md`: who depends on what,
  which imports are pending or dangling, the negative-and-unsupported claims that need attention
  first, and per-chapter statistics.
- `criticism/register.yaml` — prior critiques and experiments, each pointing at the exports it
  attacks. An audit that starts from one critic inherits that critic's blind spots.
- Verdicts, when they exist, come from a lattice (verified / modified / uncertain by N orders
  of magnitude / hypothesis violated at a use site / refuted), not true/false. In an engineering
  argument a bad input usually widens error bars rather than refuting anything.

`docs/SCHEMA.md` has the field reference. `docs/DECISIONS.md` has the reasoning.

## Running

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python tools/extract_chapter.py 9   # text from the book Markdown -> source/ch09.txt
.venv/bin/python tools/build.py               # validate, regenerate generated/INDEX.md
.venv/bin/python -m pytest                    # reproduce the book's published numbers
.venv/bin/python -m nsaudit.audit_phonon_viscosity_rod_logic   # print one edge audit
```

The text is `full_book.md` from the `Mihonarium/nanosystems` GitHub repo (a transcription of
the book, also hosted at nanosyste.ms), fetched automatically into `source/` on first use.
Equations are kept as LaTeX with the book's equation numbers. The repo's EPUB is not used: it
renders every equation as an SVG of glyph outlines, so no text can be recovered from it.

## Contributing

Extraction of a chapter is self-contained: read the text, write the chapter's file, run the
build. Don't touch other chapters' files — forward references go in your own `consumed_by` and
the reverse index is generated. Don't adjudicate while extracting. Quote hedges verbatim. A
claim with no reference is recorded as such, not skipped and not given a reference it doesn't
have.

Good first tasks: extend Ch. 7 to full coverage; process the three Moriarty–Phoenix PDFs into
the register; read the entries marked `unread`.
