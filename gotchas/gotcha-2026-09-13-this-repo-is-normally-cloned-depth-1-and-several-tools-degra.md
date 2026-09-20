---
slug:            gotcha-2026-09-13-this-repo-is-normally-cloned-depth-1-and-several-tools-degra
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

This repo is normally cloned `--depth 1`, and several tools degrade rather than fail on that.

## Story

**This repo is normally cloned `--depth 1`, and several tools degrade rather
than fail on that.** [tools/behavioral_replay.py](../tools/behavioral_replay.py)
divided by the replayable-commit count and took the whole harness down with a
`ZeroDivisionError` on a one-commit clone — the exact environment a fresh
session starts in. It now reports `REPLAY_STATUS: DEGRADED` instead. On the
same clone `origin/main` does not exist, so doc_lint's
changed-vs-default-branch scope quietly becomes changed-vs-`HEAD`: it checks
your uncommitted files and nothing else. Fix both with a bounded `git fetch
--depth=500 origin <branch>`; some git policy hooks block `--unshallow`, and a
bounded fetch works either way.

**Since 2026-09-14 the primary repo does this for you**, in
[.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh): a shallow
clone is deepened at session start, before anything reads history, bounded by
`timeout` and falling back to `--deepen` where `--unshallow` is refused.
Measured against this remote: 2.7 MB of history before, 9.5 MB after, 4
seconds. **What it does NOT cover is every case this entry is about** — a
sibling attached mid-session runs none of its own hooks
([g15](../record/GOTCHAS.md#g15)), a CI checkout is its own shallow clone, and a source set has no
such hook at all. In any of those, the manual fetch above is still the fix, and
a tool reporting a suspiciously clean result is still the symptom.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
