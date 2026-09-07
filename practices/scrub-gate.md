---
slug:        scrub-gate
title:       The proprietary scrub gate
tier:        on-demand
severity:    default
applies_to:  ["process/upstream/**"]
occasion:    "committing anything that touches the vendored/public tree"
gates:       ["merge", "push"]
index_clause: "the public tree is public-safe at all times, not just at check-in"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 15
---
## Rule
When the dependent repo is private and this repo is public,
everything under `process/upstream/` must be public-safe **at all times** —
not just at check-in. Contributions are patterns and abstracted lessons
only: no names, code words, identifiers, numbers, or incident text from the
dependent repo's subject matter. Enforcement is mechanical: the dependent
repo keeps `process/scrub_blocklist.txt` (regex per line — its private
vocabulary), and [tools/practice_audit.py](../tools/practice_audit.py) scans
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

## Install
Blocklist format and gate wiring in [INSTALL.md](../INSTALL.md).
Scrub before every commit that touches `process/`; re-run at check-in time
before opening the upstream PR.
