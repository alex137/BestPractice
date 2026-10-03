---
slug:            gotcha-2026-10-02-a-set-made-from-a-working-branch-had-its-engine-rolled-back-at
status:          live
noted:           2026-10-02
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A practice set's working copy shows engine files under `tools/` modified
or deleted at the start of a session, with nobody having touched them.
`git status` in the set lists them, and checks run there use an older
engine than the one the set committed.

## Story

On 2026-10-02 the ladder set was created from a BestPractice working
branch, because the engine it needed had not reached main yet. Its
`tools/ENGINE_MANIFEST.json` recorded that branch's commit, but
`source_branch: main`, since seed wrote "main" whatever it copied from.

At session start the refresh compares each set's recorded engine commit
with BestPractice's main, and it compared them only for being equal. They
differed, so it called the set stale and wrote main's engine over it in
the working tree. Main's engine was the older one, so it deleted files the
set had committed, the ladder's own engine file among them. That happened at
every session start, and twice in one session it was put back by hand with
`git -C <set> checkout -- .`.

## Fix

Two halves, both in [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py):

- The refresh asks whether main contains the recorded commit, not only
  whether the two are equal (`engine_is_ahead`). An engine main does not
  contain is newer work: the refresh leaves it as it is and says so, and
  the session-start survey shows the set as AHEAD instead of STALE
  ([tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)).
- `seed` and the set bootstrap refuse to copy from a checkout main does
  not contain, before writing anything. `--off-main` (`--off-main true`
  for the bootstrap) does it on purpose, and the manifest then names the
  real branch as `seeded_from_branch`, beside a `source_branch` that still
  says what the refresh follows.

Until that reaches the sets you work in: if a set's `tools/` changed at
session start, run `git -C <set> checkout -- tools/` before anything
else there.
