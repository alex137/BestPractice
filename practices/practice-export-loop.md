---
slug:        practice-export-loop
title:       The practice-export loop (how this repo propagates)
tier:        on-demand
severity:    default
applies_to:  ["process/upstream/**"]
occasion:    "merging a branch that improved a generic practice"
checked_by:  "tools/practice_audit.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 14
---
## Rule
A dependent repo vendors this repo at `process/upstream/` as plain
tracked files (no submodule — zero runtime dependency, sessions never break
on a missing remote). Install is **adaptive** (generic → specific: an agent
instantiates templates with the repo's subject matter); therefore export is
**abstractive** (specific → generic), and the mapping is recorded in
`process/manifest.json` so neither direction relies on memory. The **export
gate**: before a thread ends, if it improved a generic practice, fold the
abstracted form into `process/upstream/` in the same branch.
**Periodically**, propose accumulated vendored changes back here as a PR.

## Why
Live coupling (submodules read at session start) breaks sessions
exactly when orientation matters most, and makes capture (practice 10) a
cross-repo operation that gets skipped. Vendored-and-tracked makes the
export a local commit; the cross-repo step happens only at deliberate
check-ins.

## Story

## Install
[INSTALL.md](INSTALL.md) is the full playbook;
[tools/practice_audit.py](tools/practice_audit.py) audits the manifest
(drift between installed files and their recorded baselines) on every run.
[tools/checkin.py](tools/checkin.py) drives the cross-repo mechanics, and
**both directions of its mirror destroy work, so both are guarded**:
`update` refuses to overwrite unexported local changes, and `push` refuses
when the vendored tree is behind upstream — it deletes files it does not
have, so pushing from a stale tree silently reverts whatever upstream
gained. `--force` bypasses either.

A caution learned the hard way, worth stating because the tooling cannot
fix it: **`--force` on a mirror is a destructive command with no undo.**
Both guards were added after real losses in a single session — a stale tree
that would have reverted two upstream practices, caught only by a human
reading `status`; and then a `--force` passed to bypass the *other* guard,
which silently reverted three unexported additions including the guard code
itself. If you must force a mirror, copy what you are about to overwrite
first. The guard you are bypassing is the one that knows what you are about
to lose.
