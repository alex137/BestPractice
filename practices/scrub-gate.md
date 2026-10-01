---
slug:        scrub-gate
title:       The proprietary scrub gate
tier:        on-demand
severity:    default
applies_to:  ["process/upstream/**"]
applies_to_why: "Set at phase 1 from the Install text, which named a path unambiguously. Decided: phase 1."
occasion:    "committing anything that touches the vendored/public tree"
gates:       ["merge", "push"]
gates_why:   "The public tree must be clean at merge and at push, which are the two moments it can be checked. index_required: false: those gates and its path still reach it, and the process/upstream/** tree it was built on is in no repository here any more; its merge with private-repo-scrub is still to do. Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: decided)."
index_clause: "the public tree stays public-safe always, not just at check-in"
index_required: false
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork); index line dropped: Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: decided)"
source_practice_number: 15
---
## Rule
When the dependent repo is private and this repo is public,
everything under `process/upstream/` must be public-safe **at all times** —
not just at check-in. Contributions are patterns and abstracted lessons
only: no names, code words, identifiers, numbers, or incident text from the
dependent repo's subject matter. Enforcement is mechanical: the dependent
repo keeps `process/scrub_blocklist.txt` (regex per line — its private
vocabulary), and [tools/practice_audit.py](https://github.com/alex137/BestPractice/blob/staging/tools/practice_audit.py) scans
the entire vendored tree against it on every run, failing loudly on any hit.
The blocklist itself is never exported (it is a map of the secrets). And a
public repo is **public from its first commit** — content is authored fresh
as public-safe, never migrated from private history, because visibility
flips expose everything a private repo ever casually committed.

## Detail

## Why
The abstraction step ([practice-export-loop](practice-export-loop.md)) is a judgment call performed
repeatedly by agents under time pressure — exactly the conditions under
which [convention-to-audit](convention-to-audit.md) says a convention needs a loud audit. Public git history
cannot be un-published.

## Story
No dated incident was recorded for this rule itself, and the argument is
made from the conjunction of two properties rather than from a leak.

**The abstraction step is a judgment call performed repeatedly by agents
under time pressure.** That is precisely the condition `convention-to-audit`
identifies as the point where a written convention stops being enough and
has to become a loud, mechanical gate.

**And the consequence is irreversible: public git history cannot be
un-published.** Most rules in this catalogue guard against something
expensive to fix. This one guards against something that cannot be fixed at
all, which is why the requirement is *public-safe at all times* rather than
public-safe at check-in. A tree that is only scrubbed when somebody
remembers to check in is a tree that is unscrubbed for most of its life,
and any push during that window is the failure.

Later evidence bore the design out. Switching a private vocabulary
blocklist on against a real tree for the first time found live hits in a
public repo's own tracked files -- exactly what a gate that runs only at
check-in would have let through.

**Off the occasion index from 2026-10-01** (`index_required: false`). The reduction pass for precedent-individual's session-start file ([the session-file open item](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-30-session-file-cut-to-4000.md)) found this built on `process/upstream/**` and `process/scrub_blocklist.txt`, which no repository here has any more, and Morgan approved merging it with the repo-maintenance set's private-repo-scrub around what is in force now. That merge spans two repositories and a rewrite, so this step only drops the index line; its merge and push gates and its path still reach it, and the merge is recorded as still to do in the open item. Morgan (strength: decided): *"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)"*

## Install
Blocklist format and gate wiring in [INSTALL.md](https://github.com/alex137/BestPractice/blob/staging/INSTALL.md).
Scrub before every commit that touches `process/`; re-run at check-in time
before opening the upstream PR.
