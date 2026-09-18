# Interface file schema

One YAML file per chapter: `chapters/chNN.yaml`. It is the **source of truth** for that chapter.
Everything else (`generated/`) is built from these by `tools/build.py`.

## Top level

```yaml
chapter: 9
title: Nanoscale Structural Components
status: extracted        # extracted | reconciled | audited
coverage: full           # full | partial  (partial: list sections covered in `sections`)
sections: ["7.4"]        # only when coverage: partial
source: source/ch09.txt  # the extracted text this file was written against
history:
  - date: 2026-09-18
    note: initial extraction (chat session; converted from prepass doc)
exports: [...]
imports: [...]
```

## Exports

An export is anything the chapter puts into the book that another chapter (or a critic) could
depend on. Each has:

| field | required | values / notes |
|---|---|---|
| `id` | yes | `<section>/<mnemonic>`, e.g. `9.3.3/bounded-continuum`. The mnemonic is **ours** and stays stable; the book's own names go in `aliases`. |
| `type` | yes | `parameter` (a number) · `proposition` (a claim) · `construction` (a model, method, or design) · `scope-condition` (a precondition or exclusion) · `design-license` (a permission to design a certain way) |
| `section` | yes | e.g. `9.3.3` |
| `statement` | yes | The claim, close to verbatim. Use quotation marks for verbatim text. |
| `hedge` | no | The verbatim modal: `"appears to"`, `"typically ... save in"`, `"may be"`. Preserve it; it is evidence about the author's own confidence. |
| `support` | yes | `INT` (cross-reference within the book) · `EXT` (external citation) · `BARE` (no reference of either kind) |
| `refs` | no | list of section numbers or citations backing it |
| `polarity` | yes | `+` asserts something is so · `-` asserts something is negligible, feasible, or not a problem. `-` + `BARE` is the priority combination. |
| `hypotheses` | no | list of conditions under which the item holds. Either free text or an id of a `scope-condition` export. **This is the field the audit checks at every import site.** |
| `consumed_by` | no | sections the book says (or we expect) use this. Forward claims; confirmed against actual imports at build time. |
| `vintage` | EXT only | `OK` · `CHECK` · `SUPERSEDED?` plus a note |
| `aliases` | no | names the book uses for this item elsewhere |
| `prepass_id` | no | id from an earlier extraction doc, for traceability |
| `priority` | no | `high` · `normal` · `low` — audit ordering hint |
| `spot_check` | no | arithmetic or lookup done at extraction. **A spot-check is not a verdict.** |
| `notes` | no | anything else, clearly separated from the statement |
| `verdict` | audit only | `null` until audited, then one of the lattice below |
| `verdict_notes` | audit only | |

### Verdict lattice

Not true/false. In an engineering argument a bad lemma usually widens error bars downstream
rather than refuting anything.

- `verified` — reproduced as stated, inputs adequate
- `verified-modified` — arithmetic right, value updated (e.g. superseded external input)
- `uncertain` — with `uncertainty_oom: N`; propagate as an interval
- `hypothesis-violated` — item is fine; a downstream use site does not satisfy its hypotheses (record `at:`)
- `refuted`

Two orthogonal sub-fields where useful: `math_correct: yes|no` and `inputs_adequate: yes|no`.
The §7.4.2 case is `math_correct: yes, inputs_adequate: no` — do not collapse them.

## Imports

```yaml
imports:
  - from: "3.5/surface-continuum-models"   # id in another chapter; may not exist yet
    used_for: basis of the bounded continuum approach
    at: ["9.3.3"]                            # where in this chapter it is used
    hypotheses_discharged: unknown           # unknown | yes | no | n/a  (audit fills)
    notes: ...
```

An import whose `from` chapter has not been extracted is **pending** (fine). An import whose
`from` chapter *has* been extracted but contains no such id is **dangling** (reconciliation item).

## Single-writer rule

When extracting chapter N you edit **only** `chapters/chNN.yaml`. Never add stubs to other
chapters' files. Forward references go in your `consumed_by`; the reverse index is generated.
This is what makes reconciliation mechanical and extraction order-independent.

## Criticism register

`criticism/register.yaml`: a list of critiques and empirical results, each importing from chapters:

```yaml
- id: prase-2026-akhiezer
  kind: technical-critique   # technical-critique | experiment | field-state | defense | review
  author: ...
  date: ...
  url: ...
  targets: ["7.4.2/phonon-viscosity-small-except", "12/rod-logic-q"]   # export ids, may be pending
  claim: one paragraph
  status: unrebutted         # unrebutted | rebutted | partially-rebutted | superseded-by-experiment | straw-man-consensus | unread
  axis: ...                  # recurring dispute axis, see DECISIONS.md
  notes: ...
```
