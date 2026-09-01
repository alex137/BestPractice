<!-- Last updated: 2026-09-01 (Buenos Aires) by a follow-up session -->

# Brief — Bringing Mechanical Checks to the Private Sets

**Read this if you are a session opened directly against
`themorgan/precedent-individual` or `themorgan/precedent-team-maintainers`.**
It is written for exactly one of those sessions at a time — see
[Why this cannot run from Precedent](#why-this-cannot-run-from-precedent)
before you consider opening both, or opening one of them alongside this
repo.

It is committed here, in the public repo, rather than left in a chat thread,
because that is this repo's own `repo-is-memory`: a brief that exists only
in a conversation is already lost. It contains no private content and
cannot — the two practices this is written for live in the repositories it
describes, not here.

## The gap, stated plainly

Phase 3 populated the two private sets with one practice each. Phase 4 built
real, tested enforcement for the universal catalogue: 24 of 54 practices now
carry a `checked_by` backed by a test that plants the exact violation the
practice exists to prevent and proves it fires (see
[spec/ENFORCEMENT.md](ENFORCEMENT.md)). **Neither private set has any of
that.** Both of their practices currently carry `checked_by: null`, and no
infrastructure exists yet — in either private repo — to change that, because
the checking engine ([tools/precedent_check.py](../tools/precedent_check.py))
was built only against this repo's own tree.

[practices/checkable-gets-checked.md](../practices/checkable-gets-checked.md)
already states the standard every practice at every source should meet:

> Before a new practice is left `checked_by: null`, actually try to write
> the check — don't stop at the first plausible-sounding reason it can't be
> done, and don't wire one in without running it against the whole tree
> first... If it genuinely doesn't [have one], say so in the practice file,
> with the specific reason (not "too hard to check"), so the next session
> can tell a considered "no" from an unexamined one.

That standard is source-agnostic by design — a team or individual practice
is the same file format, with the same reachability question, as a
universal one. This brief is the missing piece: how to actually meet it
from inside a private repo, which has no `precedent_check.py` of its own
yet.

## Why this cannot run from Precedent

Same two structural reasons [spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md)
and [spec/SOURCES.md](SOURCES.md) already give for why the private sets had
to be *populated* from a session opened directly against them, not from
here:

- **A session cannot hold repositories from two owners with push access at
  once.** The two private sets belong to a different account than this one.
- **The plan forbids it regardless** ([PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md#risks)):
  *"Nothing from an individual or team set may be staged on this branch at
  any point, even transiently."* Reading a private practice's content into a
  session that also holds this branch, even just to write its check, is the
  exposure the whole arrangement exists to prevent.

So: one session, opened only against `precedent-individual` **or**
`precedent-team-maintainers` — never both at once with push access, and
never alongside this repo.

## What to bring with you (public, safe to read from either side)

You cannot hold this repo and the private one in the same session, but you
*can* read this repo's public files beforehand, or paste the relevant
pieces into the new session's context. Bring:

- **The shape of a check**, from [tools/precedent_check.py](../tools/precedent_check.py):
  a `Finding(where, detail)` result type, a `NotApplicable` exception for a
  check that cannot run (reported as SKIPPED, never as a silent pass), and
  the rule that **the failure message is the practice's own `## Rule` text,
  read through the same parser every other channel uses — never a
  paraphrase that can drift from it.**
- **The two-direction test discipline**, from `check_precedent_check_fires`
  in [tools/verify_harness.py](../tools/verify_harness.py): copy the tree
  (or just the one practice's target file) into a scratch copy, **plant**
  the exact violation the practice exists to prevent, require the check to
  fire; then require the **same check on the unplanted, current content** to
  come back clean. Skipping the second direction is how the first version of
  this repo's own `quick-index` check shipped silently broken — it would
  have fired on the planted violation perfectly while reporting zero rows on
  a real table of thirty-two, because nobody checked that it also passed
  clean content correctly.
- **The scopes vocabulary**, so the check's shape matches what the practice
  actually is: `change` (a property of what a diff adds or edits), `tree` (a
  property of the repo as it stands, checked every run), or `turn-end` (the
  state you wanted *after* an operation — excluded from routine runs, since
  mid-work isn't a violation).

You do not need to vendor `precedent_check.py` itself — it is written
against this repo's own file layout (`MAP.md`, `GLOSSARY.md`, its own
`practices/` directory) and none of that exists in a one-practice private
set. Write a small, standalone script instead; the shape above is what
carries over, not the file.

## A minimal scaffold

```python
#!/usr/bin/env python3
"""check_<slug>.py -- the mechanical check for practices/<slug>.md.

Exit 0 and print nothing when clean. Exit 1 and print the practice's own
Rule text (never a paraphrase) plus the specific finding(s) on a violation.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
PRACTICE_FILE = ROOT / "practices" / "<slug>.md"


def rule_text():
    text = PRACTICE_FILE.read_text(encoding="utf-8")
    m = re.search(r"## Rule\n(.*?)\n## ", text, re.S)
    return m.group(1).strip() if m else "(no Rule found)"


def find_violations() -> list[str]:
    """Return a finding string per violation found; empty list if clean."""
    findings = []
    # ... the actual check, specific to this one practice ...
    return findings


if __name__ == "__main__":
    findings = find_violations()
    if findings:
        print(f"VIOLATION: {PRACTICE_FILE.stem}")
        for f in findings:
            print(f"  {f}")
        print("\nthe rule:")
        print("  " + rule_text().replace("\n", "\n  "))
        sys.exit(1)
    sys.exit(0)
```

Test it exactly the way this repo tests its own 24 (adapt the paths to
whatever the practice actually governs — a file, a commit message pattern,
a repo-wide property):

```sh
# 1. Plant the violation in a scratch copy; require a non-zero exit.
cp -r . /tmp/scratch-planted && cd /tmp/scratch-planted
#   ... edit the scratch copy to introduce the exact violation ...
python3 check_<slug>.py; echo "exit: $?"   # must be 1

# 2. The real, current, unplanted content must stay clean.
cd -  # back to the real working copy
python3 check_<slug>.py; echo "exit: $?"   # must be 0
```

Only wire `checked_by: check_<slug>.py` into the practice's frontmatter
once **both** directions pass. If you can't get a real check to hold —
because the practice is a judgment call with no mechanical signature, the
same class `mistakes-become-rules`' proportionality guard already names as
resistant — leave `checked_by: null` and write the specific reason into the
practice's own `## Install` section, the same way
[practices/checkable-gets-checked.md](../practices/checkable-gets-checked.md)
documents its own resistance. "Too hard to check" is not a reason;
"this requires judging whether X, which no diff can show" is.

## How you'll know it's real, not a claim

This repo's own history is the cautionary tale, worth carrying with you:
before phase 4 tested them, 7 of 8 practices claiming `checked_by` in the
universal catalogue were not actually enforcing anything — a linter with no
such check in it, a check that only ever warns, gates that had been red so
long nobody ran them, a scan of an empty input set reporting a clean bill of
health (see [spec/ENFORCEMENT.md](ENFORCEMENT.md), "What phase 4 found
before it built anything"). The two-direction test above is what would have
caught every one of those on day one. Don't skip it because there's only
one practice to check — that repo also started from "this one's probably
fine."

## What comes back to Precedent, and what doesn't

**Nothing needs to.** The check script, its test, and the `checked_by`
value live entirely inside the private set — this repo never sees them, the
same way it never saw the private set's practice content. If the *pattern*
you land on turns out to be broadly useful — a shape of check other private
sets would want, or a case for promoting the practice itself toward team or
universal — that is a separate decision, made the normal way
([PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md#stage-4--approval-by-level)),
not a side effect of writing this check.
