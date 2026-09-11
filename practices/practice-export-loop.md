---
slug:        practice-export-loop
title:       The practice-export loop (how this repo propagates)
tier:        on-demand
severity:    default
applies_to:  ["PRACTICES.md", "practices/**", "templates/**", "tools/**", "process/upstream/**"]
occasion:    "merging a branch that improved a generic practice"
gates:       ["merge"]
index_clause: "vendor upstream as tracked files; check improvements back in"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
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

## Detail

## Why
Live coupling (submodules read at session start) breaks sessions
exactly when orientation matters most, and makes capture ([capture-gate](capture-gate.md)) a
cross-repo operation that gets skipped. Vendored-and-tracked makes the
export a local commit; the cross-repo step happens only at deliberate
check-ins.

## Story
No dated incident was recorded; the design is argued from two failure modes
of the obvious alternative.

**Live coupling breaks sessions exactly when orientation matters most.** A
submodule read at session start makes the practice layer a runtime
dependency, so a missing or unreachable remote takes out the very thing a
cold session opens first.

**It also makes capture a cross-repo operation, and cross-repo operations
get skipped.** That is the more subtle cost: `capture-gate` asks a session to
fold in what its work implied before merging, and a gate whose action
requires touching a second repository is one a session under time pressure
will defer, then lose.

Vendoring as plain tracked files answers both. Export becomes a local
commit, and the cross-repo step happens only at deliberate check-ins, when
somebody has decided to do it.

The adaptive/abstractive pairing follows from that asymmetry: install goes
generic to specific, so export must go specific to generic, and the mapping
is recorded in the manifest so neither direction depends on anyone
remembering what was changed.

## Install
[INSTALL.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/INSTALL.md) is the full playbook;
[tools/practice_audit.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/practice_audit.py) audits the manifest
(drift between installed files and their recorded baselines) on every run.
[tools/checkin.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/checkin.py) drives the cross-repo mechanics, and
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
