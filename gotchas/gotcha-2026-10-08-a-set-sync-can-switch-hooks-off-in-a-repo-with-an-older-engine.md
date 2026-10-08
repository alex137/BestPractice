---
slug:            gotcha-2026-10-08-a-set-sync-can-switch-hooks-off-in-a-repo-with-an-older-engine
status:          live
noted:           2026-10-08
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A consuming repository's push check refuses every push because a practice
set moved, so its copies are out of date. Running the sync to refresh them
rewrites `.claude/hooks/commit-identity.sh`, `freshness-guard.sh` and
`precedent-individual-bootstrap.sh` as the short pointer stub. Each stub
runs a script under `tools/` that the repository does not have yet, so it
prints one NOTE and lets everything through: the hook is off, and the sync
said nothing about it.

## Story

**2026-10-08.** On 2026-10-07 every engine hook became the permanent pointer
stub, with its logic moved to `tools/`. The individual set declares those
three hooks as adapters it ships to every consumer, and its own Update
Vendors that evening turned its copies of them into stubs too, as designed.
A consuming repository whose engine predated the move then synced the set:
the old engine copied the stubs over three working hooks, and the scripts
they point to arrive only with Update Vendors. A session caught it by
reading the diff before committing.

## Fix

[`tools/precedent_materialize.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_materialize.py) now keeps a working hook when the source's
new version is the stub and the script that stub runs is not in the
repository. It says so and names Update Vendors, `--check` agrees with what
it kept, and the next sync after Update Vendors installs the stub as an
ordinary update. The check reads the script's name from the stub itself:
the individual-source form runs `tools/individual-source-bootstrap.sh`
whatever it is installed as.

This guard reaches a repository with its next Update Vendors. **A repository
already showing the symptom is fixed the same way:** take Update Vendors,
which brings the scripts, rather than committing the sync's stubs alone.
