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

## Current state (2026-09-27, after Ch. 13 and partial Ch. 8) — START HERE

Eleven chapters extracted and mutually reconciled (3, 5, 6, 7, 9, 13, 14 full; 8, 10, 11, 12 partial);
one verdict. Read docs/DECISIONS.md top to bottom for findings; generated/INDEX.md for the graph.

- Equation errors found so far: Eq. 7.29 missing a π (in the book: its own quoted 1570 K
  follows the printed form; both this and the next were first noted by Prase fn. 49); §7.3.5e d_n exponent sign and Eq. 6.24 missing k_s and off by 2
  (not checked against the print: could be transcription; the nanosyste.ms PDF is built from
  the same Markdown, so a scan is needed). Arithmetic inconsistencies: 12.3.8b per-interlock
  energy; 14.4.8 dissipation sum and entropy term; Table 13.1 rocking compliance (10× low on a
  ring-of-springs model).
- Verdicts: `7.4.2/phonon-viscosity-small-except` → 12.3.4, hypothesis-violated, ≤ +15% on
  the switching budget (DECISIONS.md "Spike"). The 14.4.8 budget (DECISIONS.md "Audit: the
  14.4.8 energy budget"; provisional on 11/measurement, 8.4.4b): dissipation uncertain by
  ~1.5 OOM upward, 2.9e6 (book's intended physics; budget holds) to 8.2e7 J/kg (net energy
  consumer, 13× the stated cooling), set by whether preparation steps are near-reversible.
- Prase (2026) read in full and retargeted; its ≥ 2 OOM claim now points at the
  bounded-continuum application and the collective-mode deferral, not at 7.4.2.
- Priority (Darius, 2026-09-18): the path into Ch. 14. Ch. 15–16 matter only if Ch. 14 works.
- Ch. 13 findings on that path (DECISIONS.md "Ch. 13"): the 1.5e6 J/kg mill term assumes 13.3.3's ~10
  preparation steps per moiety are near-reversible (~2e6 J/kg with them counted at ~1 maJ);
  if they dissipate in snaps at the 145 maJ reliability exoergicity it is ~7e7, ~5× the free
  energy, so preparation reversibility (8.5.2b, 8.3.4f) is the lever; its low-dissipation mechanisms are the ones
  13.3.5's mass estimate excludes; 1e-15 per operation is radiation-dominated at 1e4 /s but not
  at the 1e6 Hz Table 14.1 uses for reagent prep; 13.3.8's 475 maJ is ΔH, not ΔG.
- Ch. 8 (8.3.3-8.3.4, 8.5; DECISIONS.md "Ch. 8"): near-reversibility (8.5.2b) needs >= 150 maJ
  of well-depth modulation mid-step; worked out only for tensile C-C cleavage with a 1.5× MM2
  stiffness margin; radical-addition dissipation left open (8.5.5), carbenes unclear, transition
  metals "presumably". 13.3.3's preparation example uses exactly the unworked classes, and
  13.3.7's radical coupling sets aside 8.5.3c's spin caveat. Rest of Ch. 8 (8.4, 8.6) not needed yet.
- 14.4.8 margin: the mill term can grow ~8× before the energy surplus vanishes. Cooling is
  plant sizing, not a limit (11.5.3 margin >= 33x in every scenario); Ch. 14's cooling numbers
  are per 1 kg/hr while the architecture runs at 3.6 kg/hr (4.8 kW by its own budget).
- Prase (2026): partially rebutted (DECISIONS.md "Audit: Prase"). Single-rod relaxation 12x
  overstated (but the book's Eq. 12.15 is 2.1x low); Eq. 7.40 sin 2θ correct; the molecular-solid
  model misdescribes sliding rods; at 14.4.8 every speed-dependent penalty is discharged by a
  slower clock. FDT (C.2) rebutted: displacement statistics are damping-independent; 12.3.7's
  e^-169 stands (5.3.1 and 6.3.3 edges verified). Open: edge stick-slip (uncertain 2.5 OOM on
  ch12's 10.12 import; speed-independent, could reach 14.4.8 at ~1e7-2e8 J/kg), collective modes.
- Next, in order: (1)-(2b) [done 2026-09-27: partial Ch. 8; the 14.4.8 budget; Prase]; (2c) edge
  stick-slip: an MM calculation of a terminated rod end sliding in its channel (edge
  corrugation vs 4.9 N/m) would settle the one open lever that no clock choice removes;
  Qu et al. 2020 is paywalled — ask Darius for access; (3) [done 2026-09-27: lifetime model —
  hypothesis-violated, prep stages fail ~1000x faster than radiation at 1e6 Hz, fixed by +6-16
  maJ on the weakest step]; (4) the single-edge audits: [done: 12.3.7 on 5.3.1 and 6.3.3; 6.3.3 at
  13.2.3b/13.3.7b, verified]; remaining: 9.4.3's `deficit-is-mm2-artifact` against `3.3.2/mm2-known-defects`;
  (5) [done: 7.4.2 at 10.4.6, 13.3.7a, 13.4.1f — at most +15% anywhere].
  [done 2026-09-27: Ch. 11 partial; 14.4.1 verified-modified]. Remaining: 9.4.3 vs 3.3.2; the
  MM rod-end edge calculation (2c); a book-group briefing (see memory).
