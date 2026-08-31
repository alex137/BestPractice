---
slug:        merge-runbook
title:       A merge runbook with fixed per-file-class rules
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "merging a branch that touches shared files"
checked_by:  null
defines:     ["merge runbook"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 9
---
## Rule
When many branches touch the same shared files, merge conflicts are
expected — so resolution rules are written down per file class, once, and
followed without re-derivation: registries take the **union** of both sides;
logs are **append-only, keep both**; the same content file edited on both
sides keeps both sides' additions (renumbering the side not yet referenced
elsewhere); **generated outputs are never hand-merged** (the side matching
the committed manifest wins; unshipped builds are deleted and rebuilt). The
audits (practice 6) must pass before the merge commits — the audit, not
re-inspection, is what makes fast mechanical resolution safe.

## Why
Every thread in the originating repo touched the same registry and
index files; conflicts were universal. Ad-hoc resolution was slow and once
dropped a registry entry. Fixed rules plus a loud audit made merges fast
*and* safer than careful manual resolution.

## Story

## Install
Runbook section in
[templates/AGENTS.md.template](templates/AGENTS.md.template); adapt the file
classes to your repo.
