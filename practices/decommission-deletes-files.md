---
slug:        decommission-deletes-files
title:       "Decommissioning a mechanism deletes its files, once an audit says nothing points at them"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "decommissioning a mechanism — a workflow, a tool, a vendored tree, a config — that leaves files behind with no remaining job"
gates:       []
index_clause: "delete what the decommissioned mechanism owned; audit first, never on a hunch"
checked_by:  "tools/precedent_check.py"
defines:     ["decommission"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-07"
approved_by: "Morgan"
source_practice_number: null
---
## Rule
When a mechanism is decommissioned, the files and directories that existed only
to serve it are **deleted in the same change** — not disabled, not left
"in case", not queued for a cleanup nobody schedules. Deleting is gated on
a mechanical audit, never on confidence: run
[tools/precedent_decommission.py](../tools/precedent_decommission.py) on the
path and act only on a clean report. Record what went, and why, in
`process/decommissioned_paths.json`.

## Detail
The audit refuses on four conditions, each of which is a real dependency
rather than a doubt: the path is not tracked (there is no deletion to
make); a tracked file still references it (repoint that first, or declare
it exempt if it is a historical record); a workflow file still carries a
live trigger (pause it and let a cycle pass — a decommissioning must never be
the first thing that stops a running job); or the path has uncommitted
changes (git history holds a deleted file forever and holds nothing that
was never committed). There is deliberately **no `--force`**: every
blocker is fixed by an edit someone makes on purpose.

What the audit proves is narrow and worth stating plainly — that nothing
in the tracked tree points at the path. It cannot prove the path is
useless. A reference built by string concatenation at runtime, a path
named in a GitHub setting or another repo's config, a file nothing
references that someone still needs: all invisible to it. That judgment
stays a person's, which is why the report prints its evidence — the file
count, when the path was last touched, which basename searches it skipped
as too generic — rather than only a verdict.

`process/decommissioned_paths.json` is the record: one entry per decommissioning, each
carrying the path, the reason, and the date. The reason is the load-bearing
field. A deleted file is recoverable from history by anyone who knows to
look for it; *why* it went is the thing that is otherwise gone, and the
question a later session actually asks is "was this deliberate?", not
"what did it contain?"

**Pausing is a step on the way to decommissioning, not an alternative to it.**
A workflow parked on `workflow_dispatch` with its schedule commented out is
mid-decommissioning, and the only thing separating that from abandonment is
somebody coming back. Where the pause is deliberate and open-ended, say so
where the pause is — a header comment naming what has to be true before it
resumes or goes — so the next reader can tell a hold from a leftover.

## Not the same as a retired practice

**This is about a MECHANISM, and its files go. A practice marked
`status: retired` keeps its file** — the rule is withdrawn, the reasoning
stays readable, and `precedent_show.py` prints it with a banner saying it is
in force nowhere. Retired *vocabulary*
([migration-scrubs-vocabulary](migration-scrubs-vocabulary.md)) is a third
thing again: a word this repo may no longer use.

The distinction is worth stating because this practice was itself called
`retirement-deletes-files` until 2026-09-07, and Morgan read a migration
record and asked whether practices had just been deleted. They had not, but
nothing in the vocabulary said so — and by then `precedent_retire.py`, which
only ever *proposes* a status change, was sitting in `tools/` beside
`precedent_retire_path.py`, which deletes files. Renamed to
**decommission**, the word for taking machinery permanently out of service,
which has never been used for a rule.

## Why
Leaving a dead file costs nothing today and a little every day after. The
cost is not disk: it is that every later reader has to work out whether the
file still does something, and the honest answer gets harder to reach each
year, until a tree accumulates files nobody dares delete because nobody can
prove they are dead. That is the same reasoning
[rename-updates-links](rename-updates-links.md) applies to references,
one step earlier — the cheap moment to delete a file is the moment its
mechanism is decommissioned, when the person doing it still knows exactly what it
was for.

The reason it does not happen by itself is that deleting is the one edit
with an asymmetric felt risk: leaving a file has no visible failure mode,
and cutting a live dependency has a loud one. So a rule saying "delete when
you are confident" loses to that asymmetry every time. The audit is what
changes the trade — it makes "nothing points at this" a fact someone can
check in a second rather than a belief they have to hold.

## Story
Raised 2026-09-07, from a question about what a migration from BestPractice's
old `main` onto Precedent actually deletes. Reading
[spec/MIGRATING_EXISTING_INSTALLS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/MIGRATING_EXISTING_INSTALLS.md)
against its own tooling turned up two gaps, both verified in the code
rather than suspected. Its step 6 said to "decommission the old sync workflow
entirely" and never said the file is deleted, while a paragraph much
further down spelled out the *pause* mechanics exactly ("comment it out;
leave `workflow_dispatch`") — so a session reading step 6 could
reasonably comment out a schedule and believe it had complied. And the
only check pointed at migration cleanup,
[migration-scrubs-vocabulary](migration-scrubs-vocabulary.md), scans file
*contents* for declared retired terms: a leftover file that happens to
carry none of them passes silently, and nothing anywhere asserted that a
path should no longer exist.

The precedent for the harm is already recorded in that practice's own
Story — the project's own prior notes repository's migration left the old pack's name, a
retired secret name and a paragraph about a dead workflow scattered across
five documents and three workflow headers, and it took a separate question
a day later before anyone noticed. That was the vocabulary; the files
themselves had no rule at all.

## Install
`tools/precedent_check.py`'s `decommission-deletes-files` check reads
`process/decommissioned_paths.json` (absent = `NotApplicable`, the correct state
for a repo that has decommissioned nothing) and fails if any declared path exists
in the tree again, or if an entry carries no reason. Resurrection is the
half a check can see: a vendored tree is mirrored wholesale by
[tools/checkin.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/checkin.py)'s `update`, and `practices/` and
`tools/checks/` are deleted and rewritten by
[tools/precedent_materialize.py](../tools/precedent_materialize.py) on
every sync, so a decommissioned path arriving back from a mirror is a real path
and not a hypothetical one.

The audit itself is `tools/precedent_decommission.py`; `--list` prints what
a repo has decommissioned and why. It is in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
`ENGINE_FILES`, so every repo that vendors the engine gets it — a practice
set decommissions its own tooling as readily as a consuming repo does, and the
repo most likely to be carrying dead files is one that migrated off
something.
