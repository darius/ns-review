#!/usr/bin/env python3
"""Validate chapters/*.yaml and criticism/register.yaml; generate generated/INDEX.md.

Checks (exit nonzero on hard errors):
  - schema: required fields, enum values, id format <section>/<mnemonic>, id's chapter matches file
  - duplicate ids across chapters
  - hypotheses that name an id: the id must exist (or be pending in an unextracted chapter)
  - imports: pending (from-chapter not extracted) vs DANGLING (extracted, id absent)
  - consumed_by: for each extracted target chapter, whether an import back to this id exists
    (unconfirmed forward refs are reported, not errors)
  - scope-condition exports neither listed as a hypothesis nor imported (warning: orphan condition)
Generates: reverse index (who imports / who attacks each export), negative-claims register,
support-type stats, pending/dangling lists.
"""
import re, sys
from collections import defaultdict
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
TYPES = {"parameter", "proposition", "construction", "scope-condition", "design-license"}
SUPPORT = {"INT", "EXT", "BARE"}
STATUS = {"extracted", "reconciled", "audited"}
VERDICTS = {None, "verified", "verified-modified", "uncertain", "hypothesis-violated", "refuted"}
ID_RE = re.compile(r"^(\d+(?:\.\d+)*[a-z]?)/([a-z0-9][a-z0-9.-]*)$")

errors, warnings = [], []


def err(m): errors.append(m)
def warn(m): warnings.append(m)


def chapter_of(id_: str) -> int | None:
    m = ID_RE.match(id_)
    return int(m.group(1).split(".")[0]) if m else None


def load_chapters():
    chapters = {}
    for p in sorted((ROOT / "chapters").glob("ch*.yaml")):
        d = yaml.safe_load(p.read_text())
        n = d.get("chapter")
        if not isinstance(n, int):
            err(f"{p.name}: missing/invalid 'chapter'"); continue
        if d.get("status") not in STATUS:
            err(f"{p.name}: status must be one of {sorted(STATUS)}")
        if d.get("coverage") == "partial" and not d.get("sections"):
            err(f"{p.name}: coverage: partial requires 'sections'")
        for ex in d.get("exports", []):
            for f in ("id", "type", "section", "statement", "support", "polarity"):
                if f not in ex:
                    err(f"{p.name}: export {ex.get('id','?')} missing '{f}'")
            i = ex.get("id", "")
            if not ID_RE.match(i):
                err(f"{p.name}: bad id format '{i}' (want <section>/<mnemonic>)")
            elif chapter_of(i) != n:
                err(f"{p.name}: id '{i}' does not belong to chapter {n}")
            if ex.get("type") not in TYPES: err(f"{p.name}: {i}: bad type {ex.get('type')}")
            if ex.get("support") not in SUPPORT: err(f"{p.name}: {i}: bad support {ex.get('support')}")
            if str(ex.get("polarity")) not in {"+", "-"}: err(f"{p.name}: {i}: polarity must be '+' or '-'")
            if ex.get("verdict") not in VERDICTS: err(f"{p.name}: {i}: bad verdict {ex.get('verdict')}")
            if ex.get("support") == "EXT" and not ex.get("vintage"):
                warn(f"{i}: EXT support without 'vintage'")
        for im in d.get("imports", []):
            if "from" not in im or "used_for" not in im:
                err(f"{p.name}: import missing 'from'/'used_for': {im}")
            if im.get("cited", True) not in (True, False):
                err(f"{p.name}: import {im.get('from')}: 'cited' must be yes/no")
            if im.get("verdict") not in VERDICTS:
                err(f"{p.name}: import {im.get('from')}: bad verdict {im.get('verdict')}")
        chapters[n] = d
    return chapters


def load_criticism():
    p = ROOT / "criticism" / "register.yaml"
    return yaml.safe_load(p.read_text()) if p.exists() else []


def main():
    chapters = load_chapters()
    crit = load_criticism()
    extracted = set(chapters)

    def covered(id_: str) -> bool:
        """Is the section of this id inside the extracted coverage of its chapter?"""
        c = chapter_of(id_)
        if c not in chapters: return False
        d = chapters[c]
        if d.get("coverage", "full") != "partial": return True
        sec = ID_RE.match(id_).group(1)
        return any(sec == s or sec.startswith(s + ".") for s in d["sections"])
    exports = {}          # id -> (chapter, export)
    for n, d in chapters.items():
        for ex in d.get("exports", []):
            if ex["id"] in exports:
                err(f"duplicate id {ex['id']} in ch{n} and ch{exports[ex['id']][0]}")
            exports[ex["id"]] = (n, ex)

    # --- hypotheses referencing ids
    hyp_refs = defaultdict(list)   # condition id -> [item ids that depend on it]
    for i, (n, ex) in exports.items():
        for h in ex.get("hypotheses") or []:
            if isinstance(h, str) and ID_RE.match(h):
                hyp_refs[h].append(i)
                c = chapter_of(h)
                if h not in exports and covered(h):
                    err(f"{i}: hypothesis '{h}' names an id absent from extracted ch{c}")

    # --- imports: pending vs dangling; reverse index
    importers = defaultdict(list)  # export id -> [(chapter, at, cited, verdict)]
    pending, dangling, inferred = [], [], []
    for n, d in chapters.items():
        for im in d.get("imports", []):
            f = im["from"]; c = chapter_of(f)
            if c is None:
                err(f"ch{n}: import from '{f}' is not a valid id"); continue
            if im.get("cited", True) is False:
                inferred.append((n, f, im.get("hypotheses_discharged", "unknown"), im.get("verdict")))
            if f in exports:
                importers[f].append((n, im.get("at", []), im.get("cited", True), im.get("verdict")))
            elif covered(f):
                dangling.append((n, f, im.get("used_for", "")))
            else:
                pending.append((n, f, im.get("used_for", "")))
    for n, f, u in dangling:
        err(f"DANGLING import in ch{n}: '{f}' (ch{chapter_of(f)} is extracted but has no such id) — {u}")
    # an imported scope-condition has a use site; only one nobody lists or imports is orphaned
    for i, (n, ex) in exports.items():
        if (ex["type"] == "scope-condition" and i not in hyp_refs and i not in importers
                and ex["section"] != str(n)):
            warn(f"orphan scope-condition {i}: no export lists it as a hypothesis and no chapter imports it")

    # --- consumed_by confirmation (section-aware: a claim into a partially extracted chapter is
    #     checkable only if the named section lies inside the extracted coverage)
    unconfirmed, unconfirmed_by_chapter = [], defaultdict(int)
    def checkable(tgt: str):
        m = re.match(r"^(\d+(?:\.\d+)*)", str(tgt).strip())
        if not m: return None
        sec = m.group(1); c = int(sec.split(".")[0])
        if c not in chapters: return None
        d = chapters[c]
        if d.get("coverage", "full") != "partial": return c
        return c if any(sec == s or sec.startswith(s + ".") for s in d["sections"]) else None
    for i, (n, ex) in exports.items():
        for tgt in ex.get("consumed_by") or []:
            c = checkable(tgt)
            if c is not None and c != n and not any(k == c for k, *_ in importers.get(i, [])):
                unconfirmed.append((i, tgt)); unconfirmed_by_chapter[n] += 1

    # --- reconciliation readiness: no dangling imports, no unconfirmed checkable forward claims
    dangling_by_chapter = defaultdict(int)
    for n, f, u in dangling: dangling_by_chapter[n] += 1
    reconcilable = {n: (dangling_by_chapter[n] == 0 and unconfirmed_by_chapter[n] == 0) for n in chapters}
    for n, d in chapters.items():
        if d["status"] in ("reconciled", "audited") and not reconcilable[n]:
            err(f"ch{n} is marked {d['status']} but has {dangling_by_chapter[n]} dangling imports "
                f"and {unconfirmed_by_chapter[n]} unconfirmed forward claims")

    # --- criticism
    attackers = defaultdict(list)
    for e in crit:
        for t in e.get("targets") or []:
            attackers[t].append(e["id"])
            c = chapter_of(t)
            if c is None: err(f"criticism {e['id']}: bad target id '{t}'")
            elif t not in exports and covered(t):
                warn(f"criticism {e['id']}: target '{t}' absent from extracted ch{c}")

    # --- stats
    stats = defaultdict(lambda: defaultdict(int))
    for i, (n, ex) in exports.items():
        stats[n][ex["support"]] += 1; stats[n]["total"] += 1
        if ex["polarity"] == "-": stats[n]["neg"] += 1
        if ex["polarity"] == "-" and ex["support"] == "BARE": stats[n]["neg_bare"] += 1

    # --- write INDEX.md
    out = ["# Generated index — do not edit (tools/build.py)\n"]
    out.append("## Coverage\n")
    for n, d in sorted(chapters.items()):
        cov = d.get("coverage", "full")
        secs = f" ({', '.join(d['sections'])})" if cov == "partial" else ""
        s = stats[n]
        rec = "" if d["status"] != "extracted" else (" — reconcilable" if reconcilable[n] else
              f" — NOT reconcilable ({dangling_by_chapter[n]} dangling, {unconfirmed_by_chapter[n]} unconfirmed forward claims)")
        out.append(f"- **Ch. {n}** {d.get('title','')} — {d['status']}, {cov}{secs}: "
                   f"{s['total']} exports, INT {s['INT']} / EXT {s['EXT']} / BARE {s['BARE']} "
                   f"({100*s['BARE']//max(s['total'],1)}% bare); negative {s['neg']} (bare-negative {s['neg_bare']}){rec}")
    out.append("\n## Priority audit set — negative & bare\n")
    for i, (n, ex) in sorted(exports.items()):
        if ex["polarity"] == "-" and ex["support"] == "BARE":
            pr = ex.get("priority", "normal")
            out.append(f"- `{i}` [{pr}] {ex['statement'].strip()[:140]}")
    out.append("\n## Reverse index — who depends on each export\n")
    for i, (n, ex) in sorted(exports.items()):
        rows = []
        for k, at, cited, verdict in importers.get(i, []):
            tag = "" if cited else " (inferred, not cited)"
            v = f" — verdict: {verdict}" if verdict else ""
            rows.append(f"imported by ch{k} at {', '.join(at) or '?'}{tag}{v}")
        for dep in hyp_refs.get(i, []):
            rows.append(f"hypothesis of `{dep}`")
        for a in attackers.get(i, []):
            rows.append(f"attacked by `{a}`")
        for tgt in ex.get("consumed_by") or []:
            rows.append(f"(book/forward) consumed by {tgt}")
        if rows:
            out.append(f"- `{i}` ({ex['type']}, {ex['support']}, {ex['polarity']})")
            out.extend(f"    - {r}" for r in rows)
    out.append("\n## Pending imports (source chapter not yet extracted)\n")
    for n, f, u in sorted(pending):
        out.append(f"- ch{n} <- `{f}` — {u}")
    out.append("\n## Inferred imports (dependency not acknowledged in the text)\n")
    for n, f, hd, v in sorted(inferred):
        hd = {True: "yes", False: "no"}.get(hd, hd)
        out.append(f"- ch{n} <- `{f}` — hypotheses discharged: {hd}" + (f"; verdict: {v}" if v else ""))
    out.append("\n## Verdicts recorded\n")
    for i, (n, ex) in sorted(exports.items()):
        if ex.get("verdict"):
            out.append(f"- `{i}`: **{ex['verdict']}**")
    for n, d in sorted(chapters.items()):
        for im in d.get("imports", []):
            if im.get("verdict"):
                out.append(f"- ch{n} <- `{im['from']}`: **{im['verdict']}**")
    out.append("\n## Unconfirmed forward references (book says consumed, target chapter extracted, no import found)\n")
    for i, tgt in unconfirmed:
        out.append(f"- `{i}` → {tgt}")
    out.append("\n## Criticism targets pending extraction\n")
    for e in crit:
        for t in e.get("targets") or []:
            if t not in exports:
                out.append(f"- `{e['id']}` → `{t}`")
    if warnings:
        out.append("\n## Warnings\n"); out.extend(f"- {w}" for w in warnings)
    (ROOT / "generated").mkdir(exist_ok=True)
    (ROOT / "generated" / "INDEX.md").write_text("\n".join(out) + "\n")

    print(f"exports: {len(exports)}  imports pending: {len(pending)}  dangling: {len(dangling)}  "
          f"unconfirmed forward claims: {len(unconfirmed)}  criticism entries: {len(crit)}  "
          f"warnings: {len(warnings)}  errors: {len(errors)}")
    for w in warnings: print("  warn:", w)
    for e in errors: print("  ERROR:", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
