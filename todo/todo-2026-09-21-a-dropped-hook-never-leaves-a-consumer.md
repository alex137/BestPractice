---
slug:              todo-2026-09-21-a-dropped-hook-never-leaves-a-consumer
kind:              manual
domain:            vendoring
severity:          medium
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Build the third removal path -- Morgan, 2026-09-22: \"can you fix that bug?\""
decision_strength: decided
waiting_on:        null
noted:             2026-09-21
closed:            2026-09-22
---
## What

**A hook dropped upstream stays installed in every consumer, forever.**
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) has
exactly two removal paths — `_remove_dropped_engine_files` for `tools/` and
`_remove_retired_ci_workflow_files` for `.github/workflows/`. There is no
third for `.claude/hooks/`, and the manifest's own `hook_files` /
`hooks_sha256` keys go on recording the orphan with nothing that will ever
clear them.

Found 2026-09-21 by the very deep check's new deletion-propagation table
(`very-deep-check` pass 2, item 8b) on the first run of the question it
asks — which is the same question that exposed the CI-workflow asymmetry
the day before.

## The three columns, for hooks

| | Reaches an installed repo? |
|---|---|
| **Addition** | **No** — a hook is vendored only into a repo whose `settings.json` already wires that name, and a new hook cannot be wired to a file that is not there yet. Already filed as [todo-2026-09-21-a-new-hook-cannot-reach-an-installed-consumer](todo-2026-09-21-a-new-hook-cannot-reach-an-installed-consumer.md) |
| **Change** | Yes — a wired hook is rewritten on every refresh |
| **Deletion** | **No** — no mechanism exists |

## Why it matters

This is the shape the CI-workflow path had until 2026-09-21, and that one
cost real checks: a template dropped from the shipping list without a
tombstone left the installed file in every repository, tracked by nothing,
looking exactly as intentional as a live one. A hook is worse in one
respect — it **runs**, on every session, in every repo that still carries
it, long after upstream stopped shipping it.

Nothing is known to be affected today; no hook has been dropped since the
mechanism was measured. This is the gap, not an incident.

## What would close it

Mirror `_remove_dropped_engine_files` for hooks: diff the previous
manifest's `hook_files` against what the current `HOOK_SOURCE_DIR` ships
*and* what the destination still wires, delete the difference where the
on-disk hash still matches what the manifest recorded, and keep a
hand-edited copy with a warning rather than deleting it — the same standard
the engine path already uses. It wants a planted harness case in both
directions, as the dependent-reporting case got.

**Not done here** because it changes what a refresh does to somebody else's
repository, which is a bigger step than the check that found it.

## Closed 2026-09-22 — the third removal path exists

`_remove_dropped_hook_files` in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
mirrors the engine path: a hook the previous manifest recorded that
**upstream no longer ships** is deleted when its on-disk hash still matches
what the manifest recorded, kept and reported when it has been hand-edited
since, and the manifest loses the name either way so the next refresh does
not re-report it. Removals go through `_warn_about_dependents`, so anything
still naming the hook is named at the moment it goes.

**Two guards, both of which the case list proves.** The sweep keys on what
upstream **ships**, never on what this repo **wires** — un-wiring is the
repo's own act, and `hooks-on-disk-are-reachable` already reports the orphan
it leaves. And an **empty** upstream `hooks/` sweeps nothing: a directory
that globs to zero is indistinguishable from a checkout that cannot see
upstream, and reading it the other way would delete every hook in the
consumer.

**The very deep check now sees it coming too.** `DELETIONS PENDING` counts
hooks alongside engine files and CI workflows, so a hook about to be removed
on the next refresh — and whatever still names it — is reported before the
refresh runs, not after.

Harness: `check_vendor_engine_removes_a_hook_upstream_dropped`, five stated
cases covering deletion, the manifest record, the still-shipped hook left
alone, the hand-edited copy kept, and the empty-upstream refusal.

