---
slug:        convention-to-audit
title:       A convention violated once becomes an audit that fails loudly
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a convention is violated for the first time"
gates:       ["review"]
index_clause: "promote a costly broken convention to a script that exits non-zero"
checked_by:  null
defines:     []
status:      active
in_force_at: null
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

## Detail

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
2026-08). A required CI check ([GITHUB_ACTIONS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/GITHUB_ACTIONS.md)) is
the form that binds every path to the default branch.

## Story
**Every audit in the originating repo exists because its rule was broken
once despite being written down.** Three of them, each a different shape of
the same failure: a status flag that was not flipped, which made a generated
bundle silently drop updated content; a renumbering that left stale
cross-references undetected for weeks; and a markdown footgun that garbled
an external document. None of the three recurred after being promoted to an
audit, which is the evidence the rule rests on.

**The binding layer turned out to matter as much as the check**, and that
was learned separately and later. A gate living only in a merge runbook
binds only the sessions that actually run the runbook -- a pull request
merged through the hosting platform's web interface skips it entirely. A
dependent repo's first member merges bypassed the capture and export gates
exactly that way in 2026-08.

That is why the rule names a required continuous-integration check as the
form to reach for rather than any non-zero exit: it is the only form that
binds every path to the default branch, including the paths that do not
involve a session at all.

## Install
[tools/doc_lint.py](../tools/doc_lint.py) and
[tools/practice_audit.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/practice_audit.py) are audits of this kind
(and worked examples for writing your own). Run them before commit; wire them
into the merge runbook ([merge-runbook](merge-runbook.md)).
