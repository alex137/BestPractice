---
slug:            gotcha-2026-09-13-a-scratch-copy-of-this-repo-taken-to-prototype-a-change-with
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A scratch COPY of this repo, taken to prototype a change without touching the working tree, goes stale the moment the freshness guard fast-forwards the real checkout under you — and copying the prototyped files back reverts every commit that arrived in between, silently.

## Story

**A scratch COPY of this repo, taken to prototype a change without touching
the working tree, goes stale the moment the freshness guard fast-forwards the
real checkout under you — and copying the prototyped files back reverts every
commit that arrived in between, silently.** 2026-09-11: a session copied the
tree to the scratchpad, prototyped a fix to `precedent_check.py` there,
measured it, and copied the two changed files back. In between, the guard had
done exactly what it is built to do and moved the checkout forward three
merges. `git diff` against the copy had read clean when the copy was taken,
which is the whole trap: it rots from the OTHER side, so nothing about the
copy looks different afterwards. The revert took out another session's
refinement of an unrelated check's description, and **only
[tools/doc_sync.py](../tools/doc_sync.py) caught it** — `spec/ENFORCEMENT.md`'s
generated block regenerated to text OLDER than the committed block, which is a
shape no other gate here looks for. The wholesale-copy-back is the mistake; a
prototype copy is still the right way to measure. **Re-apply the edits to the
CURRENT file** — the same patch script, run against `HEAD`'s version, with
each `old` string asserted to occur exactly once so a moved file fails loudly
instead of half-applying — **then read `git diff` before committing and
confirm every hunk is one you meant.** A hunk you did not write is the revert.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
