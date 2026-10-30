---
slug:            gotcha-2026-10-29-a-note-line-that-reports-a-state-lands-in-the-upstream-review
status:          live
noted:           2026-10-29
severity:        notable
retired:         null
retires_when:    "the ladder set's upstream review stops treating NOTE: as a warning word"
---
## Symptom

Every Update Vendors run in a consuming repository lists the same engine
line for judgment in the ladder set's upstream review, and the line says
nothing is wrong: a repair that already finished, a hook wired on purpose,
a file the person chose to undeclare.

## Story

The ladder set's upstream review ([`tools/ladder/upstream_review.py`](https://github.com/alex137/precedent-shared-ladder/blob/main/tools/ladder/upstream_review.py), which
the set installs) picks warning-shaped lines out of a run's output, and
`NOTE:` is one of its warning words. The engine used `NOTE:` for two kinds
of line: things a person should look at, and states with nothing to do.
The review cannot tell them apart, so each state became an item.

It came up three times. On 2026-10-12 the hook-state lines were cut to
print once instead of every run. Later the review learned `_SETTLED`
exemptions for "KEPT ON PURPOSE:" lines. On 2026-10-29 the push check's
"rewrote the global git hooks" line, a finished repair, was listed in
every run until it stopped saying `NOTE:`. Each round fixed only the
latest line.

## Fix

The engine keeps `NOTE:` for a line a person must judge: something it
could not do or check, or a choice it will not make for them. A line that
only reports a state prints without it, named by its tool, as in
`precedent_vendor_engine: hooks: ...` or `global git hooks: rewrote them
...`. The review stays loose on purpose, since a miss costs it more than a
false item.

On 2026-10-29 the two hook-state lines and the "no longer declared, left
on disk" line in
[`tools/precedent_vendor_engine.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_vendor_engine.py)
were changed to plain lines.
`check_refresh_names_an_in_place_hook_no_engine_path_keeps` in
[`tools/verify_harness.py`](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py) runs the review
over the hook lines, when the ladder set is installed, and fails if it
lists the "nothing to do" one. Before you add a `NOTE:` line, ask whether
the person has anything to decide. If not, leave `NOTE:` off.
