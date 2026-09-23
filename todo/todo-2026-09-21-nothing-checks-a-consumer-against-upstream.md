---
slug:              todo-2026-09-21-nothing-checks-a-consumer-against-upstream
kind:              manual
domain:            vendoring
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

**Every check in this system runs inside one repository.** Nothing compares
a consuming repo against the upstream it vendored from. That is the
structural reason a `very-deep-check` has never found a stale vendored
tree -- not a gap in its passes, a gap in what any pass can see.

Answering Morgan's questions of 2026-09-21 precisely, because several of
them have a better answer than expected and one has a worse one:

**Deletions of ENGINE files DO propagate, automatically.**
`_remove_dropped_engine_files` diffs the PREVIOUS manifest's `files`
against the current kind's list -- so dropping a name from `ENGINE_FILES`
deletes it from every consumer on its next `refresh()`, with or without a
`RETIRED_ENGINE_FILES` tombstone. A hand-edited copy is kept and reported
rather than deleted. This is stronger than assumed.

**Deletions of CI WORKFLOW files do NOT, unless someone writes a
tombstone.** `_remove_retired_ci_workflow_files` is driven entirely by the
`RETIRED_CI_WORKFLOW_FILES` dict. There is no manifest diff on that path.
**A CI template dropped from `CI_WORKFLOW_TEMPLATES` without a matching
tombstone entry leaves the installed file in every repo, forever, tracked
by nothing.** That asymmetry between the two paths is the concrete gap.

**Neither propagates until `refresh()` runs in that repo**, and nothing
anywhere reports which repos have not refreshed. A fix merged upstream
reaches an installed repo only when a session goes there and runs "Update
Vendors". On 2026-09-20, 18 of 22 repos had never done so.

**The files that started this were never ours.** `light-check.yml` and the
rest were never Precedent templates, so no retirement mechanism could ever
have removed them -- they were live, repo-local checks, and deleting them
was the error ([spec/CI_MINUTES_PLAN.md](../spec/CI_MINUTES_PLAN.md) item
14). The only genuinely retired Precedent workflow is `views-drift.yml`,
and that one is handled.

## Why It Matters

Three defects shipped in one template in two days, each reaching or nearly
reaching real repositories, and each was caught by a session verifying a
claim rather than by any mechanism. `shipped-template-carries-its-script`
(added 2026-09-21) now closes one of the three. The other two -- a
self-declared field that was wrong, and a manifest read that ignored one of
two files -- were caught by reading, and nothing would have caught them
otherwise.

## What Would Close It

Three pieces, smallest first:

1. **Give the CI-workflow path the same manifest diff the engine path
   has**, so a dropped template propagates its deletion without anyone
   remembering a tombstone. The tombstone stays for the case a diff cannot
   express (a rename), exactly as `RETIRED_ENGINE_FILES` does.

2. **A carry-through report a session runs IN a consuming repo**: compare
   `ENGINE_MANIFEST.json`'s recorded upstream commit against the live
   upstream, and name every engine file added, removed or changed since --
   so "did this reach us" is one command, not an audit.

3. **A staleness roll-up.** Nothing today can answer "which of my repos are
   behind, and by how much" without visiting each. Whether that belongs in
   this repo at all is open -- it needs cross-repo read access this
   repository deliberately does not have.

Morgan's framing, 2026-09-21: an iron law that every change is tested for
whether it carries through to the vendored-in versions. Items 1 and 2 are
the mechanical half of that; the law without them is a reminder, and
reminders are what failed here.

## Progress (2026-09-21, PR #513)

**Items 1 and 2 are built and merged.** Item 3 is the whole remaining item.

**1 — CI-workflow deletions propagate.**
[precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
`_remove_retired_ci_workflow_files()` now diffs the manifest's recorded
`ci_workflow_files` against what the kind actually ships and removes the
difference, the same way the engine path has always diffed
`ENGINE_MANIFEST.json`. The tombstone list stays for what a diff cannot
express. `kind` comes from the caller, not from the manifest: during a
source-to-consumer conversion the manifest still names the old kind, and
reading it there removes the wrong set. The harness caught exactly that.

**2 — the carry-through report exists**, as
[precedent_engine_freshness.py](../tools/precedent_engine_freshness.py).
It reads the manifest's `source_commit`, `ls-remote`s the pinned branch
tip, and says how far behind the repo is; `--files` names every engine
file added, removed or changed since, marking anything upstream ships that
this repo does not as `(NOT YET VENDORED HERE)`. It never refreshes
anything and exits 0 in every failure mode, including no network — a
freshness notice that can fail a build is a notice people turn off. Wired
into the session-start hook and into
[precedent_gate.py](../tools/precedent_gate.py)'s push and merge moments,
both `--quiet`.

**3 — the staleness roll-up is NOT built**, and the open question in it is
unchanged: answering "which of my repos are behind, and by how much"
needs cross-repo read access this repository deliberately does not have.
Nobody has decided whether it belongs here at all. That decision is what
this item now waits on.

2026-09-23: **2 now covers every declared source, not only the engine.**
Alex asked for the general form ("patent-system won't be our last") after a
consumer that declared a second shared set turned out to have no freshness
check on either of its halves -- the set's practices resolve from a sibling
clone, its code is vendored under `process/<name>/` with its own manifest,
and both the engine notice and `checkin.py fresh` read one manifest each.
[precedent_engine_freshness.py](../tools/precedent_engine_freshness.py)
now reads `precedent.json` and reports one row per way each declared
source is reached: the engine manifest, a
vendored tree's `process/manifest*.json`, and a live clone at the declared
path (its HEAD against origin, with the fetch command, since a stale clone
loads stale rules). Repo-local is skipped; a source declared but neither
vendored nor cloned is reported as absent rather than silently current.
`templates/bootstrap.sh` now runs it `--quiet` at session start for every
consumer, which the earlier wiring did not (only this repo's own hook
called it). Planted end to end in the harness
(`check_freshness_covers_every_declared_source`). Its first real run found
that consumer's shared-set code one commit behind the set's `main`. Item 3
is unchanged.
