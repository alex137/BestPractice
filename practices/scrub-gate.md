---
slug:        scrub-gate
title:       The proprietary scrub gate
tier:        on-demand
severity:    default
applies_to:  ["process/upstream/**"]
occasion:    "committing anything that touches the vendored/public tree"
index_clause: "the public tree is public-safe at all times, not just at check-in"
checked_by:  "tools/practice_audit.py"
defines:     []
status:      active
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
vocabulary), and [tools/practice_audit.py](tools/practice_audit.py) scans
the entire vendored tree against it on every run, failing loudly on any hit.
The blocklist itself is never exported (it is a map of the secrets). And a
public repo is **public from its first commit** — content is authored fresh
as public-safe, never migrated from private history, because visibility
flips expose everything a private repo ever casually committed.

## Detail

## Why
The abstraction step (practice 14) is a judgment call performed
repeatedly by agents under time pressure — exactly the conditions under
which practice 6 says a convention needs a loud audit. Public git history
cannot be un-published.

## Story

## Install
Blocklist format and gate wiring in [INSTALL.md](INSTALL.md).
Scrub before every commit that touches `process/`; re-run at check-in time
before opening the upstream PR.
