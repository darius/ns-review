# Design decisions and rationale

This file stands in for the conversation in which the project was designed. If something here
seems arbitrary, it probably had a reason; if the reason no longer holds, change it and say so.

## Purpose

Two deliverables:
1. **Audit notebooks** — claims checked, calculations and derivations, verdicts with provenance.
2. **Expository notebooks** — for a general STEM reader with no condensed-matter background.

Exposition is organised by **physics domain** (phonon transport and internal friction, sliding-
interface models, mechanosynthesis thermochemistry, fault-tolerant architectures), *not* by
chapter. Reasons: a generalist needs the domain background more than a paraphrase of Drexler;
domain notes are reusable whatever the verdicts turn out to be; and writing exposition and audit
together for the same claim invites motivated reasoning in both directions. Exposition for a
cluster is written after that cluster's verdicts exist.

## Why interface files (the formalization analogy)

The book is an engineering argument with a real dependency structure: Ch. 14 turned out to be
nearly pure bookkeeping over imports (§13.3.7 dissipation, §13.3.6 error rates, §12.7.4 energy
per instruction), so its robustness is entirely inherited. The analogy to a formalization —
theory files with imports/exports, named propositions, hypotheses that must be discharged at
use sites — is what makes the audit tractable and mechanical.

Where the analogy is load-bearing: **hypotheses**. A Lean theorem can't be applied without
discharging its hypotheses. Drexler states hypotheses in prose ("assumes phonon mean free paths
are shorter than l"; "save in systems undergoing very high frequency motion") and the central
audit question is whether downstream use sites satisfy them. That check is a graph traversal
once the files exist.

Where the analogy breaks: **verdicts are not booleans.** One bad lemma doesn't break the
argument; it widens error bars downstream. Ch. 14 showed a 3-OOM uncertainty in one import
surfacing as a 3-OOM uncertainty in one budget line, not a refutation. Hence the verdict
lattice (verified / verified-modified / uncertain-by-N-OOM / hypothesis-violated / refuted) and
interval-style propagation. Hence also the audit ordering: out-degree × downstream sensitivity,
not bare topological position. Ch. 14 was insensitive to Ch. 9's moduli and violently
sensitive to Ch. 12's per-instruction dissipation.

## Single-writer per file; generated reverse index

The original conception had each chapter's extraction update the docs of chapters it references.
Rejected because every chapter referencing Ch. 10 would write a stub into Ch. 10's file before
Ch. 10 is read, each under whatever name the referencing chapter uses ("bounded continuum
model", "BCM", "the continuum approach of Ch. 9"). Reconciliation would then be mostly
de-duplicating stubs. Instead: a chapter records only its own imports and exports (including
forward claims in `consumed_by`); the reverse index is a build artifact. Reconciliation shrinks
to three mechanical checks — dangling imports, duplicate exports, alias merging — all in
`tools/build.py`. Extraction becomes order-independent. (Parallelism isn't expected to be
needed; the reason is name drift, not concurrency.)

## Three-way support taxonomy, not two

The first proposal was internal refs / external refs. That enumerates *supported* claims and
drops unsupported ones, which is exactly where omissions live. The §7.4.2 finding (below) has
no reference of either kind. ~65% of nontrivial claims in the pilot were BARE. The negative-
and-BARE combination is the priority audit set.

## The motivating finding: §7.4.2

The circulating charge (Prase 2026) is that Drexler omitted Akhiezer damping. §7.4.2 contains
it, as "phonon viscosity," correctly attributed to Lothe (1962), with tau_relax ~1e-13 s from
boundary scattering. It also contains a self-declared exception: phonon viscosity losses are
"typically ... small ... save in systems undergoing very high frequency motion or nearly pure
shear." No threshold is given. Ch. 12's rod logic operates at ~10 GHz effective. So the
accurate charge is "the author's own stated exception was not honoured downstream" — worse for
the book, and only answerable by checking §7.4.2's out-edges. A claim-level audit cannot find
this; a graph-level one can. That is the existence proof for the whole design.

Two adjudication concerns already recorded on the Ch. 7 side: (a) the tau in §7.4.2 is an
*elastic* boundary-scattering time, but Akhiezer loss is governed by the *inelastic* mode-
population equilibration time; substituting one for the other is not obviously conservative.
(b) A single scalar Grüneisen number is the mean anharmonicity; the loss depends on its
dispersion across modes.

## What the Ch. 14 analysis established (chat session, before the repo)

Not yet in any chapter file; recorded here so it isn't lost.
- Table 14.1's frequency ladder runs 1e6 Hz (mills, 20 nm) down to 5 Hz (manipulators, 0.2 m);
  Drexler states twice that parallelism is bought to lower per-unit frequency and dissipation.
- Granting Prase's full molecular-solid correction (f·Q ~1e10 Hz), a mill at 1 MHz has Q ~1e4
  and loses ~0.05–0.5 kT per operation against a stated budget of ~3.6 kT/op. ~2 OOM margin.
  Molecular-relaxation and FDT arguments also fail to propagate at 1 MHz.
- The one propagation path: §14.4.8 imports 1e-16 J/instruction from §12.7.4 × 1e6 instr/block
  × 1e15 blocks = 1e5 J/kg. A 100–1000× rod-logic penalty makes this 1e7–1e8 J/kg against
  1.5e7 J/kg free energy available. Softened by Drexler flagging 1e6 instr/block as generous.
- Independent of friction: §14.2.1c assumes "almost all" bonding energy is recoverable
  (9e6 → 5e5 J/kg, ×18), tracing to §9.7.3's four unquantified mechanisms
  (`9.7.3/energy-release-controllable`). Mill power density ~2.3 MW/m³ in 97%-void machinery
  with no described internal cooling loop.

## Prior criticism: why a register, and what's in it

An audit that starts from one critique inherits that critique's blind spots. Prase attacks
Part II mechanics; Moriarty attacks Part I chemistry and Part III implementation; they barely
overlap. The audit root set is therefore Ch. 6, 7, 10, 12 *and* 8, 16. Smalley — the best-known
critique — is regarded as a straw man by Jones, Moriarty, and Marblestone alike.

Recurring dispute axes, tracked in `axis:`:
- **bound-vs-engineering-number** — is a stated limit physical or contingent on fabrication?
  (Finney vs Moriarty on tip geometry; also the reversible-computing Q argument.)
- **stated-exception-not-honoured** — §7.4.2 pattern.
- **unrefuted-vs-unpursued** — a sound claim in a direction nobody worked on (Marblestone's
  taboo thesis; NAS 2006).
- **material-choice** — diamondoid chosen for tractability, not as endpoint (Marblestone);
  silicon empirically easier (Moriarty EPSRC).

Empirical results outrank arguments: Moriarty's EPSRC fellowship (2008–13, ~£1.5M) set out to
test diamond mechanosynthesis and produced silicon-dimer manipulation instead.

Sources found so far are in `criticism/register.yaml`. Marblestone (2021) explicitly proposes
"an open source Nanosystems 2.0 with modern computation" — this project is a subset of that.

## Tooling

Interface files are YAML because they must be parseable; `generated/INDEX.md` is the readable
view. Calculations belong in the tested Python package `nsaudit/` with pytest tests that
reproduce Drexler's published figures to a stated tolerance — each such test is simultaneously
a verification, a regression guard, and provenance. Plain SI floats, unit in the docstring (see
the spike section for why not `pint`). Notebooks (marimo for audit, Quarto for exposition) are
thin views importing the package.

Claude Code is the working environment: it cannot see the design conversation, only this repo.

## Source text: Markdown, not EPUB (2026-09-18)

The design session extracted from the Mihonarium EPUB. That EPUB has no MathML: every equation
is a MathJax SVG of glyph outlines with no text alternative, so the original extractor dropped
every equation silently (its `[M]` placeholder never fired). The EPUB is built from
`full_book.md` in the same repo, which has display equations as `$$ ... \tag{N.NN} $$` with the
book's own numbering, inline math, and proper tables; `tools/extract_chapter.py` now reads that.
Ch. 9 and §7.4 were re-extracted; the prose is word-for-word identical to the EPUB extraction,
so the existing chapter files stand. The transcription is OCR plus math recognition: check
load-bearing equations against the print scan (e.g. `\text {relax }` spacing artifacts are
common, and a mis-recognised exponent would not be flagged by anything).

## Spike: one edge end to end before extracting more (2026-09-18)

Rationale: the schema had been exercised for extraction only. Before spending effort on more
chapters, one edge was pushed through extraction → import → calculation → verdict, to find out
what the adjudication side needs. The edge: `7.4.2/phonon-viscosity-small-except` → §12.3.4.
Ch. 12 was extracted partially (12.3.3–12.3.8, 12.4.3, 12.7.4), `nsaudit/` was created with
tests reproducing every published number in those sections, and the edge was adjudicated.
The verdicts are marked provisional: Ch. 7 and Ch. 12 are not reconciled and Ch. 10/5 imports
are pending. This deliberately breaks the "audit only after reconciled" rule once.

What the spike found about the *book*:
- §7.4.2 is cited nowhere outside itself (grep of the full text). The exception clause is never
  evaluated because the mechanism is never invoked; §12.3.4's inventory simply lacks it.
- Under the book's own model the omission is bounded: ≤ 0.165 maJ per transition, ≤ +15% on the
  2 maJ switching cycle, for any relaxation time. With the book's tau_relax the exception is not
  even triggered (ω·tau ~ 3e-3); with the thermalization time implied by modern f·Q data it is
  (ω·tau ~ 0.4–0.7). So: exception not honoured, hypothesis violated on modern inputs, impact
  small. Prase's fn. 30 says the same, and the ≥ 2 OOM claim attaches elsewhere (the assembly as
  a soft molecular solid: `12.3.3/bounded-continuum-applies`, `12.3.4/nonthermal-vibrations-by-design`).
- Two arithmetic flags recorded as spot checks, not verdicts: §7.4.3's "0.04 W/m² at 1 cm/s"
  contradicts Eq. 7.54's v² scaling by 100×; §12.3.8b's "0.013 maJ per interlock" is a typo for 0.13 (its
  own "0.031 kT" figure matches 0.125 maJ), and §12.7.4 then uses 0.03 maJ per interlock, which
  undercounts the interlock term ~7× (74 aJ per clock would be ~240 aJ); this feeds 14.4.8.
- The Landau–Rumer crossover backed out of Prase's cited f·Q is ~10–30 GHz (v = 1.2–1.8e4 m/s,
  γ = 0.9), correcting the "20–75 GHz" noted below from the design session.

What the spike found about the *schema*:
- Imports need `cited: yes|no`. The interesting edges are the ones the book does not
  acknowledge, and they must be written by the extractor of the *consuming* chapter, who has
  to know to look. Guidance: after extracting chapter N, read the generated index's
  `consumed_by` forward claims pointing at N and write an import (cited or inferred) for each.
- `hypothesis-violated` belongs on the import, with a one-line mirror on the export.
- A `hypothesis-violated` verdict is useless without a magnitude. The notes carry it in prose;
  the calculation module carries it in code. A structured `impact:` field may follow.
- Free-text hypotheses ("NOT very high frequency motion") cannot be checked without the auditor
  supplying a threshold; the threshold and its provenance go in the calculation module.
- `pint` was dropped: the book's empirical-exponent formulas (Eq. 12.17 has k_a^1.7 with a
  dimensional constant absorbing the units) make unit tracking noise rather than a check.
  Plain SI floats with the unit in the docstring.
- The index now lists inferred imports and all verdicts.

## Ch. 7 full extraction (2026-09-18): findings worth knowing before Ch. 10

- **Eq. 7.29 is missing a π.** Printed k_D = (6πn)^(1/3); the standard Debye cutoff is
  (6π²n)^(1/3). The printed form reproduces the Fig. 7.3 caption and the quoted T_D = 1570 K;
  the standard form gives ~2300 K for the same inputs, so the book's "1570 vs 2230 K measured"
  discrepancy is entirely the missing π^(1/3) = 1.46. The working energy density ε ≈ 2e8 J/m³
  used in §7.3.4–7.3.6 matches the *standard* cutoff (1.7e8), not the printed one (1.05e8), so
  the worked examples seem to have used the right k_D. T' and d' in the transmission fit
  (Eq. 7.40–7.41) are defined through k_D; whether the fit was calibrated with the printed or
  the standard value is not determinable from the text. Spot check on `7.3.2/debye-model`.
- **§7.1 defines the hedges.** "Typically", "frequently", "many systems" are declared to mean
  "characteristic of the Part II designs". Every hedge in Ch. 7 is therefore a forward claim
  about Ch. 10–14, which is exactly what the 7.4.2 spike found unevaluated.
- **The chapter's own summary is circular by admission** (`7.7/all-mechanisms-small-vs-kt`):
  each mechanism is small compared to kT "with reasonable choices of physical parameters (one
  criterion for a reasonable choice, of course, is that it result in acceptable energy
  dissipation)". The audit question for Part II is whether one parameter set is "reasonable"
  for all mechanisms at once.
- **Three of the load-bearing interface results rest on Soreff 1991, "Personal
  communications"**: the transmission coefficient (Eq. 7.39–7.40), the shear-reflection drag
  coefficient D_sr ≈ 1 ("a more thorough numerical investigation would be desirable"), and the
  nonadiabatic-excitation estimate. None is reproducible from the text as printed; Eq. 7.40 is
  derivable, D_sr is not.
- **Ch. 7's worked drag numbers presuppose Ch. 10.** Δk_a/k_a ≈ 0.1 and A/d ≈ 1e-2 are cited
  forward ("As discussed in Chapter 10"), so 7.3.5's ~200 and ~10 W/m² are not independent
  evidence for the bearing designs.
- `7.5.2/soft-surroundings-design` licenses a polymer-like local structure (M ≈ 3e9) to cut
  compression losses 1400×, in tension with `9.2/stiff-housing-architecture`; any consumer of
  the reduction must be checked for which it takes.
- Bare fraction for Ch. 7 in full: see the index. 7.4 alone was 53%; the full chapter is lower
  because §7.2–7.3 cite the dislocation literature heavily.

## Ch. 10 partial extraction (2026-09-18): bearings and the drag chain

Sections 10.3.4–10.3.6, 10.4, 10.8, 10.11–10.12. Every constant in §10.4.6 (2.4e-37, 1.8e-33,
3.0e-33, 1.2e-31, 4.3e-27) is re-derived in `nsaudit/ch10.py` from the Ch. 7 functions, so the
Ch. 7 → Ch. 10 → Ch. 12 drag chain is now executable end to end.

- **§7.3.5e's d_n has the wrong sign on the exponent.** Printed d_n = n^(-1/3) M/k_a has units
  of m²; the "atomic layers" reading and the 2.4e-37 of Eq. 10.19 both need n^(+1/3). Typo.
- **Eq. 10.19 uses the measured Debye temperature.** The 2.4e-37 reproduces only with
  T_D = 2230 K; the 1570 K that the printed Eq. 7.29 yields would give 1.5e-37. Together with
  the ε ≈ 2e8 finding, the Ch. 7 worked values were computed with the right k_D and the printed
  Eq. 7.29 is the odd one out.
- **§10.4.6f's "< 0.06 kT per rotation" is 0.082 kT from its own inputs.** 25% low; the
  "~1e11 W/m³" needs a volume ~4× the interface cylinder (undefined in the text).
- **Δk_a/k_a is a 100× lever on every bearing drag number** (`10.4.6/delta-ka-over-ka-values`:
  0.3–0.4 vs 0.001–0.003) and rests on an unshown row-row stiffness calculation plus a
  geometric argument. Which value a design earns is decided by `10.4.7/interface-catalogue`:
  the low value needs H- or F-terminated (111) surfaces *and* no axial load; every interlocking
  (axially stiff) interface is high-drag. 12.3.4c uses 0.4. The book's own designed bearing
  (10.4.7c) is stated to have higher drag than the sample calculation.
- **The 7.4.2 exception is unevaluated at a second site.** 10.4.6's inventory omits phonon
  viscosity too, and here the "nearly pure shear" branch is the relevant one. Recorded as an
  inferred import, not adjudicated (the 12.3.4 bound should transfer).
- Eq. 10.26 is Eq. 7.50 with an asserted τ_therm = 1e-12 s (40× the Eq. 7.51 value for the
  0.4 nm stress region), not Eq. 7.54 as the text says; conservative direction. Its "negligible"
  6e-16 W exceeds the shear-reflection term it is compared against in the 0.4 case.
- `10.11/stiffness-factor-0.5` is where 12.3.3's E = 5e11 comes from; asserted, not derived
  from the 9.4.3 rod moduli.
- Two atomic-detail bearings with stated numbers (10.4.7c, 10.4.7e; the latter on self-flagged
  sp³ nitrogen chains and ad hoc MM2 parameters) are the best reproduction targets so far.

## Ch. 3 full extraction (2026-09-18): where the chains bottom out

Every Part II import chain now resolves to a Ch. 3 export with zero dangling imports across
Ch. 3, 7, 9, 10, 12. Findings from reproducing what the later chapters read off Ch. 3:

- **9.4.2's δ_surf ≈ 0.07 nm is derivable.** Eq. 3.20 at the 0.1 nN convention gives a summable
  radius of 0.150 nm for sp³ carbon; minus the 0.077 nm covalent radius is 0.073 nm. The
  surface correction is not a free parameter; it is the loaded-contact radius minus the
  covalent radius, and its value depends on the 0.1 nN choice.
- **9.7.1 read Fig. 3.12's dense-surface curve, not curve (a).** Reconstructing Eqs. 3.33–3.38
  (continuum surface d_g behind each explicit plane), curve (a) gives 0.45 GPa tensile strength
  and 22 N/m·nm²; curves (c) and (e) give 0.8–1.1 GPa and 41–50 N/m·nm², matching 9.7.1's
  "~1 GPa, > 30 N/m·nm², compliance of a ~30 nm slab". Which curve a design earns depends on
  its surface atom density. The figure was not checked against the print edition.
- **MM2's stiffness defect is in bending, not stretching.** Table 3.7: MM3/MM2 = 1.02 for C–C
  stretch, 1.5–1.7 for angle bending. 9.4.3 attributes the sub-nm rod modulus deficit to "defects
  in the MM2 model"; whether bending dominates those rods enough to explain a substantial
  longitudinal deficit is now a concrete question for the 9.4.3 audit.
- **The exception 3.3.2g states is the strained-shell regime.** MM2's low bending stiffness
  "may then result in a false-positive assessment of the stability of a stretched bond" where
  bending relieves stretching: that is 9.6.1's strained shells and 10.4.7c's 0.166 nm bonds.
- **All nonbonded stiffnesses carry a stated "tens of percent" softness uncertainty** vs MM3
  (`3.3.2/mm3-softer-nonbonded`), conditional on "a substantial margin of safety" in every stiff
  interface design. The validation of the repulsive wall is against noble-gas beam data
  (`3.3.3/mm2-repulsion-validated-to-100maj`), stated as "within tens of percent" to 0.5 r_vdw0.
- **0.323 r_vdw0** (the stated breakdown of the exp-6) is where MM2's stiffness crosses zero;
  the force reverses at ~0.275 and the energy at ~0.22 r_vdw0.
- The MM2 pairwise Hamaker constant for diamond (Eq. 3.29) is ~2× the Lifshitz value in
  Table 3.9; which convention 9.7 and 10.4.8 use is a 2× question.
- The LEPS potential (3.4.3) is the modelling basis for 8.5.4's abstraction analysis that
  Moriarty attacks; it is a 1955–66 three-body semiempirical surface.

Statuses: the build now checks forward claims by section. The first run found 61 unconfirmed
claims into extracted sections; each real dependency became an inferred import in the
consuming chapter (27 added, e.g. Ch. 12's error model on `3.3.2/mm3-softer-nonbonded`, Ch. 10's
strained shell on `3.3.2/mm2-known-defects`) and 26 speculative `consumed_by` guesses were
trimmed. Ch. 3, 7, 9, 10, 12 now report reconcilable and are marked `reconciled`. Their remaining imports (Ch. 4, 5, 6, 8, 13,
14) are pending; that keeps the one verdict provisional, per SCHEMA.md.

## Known inaccuracies from the design session, corrected

- "Drexler omitted Akhiezer damping" — false as stated; see above.
- Diamond thermal conductivity cited in §7.4.1 (Gray 1972, ~700 W/m·K) is ~3× below modern
  values; low impact because worked estimates use K_T=10.
- The Landau–Rumer crossover for diamond is ~10–30 GHz (back out tau from the cited f·Q; see
  tests/test_ch07.py), not ~1 THz as Prase fn. 28 says; not load-bearing. (The design session
  said 20–75 GHz; superseded by the computed range.)
- Marblestone PDF at web.mit.edu is dead as of 2026-09; the blog repost is canonical.
