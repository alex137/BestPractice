---
slug:        merge-runbook
title:       A merge runbook with fixed per-file-class rules
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A moment — routed by the `merge` gate instead. Decided: phase 4 routing pass."
occasion:    "merging a branch that touches shared files"
gates:       ["merge"]
gates_why:   "Fires when merging a branch that touches shared files."
index_clause: "write conflict resolution per file class, once, then follow it"
index_required: false
checked_by:  null
defines:     ["merge runbook"]
status:      active
in_force_at: null
visible_to:  code-owners
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
re-inspection, is what makes fast mechanical resolution safe; a catch-up review
(`## Detail`) covers the rules they cannot check. Authorization
to actually run this runbook is the user saying so, in whatever words they
use; a project where one fixed phrase carries that meaning should say so in
its own instructions file, where the people who use it will read it.

## Detail
**Bringing the trunk in includes a catch-up review** of what landed there
since the branch forked, because the audits enforce only the rules that have
a check. Two passes: **apply every rule that changed on the trunk** (the
practices, conventions and instructions files, a vendor update included) to
the files the branch changed, fixing them before the merge commits; and
**read the trunk's other work against the merge decision**, stopping to ask,
with a recommendation, when the trunk already did the same work, reversed a
decision the branch builds on, or moved a figure or design it relies on.
Record the fork point before merging; afterwards the merge base is the trunk
itself. The reply reports the outcome in one line.

## Why
The expensive part of an ad-hoc merge is not the time it takes. It is that **conflict resolution is judgment exercised under pressure, on exactly the files that matter most** — shared registries, indexes, logs — and that is where an entry quietly gets dropped rather than where anyone expects to make a mistake.

Writing the rules per file class once removes the judgment from the moment it is least reliable. A rule decided calmly, in the abstract, is applied mechanically under pressure.

The audit is what makes that mechanical application *safe* rather than merely fast, and the ordering matters: the audit has to pass before the merge commits, not after. Together they make fixed-rule resolution safer than careful manual inspection, which is the claim that justifies the whole practice — otherwise this would be a speed optimization bought with risk.

## Story
Every thread in the originating repo touched the same registry and
index files; conflicts were universal. Ad-hoc resolution was slow and once
dropped a registry entry. Fixed rules plus a loud audit made merges fast
*and* safer than careful manual resolution.

Later (2026-10-16), a person asked whether "merge" checked the trunk for
anything that should change the decision to merge, such as new practices
the branch's content should meet first. It did not: the trunk was merged in
and its audits ran, but a rule that relied on judgment and had landed while
the branch was open was never applied to the branch's content, and nothing
checked whether the trunk's other work overlapped or contradicted the
branch. The catch-up review was added to the Rule.

## Install
Runbook section in
[templates/AGENTS.md.template](https://github.com/alex137/BestPractice/blob/staging/templates/AGENTS.md.template); adapt the file
classes to your repo.
