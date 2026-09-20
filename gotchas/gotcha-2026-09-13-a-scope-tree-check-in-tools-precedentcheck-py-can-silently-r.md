---
slug:            gotcha-2026-09-13-a-scope-tree-check-in-tools-precedentcheck-py-can-silently-r
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A `scope: 'tree'` check in `tools/precedent_check.py` can silently report a false *pass* on an under-fetched local clone, not just degrade loudly like the two entries above.

## Story

**A `scope: 'tree'` check in `tools/precedent_check.py` can silently report a
false *pass* on an under-fetched local clone, not just degrade loudly like the
two entries above.** `parallel-artifact-ledger` walks `git log --no-merges --
<member-dir>` and fails on any commit whose hash isn't in
`templates/harness/LEDGER.md`. 2026-09-05: a local run reported `0 violated`,
but GitHub Actions' checkout of the same commit reported a real violation
twice — the local clone's history simply didn't reach back far enough for `git
log` to find the commit at all, so **an empty result read as "clean," not as
"couldn't check."** `git fetch --depth=1000 origin <branch>` (or deeper — this
check needs the *entire* history of the directories it walks) before trusting
a clean local run of any `scope: 'tree'` check.

**Second cause of the same false pass, 2026-09-14: running the deep check
BEFORE committing.** `parallel-artifact-ledger` walks `git log` for each member
directory and fails on a commit whose hash no `LEDGER.md` row references. An
uncommitted change has no hash, so the check has nothing to find and reports
`0 violated` — a pass it is structurally incapable of withholding. A session
ran all five gates clean against a dirty tree, committed, pushed, and CI failed
on the one violation the local run could not have seen. AGENTS.md already says
which moment each level gates — light check gates a commit, deep check gates a
**push** — and this is exactly what that distinction is for: a deep check run
before the commit exists is measuring a different tree from the one CI reads.
Run it between `git commit` and `git push`, never before both.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
