---
date:        2026-09-03
question:    Switching the leak gate's vocabulary layer on for real against
             precedent-individual's current tree found 36 hits (not the 45
             first reported — that count reflected an earlier state), all
             on three patterns: `morgan@westegg\.com`, `\bwestegg\.com\b`,
             and `\bMorgan\s+F\b`. Are these a miscalibrated blocklist, or
             has it just never run clean?
decision:    Narrowed. All 36 hits collided with this branch's own
             by-design identity content — the `commit-author`/
             `buenos-aires-dates` practices' own Rule text quoting the
             actual values, `check_commit_author.py`'s hardcoded expected
             constants, and `approved_by:` frontmatter on every practice
             file — not real leaks. Removed those three patterns from the
             blocklist. `\bmorganfriedman\b` and `\b6497032\b` stay
             blocked: zero observed collisions, no evidence to loosen them.
alternatives: ["Leave all patterns blocked and add per-file exemptions for
               the colliding practice files instead", "Treat the 36 hits as
               a sign the gate needs a broader by-design-content carve-out
               mechanism rather than pattern-by-pattern removal"]
decided_by:  Morgan
---

## Why this needed a decision rather than a quiet fix

Loosening a leak-gate pattern is exactly the kind of change that looks safe
in the moment and is expensive if wrong — the blocklist exists to catch
something that cannot be un-published once it leaks. It needed the same
evidence-based treatment as the prior `themorgan`/`Buenos Aires` narrowing:
look at what actually collided, not just make the gate quieter.

## What was found

All three removed patterns collided with content this repo intentionally
carries in the open — practice files that document, by design, the exact
values the check exists to detect (so the practice's own text and the
check's own hardcoded constants necessarily contain them), plus
`approved_by:` frontmatter that is not private content at all. None of the
36 hits were an actual leak of anything not already meant to be public.

## What stays blocked, and why

`\bmorganfriedman\b` and `\b6497032\b` were not touched — neither had any
observed collision with by-design repo content, so there is no evidence
they are miscalibrated. Narrowing is done per-pattern, on evidence, not as
a blanket loosening.

## Outcome

Landed via [precedent-individual#10](https://github.com/themorgan/precedent-individual/pull/10),
merged. Re-running the vocabulary layer against the real tree afterward
comes back with zero hits.
