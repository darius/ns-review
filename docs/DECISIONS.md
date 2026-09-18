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
view. Calculations belong in a tested Python package (`nsaudit/`, not yet created) with
pytest tests that reproduce Drexler's published figures to a stated tolerance — each such test
is simultaneously a verification, a regression guard, and provenance. Use `pint` for units.
Notebooks (marimo for audit, Quarto for exposition) are thin views importing the package.

Claude Code is the working environment: it cannot see the design conversation, only this repo.

## Known inaccuracies from the design session, corrected

- "Drexler omitted Akhiezer damping" — false as stated; see above.
- Diamond thermal conductivity cited in §7.4.1 (Gray 1972, ~700 W/m·K) is ~3× below modern
  values; low impact because worked estimates use K_T=10.
- The Landau–Rumer crossover for diamond is ~20–75 GHz (back out tau from the cited f·Q), not
  ~1 THz as Prase fn. 28 says; not load-bearing.
- Marblestone PDF at web.mit.edu is dead as of 2026-09; the blog repost is canonical.
