---
slug:        merge-runbook
title:       A merge runbook with fixed per-file-class rules
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "merging a branch that touches shared files"
gates:       ["merge"]
index_clause: "write conflict resolution per file class, once, then follow it"
checked_by:  null
defines:     ["merge runbook"]
status:      active
in_force_at: null
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
audits ([convention-to-audit](convention-to-audit.md)) must pass before the merge commits — the audit, not
re-inspection, is what makes fast mechanical resolution safe. Authorization
to actually run this runbook is the user saying so, in whatever words they
use; a project where one fixed phrase carries that meaning should say so in
its own instructions file, where the people who use it will read it.

## Detail

## Why
The expensive part of an ad-hoc merge is not the time it takes. It is that **conflict resolution is judgment exercised under pressure, on exactly the files that matter most** — shared registries, indexes, logs — and that is where an entry quietly gets dropped rather than where anyone expects to make a mistake.

Writing the rules per file class once removes the judgment from the moment it is least reliable. A rule decided calmly, in the abstract, is applied mechanically under pressure.

The audit is what makes that mechanical application *safe* rather than merely fast, and the ordering matters: the audit has to pass before the merge commits, not after. Together they make fixed-rule resolution safer than careful manual inspection, which is the claim that justifies the whole practice — otherwise this would be a speed optimization bought with risk.

## Story
Every thread in the originating repo touched the same registry and
index files; conflicts were universal. Ad-hoc resolution was slow and once
dropped a registry entry. Fixed rules plus a loud audit made merges fast
*and* safer than careful manual resolution.

## Install
Runbook section in
[templates/AGENTS.md.template](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/AGENTS.md.template); adapt the file
classes to your repo.
