# CLAUDE.md — Nanosystems audit

Technical audit of Drexler, *Nanosystems* (1992), structured as a formalization project:
one interface file per chapter recording what the chapter imports and exports, a generated
dependency graph, then adjudication in dependency order. Owner: Darius. Read
`docs/DECISIONS.md` for why things are the way they are — it stands in for the design
conversation, which is not otherwise available to you.

`generated/` is built by `tools/build.py` — never hand-edit it. Tests: `.venv/bin/python -m pytest`.

## Invariants — these are rules, not preferences

1. **Single writer.** Extracting chapter N edits only `chapters/chNN.yaml`. Never add stubs,
   ids, or notes to another chapter's file. Forward references go in your own `consumed_by`;
   the reverse index is generated.
2. **Extraction is not adjudication.** During extraction, `verdict` stays `null`. Arithmetic
   checks go in `spot_check` and are explicitly not verdicts. Concerns go in `notes`, phrased
   as "adjudicate at audit."
3. **Read the text.** Extract from `source/chNN.txt` (run `tools/extract_chapter.py N` if
   absent). Do not extract from memory of the book. Quote hedges verbatim.
4. **Preserve the hedge.** `hedge:` holds the author's exact modal ("appears to", "typically
   ... save in", "may be"). It is evidence.
5. **BARE is a category, not a gap.** A claim with no internal or external reference is
   `support: BARE`. Do not omit it, do not invent a reference for it. The BARE fraction
   (13–63% by chapter so far; see generated/INDEX.md) is tracked and is itself a finding. Do
   not aim for a rate; classify each claim on its own text.
6. **Hypotheses are the point.** Every export of type `construction` or `design-license`, and
   every `parameter` with a stated regime of validity, gets a `hypotheses:` list. A stated
   scope condition ("assumes mean free paths shorter than l") becomes its own
   `scope-condition` export *and* appears in the hypotheses of what depends on it.
7. **No number without a source.** Material parameters cite external literature (with
   `vintage`), the book (with section), or an executed computation (in `spot_check`). Never
   your own recall.
8. **Verdicts come from the lattice** in `docs/SCHEMA.md`, not true/false. Keep
   `math_correct` and `inputs_adequate` separate.
9. **Build before commit.** `python tools/build.py` must exit 0. Warnings are allowed and
   informative (an orphan scope-condition usually means its dependents aren't extracted yet).

## Workflows

**Extract a chapter**
```
python tools/extract_chapter.py N            # -> source/chNN.txt
# read it in full; write chapters/chNN.yaml per docs/SCHEMA.md
python tools/build.py                        # fix errors; read warnings
```
Aim for every nontrivial claim: one a downstream number depends on, one that licenses a
design choice, or any negative claim ("X is negligible / no problem / feasible"). The third
class is the highest-value and most easily missed.

**Extend a partial chapter** — set `coverage: full` or extend `sections:`; keep existing ids.

**Process a criticism** — add or update an entry in `criticism/register.yaml`; `targets` are
export ids, pending if the chapter isn't extracted. Read the source, don't summarise from
secondary descriptions. Set `status: unread` if you haven't.

**After extracting chapter N**, read `generated/INDEX.md` for `consumed_by` forward claims
that point at N. For each, add an import to `chNN.yaml` — `cited: yes` if the text references
it, `cited: no` if N uses (or should have used) the result silently. The inferred ones are
where the findings are.

**Audit an item** (only after its chapter and its imports' chapters are `reconciled`; the
2026-09-18 spike is the one sanctioned exception, and its verdicts say "provisional"):
verify each hypothesis at each import site; fill `verdict`, `verdict_notes`,
`hypotheses_discharged` on the import side, with a one-line mirror on the export. Put the
calculation in `nsaudit/` with a test, and cite the module from `verdict_notes`. A
`hypothesis-violated` verdict must state the magnitude of the downstream impact.

## Do not

- Do not rewrite existing entries for style or completeness. Edit only when the text or a
  source contradicts what's there.
- Do not adopt a critic's framing as a verdict. Register it, then check it.
- Do not summarise the book's argument in a chapter file; record claims.
- Do not run `memory_delete`-style cleanups on `generated/` — just rebuild it.

## Current state (2026-09-18, end of first working session) — START HERE

Handoff for review. Eight chapters extracted and mutually reconciled; one verdict; 126 tests.
Read docs/DECISIONS.md top to bottom for findings; generated/INDEX.md for the graph.

- Equation errors found so far: Eq. 7.29 missing a π (in the book: its own quoted 1570 K
  follows the printed form); §7.3.5e d_n exponent sign and Eq. 6.24 missing k_s and off by 2
  (not checked against the print: could be transcription; the nanosyste.ms PDF is built from
  the same Markdown, so a scan is needed). Arithmetic inconsistencies: 12.3.8b per-interlock
  energy; 14.4.8 dissipation sum and entropy term.
- One verdict (no longer provisional): `7.4.2/phonon-viscosity-small-except` → 12.3.4,
  hypothesis-violated, impact ≤ +15% on the switching budget. See DECISIONS.md "Spike".
- Prase (2026) read in full and retargeted; its ≥ 2 OOM claim now points at the
  bounded-continuum application and the collective-mode deferral, not at 7.4.2.
- Priority (Darius, 2026-09-18): the path into Ch. 14. Ch. 15–16 matter only if Ch. 14 works.
- Ch. 13 is now the gap on the Ch. 14 path: 13.3.7 supplies the largest term of the 14.4.8
  budget (1.5e6 J/kg) and 13.3.6 the error rates and fail-stop behaviour.
- 13.3.7's 1.5e6 J/kg is a ~30 maJ mean per operation, lowered from the naive 145 maJ by
  conditional repetition (13.3.1c, 8.3.4f), near-reversible steps (8.5.2b) and dissipation-free
  radical coupling (8.5.3b). Those Ch. 8 subsections are on the Ch. 14 path; the rest of
  Ch. 8 is not yet. Audit question: 30 maJ × 5e25 atoms/kg is one operation per atom, while
  13.3.7b's naive estimates assume ten steps per atom (×10 would consume the whole 1.5e7 J/kg).
- 14.4.8 margin: the mill term can grow ~8× before the energy surplus vanishes, but waste
  heat grows in proportion from the start, so cooling (Ch. 11, 14.4.1) may bind first.
- Next, in order: (1) extract Ch. 13 (at least 13.2.2, 13.3.1, 13.3.2, 13.3.5–13.3.8, 13.4),
  then 8.3.4, 8.5.2, 8.5.3 as a partial Ch. 8; (2)
  adjudicate the 14.4.8 budget as a unit, with its three imports (13.3.7, 9.7.3 recovery,
  12.7.4 computation) and the two arithmetic inconsistencies above; (3) the three single-edge
  audits exposed by reconciliation: 12.3.7 on `5.3.1/bath-coupling-irrelevant` (Prase FDT),
  12.3.7 on the equilibrium limit of `6.3.3/switched-coupling-error-model`, and 9.4.3's
  `deficit-is-mm2-artifact` against `3.3.2/mm2-known-defects`; (4) the 7.4.2 exception's second
  use site at 10.4.6 (the 12.3.4 bound should transfer). Ch. 11 after Ch. 13 if 14.4.1's
  "supporting systems peripheral" (cooling, power) needs checking.
