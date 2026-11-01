---
slug:            gotcha-2026-10-31-a-set-cloned-mid-session-puts-untracked-tools-into-map-md
status:          live
noted:           2026-10-31
severity:        notable
retired:         null
retires_when:    "build_views.py lists only the tools git tracks, or the shipped-files record refreshes whenever a set is cloned"
---
## Symptom

A commit's hook rebuilds `MAP.md` with rows for tools this repository does
not track: `tools/landing_pr_guard.py`, `tools/branch_name_guard.py` and
others a practice set delivers at session start. In this checkout,
`build_views.py --check` is clean. In a fresh clone, and in the harness's
planted-case run, the same `MAP.md` is stale and links to files that are
not there.

## Story

On 2026-10-31 a session attached the ladder set after session start, by
hand, because the start had said it did not load. The set's tools were on
disk, but `.precedent/session_ships.json`, the record of what a set
delivered and so what the map leaves out, had been written at session start
without them. Every commit hook from then on put five extra rows into
`MAP.md`. The whole-suite run caught it ("an unplanted copy of this tree
passes every check": `MAP.md` stale and a broken link), and it cost one
re-run of the planted cases and a rebuild in a pristine clone to tell apart
from the change being tested.

## Fix

After attaching a set mid-session, run
`python3 tools/precedent_session_practices.py` once. It delivers the set's
files again and rewrites `.precedent/session_ships.json`, after which
`python3 tools/build_views.py --check` agrees with a fresh clone. If a
commit has already picked up the extra rows, build [MAP.md](https://github.com/alex137/BestPractice/blob/staging/MAP.md) in a fresh
clone (`git clone` this checkout, `python3 tools/build_views.py`) and
commit that.
