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
**everything the session has delivered**, not only what this merge carries:
work it landed in an earlier merge is reviewed too, and anything a new rule
now faults is fixed in this merge, by the session that knows why it was
written that way. Work other sessions delivered is not its to sweep. And
**read the trunk's other work against the merge decision**, stopping to ask,
with a recommendation, when the trunk already did the same work, reversed a
decision the branch builds on, or moved a figure or design it relies on.
Record the fork point before merging; afterwards the merge base is the trunk
itself. The reply reports the outcome in one line.

**In a repository on the Precedent loader, the runbook is this** (it was
the AGENTS.md template's "Merging a thread branch" section until
2026-10-31, and is kept here word for word in substance):

0. **Capture gate -- before the merge, in the thread that did the work**
   ([capture-gate](capture-gate.md)): fold now any document update,
   registry entry or decision record the work implied, and run the
   repository's parking-lot grep. **0b. Export gate**
   ([practice-export-loop](practice-export-loop.md)): a *generic*
   improvement goes into the vendored universal copy and upstream with
   `python3 tools/checkin.py push <upstream-clone> --why "<what went
   wrong>"`, then `python3 tools/precedent_sync_views.py --repo .` picks it
   back up once it lands.
1. Fetch and merge the default branch locally.
2. Resolve by the per-file-class rules above. **Renumbering is
   repo-wide:** when sections are renumbered, grep every doc --
   instructions, map, glossary, open items, not just the content file
   itself -- for the old numbers and update them in the same commit
   (observed 2026-08: a reorganization updated an index row but left two
   stale section references standing in the instructions file). **The
   generated `<!-- BEGIN GENERATED: precedent-loader -->` block is never
   hand-merged**: re-run `python3 tools/precedent_sync_views.py --repo .`,
   never hand-resolve its own conflict markers.
3. Run the audits -- **all must pass before the merge commits**: the
   repository's own audit commands and `python3
   tools/precedent_sync_views.py --repo . --check`.
4. Commit the merge, push, land per the repository's convention.

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
branch. The catch-up review was added to the practice. The same person then asked that it
cover the session's earlier merges as well, since a new rule can fault work
already landed, and that the session adding a rule sweep existing work once
([rule-level-by-reach](rule-level-by-reach.md)) rather than every merge
sweeping everything.

**2026-10-31: the template's runbook section came here.** A reduction pass
in a consuming repository found the AGENTS.md template's "Merging a thread
branch" section copied word for word into every repository, about 530
tokens each, while this practice already loaded at the merge gate. Morgan
approved moving template sections that practices carry into the practices
(strength: decided). The lines this practice lacked -- the loader-specific
steps, the repo-wide renumbering rule and the generated block -- moved into
Detail above; the template keeps a one-line pointer.

## Install
Nothing to write: the `merge` gate prints this practice. A repository with
file classes of its own adds them in a local add-on practice (`adds_to:
merge-runbook`).
