---
slug:        convention-to-audit
title:       A convention violated once becomes an audit that fails loudly
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a convention is violated for the first time"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 6
---
## Rule
Prose rules are advisory; a non-zero exit is not. The first time a
convention is violated with real cost, promote it to a script that detects the
violation and fails the build/merge — and keep the origin story in the
script's docstring.

## Why
Every audit in the originating repo exists because its rule was
broken once despite being written down: a status flag not flipped caused a
generated bundle to silently drop updated content; a renumbering left stale
cross-references undetected for weeks; a markdown footgun garbled an external
document. None recurred after promotion to an audit. The binding layer
matters as much as the check: a gate that lives only in a merge runbook
binds only the sessions that run the runbook — a PR merged through the
hosting platform's web UI skips it entirely (a dependent repo's first
member merges bypassed the capture and export gates exactly this way,
2026-08). A required CI check ([GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)) is
the form that binds every path to the default branch.

## Story

## Install
[tools/doc_lint.py](tools/doc_lint.py) and
[tools/practice_audit.py](tools/practice_audit.py) are audits of this kind
(and worked examples for writing your own). Run them before commit; wire them
into the merge runbook ([merge-runbook](merge-runbook.md)).
