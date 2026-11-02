---
title:         Rehearsal of the set-copy change on the repositories at hand
kind:          record
status:        closed
opened:        2026-11-01
closed:        2026-11-01
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Update Vendors with the set-copy engine, run on scratch copies of a voice repository, the ladder and writing sets, a private rules set and a planning repository: every whole copy now carries the files the engine reads, each repository reaches DONE or only its own earlier calls, no new check turns red, and a second run reports nothing new."
---

# Rehearsal of the set-copy change on the repositories at hand

What [the plan](SET_COPY_CARRIES_WHAT_THE_ENGINE_READS_PLAN.md) asked the
build to show before it lands: the new Update Vendors, run with this
branch's engine (`--from-ref`, commit `cc811f694`), on scratch copies
(`cp -a`, pushes disabled, `PRECEDENT_NO_SHARED_PASS=1`) of the
repositories on this machine. The originals were never touched. The
scratch copies' user config pointed at a scratch copy of the person's
individual set, so the sets each update copied came from scratch clones
too. Scratch commits between steps were authored as the person the
environment declares, the way their own commits are.

## The repositories

| Repository | Kind | Result |
|---|---|---|
| A voice repository | consumer; whole copies of the ladder set, the writing set and a private rules set; a files-only copy of a voice pack | **DONE**, before its sets took the engine. Its ladder copy gained `our_language.json`, one line in the summary: "added our_language.json, the set's own words, for the vocabulary list: copies of shared sets now carry every file the engine reads from them". Basic check passed; a full sweep afterwards: 0 violated. |
| precedent-shared-ladder | shared practice set | **DONE**. "set-file-decided is strict here from now on: every top-level file is already decided". Its own 10 tests pass; full sweep 0 violated. |
| precedent-shared-writing | shared practice set | **DONE**, the same line; its 7 tests pass; full sweep 0 violated. |
| A private rules set | shared practice set | **DONE** on the first run, with one note: a top-level notes file nothing decides. The marker reads "noted", so the check stays a note there. **LEFT FOR YOU** on the second run, with that one file and the two lines that decide it: the set's call, which it has not made yet. |
| A planning repository | consumer; reads its sets live | **LEFT FOR YOU**, with the same eight items the current `staging` engine leaves there (three copy-in questions, a settings change, four `AGENTS.md` sections): its own calls, none from this change. |

Neither the ladder set's nor the writing set's `precedent.json` declares
`adapters`.

## Before and after, in the voice repository

- **Before the update**, `set-copy-complete` (this branch's check, run
  against the old copies): a note, never a finding. "this copy of
  precedent-shared-ladder predates the set-files registry; the next Update
  Vendors fills it: it will add our_language.json", and the same for the
  other two whole copies.
- **After it**: no finding, with the copies compared byte for byte against
  the commits their records name. The records:
  - ladder: `precedent-source.json`, `reply_check.json`, `our_language.json`;
  - writing: `precedent-source.json`, `reply_check.json`;
  - the private rules set: `precedent-source.json`.
- **A second update right after**: DONE, nothing added, nothing changed in
  any copy.

## The cases the second review asked for

1. **A consumer updated before its sets took the engine**: the voice
   repository above, first in the order. DONE.
2. **A files-only copy**: the voice pack copy holds exactly what it held
   before, and its manifest has no `set_files` record.
3. **A kept local edit to a registered file**: `our_language.json` in the
   ladder copy edited, with a `kept_template_divergences` line and a
   reason. Update Vendors: DONE, "our_language.json kept as this repository
   changed it"; the edit is still there; `set-copy-complete` names it as
   kept and reports nothing red.
4. **A set rooted at its top exporting a path under `process/`**: the
   scratch ladder set was given a `process/zz-other/` with its
   `process/manifest_zz-other.json` and an export of it. The consumer's
   update left the copy for the person, nothing copied: "A copy never
   carries another source's copy". **With a consumer copy that already held
   it**: DONE, with one line naming the nested copy and the
   `precedent_decommission.py` line that removes it.

## What the rehearsal found, and what changed because of it

- **`set-file-registered` named the harness file by its literal path**, and
  `vendored-engine-file-refs-resolve` failed in every consumer's full sweep.
  The check now tells the engine's own repository by its missing
  `tools/ENGINE_MANIFEST.json`.
- **A set's first update would have been refused at its push.** Writing the
  strict marker on the first update left the private rules set's next push
  red on its undecided file. The marker now has two steps ("noted", then
  the date), and once strict, Update Vendors leaves each undecided file for
  the person on every run.
- **The voice repository's first update stopped on three workflows the
  person had approved.** A self-replacing engine refresh runs its second
  pass's sweeps before it writes the files the new list adds, so the new
  `precedent_check.py` could not import `precedent_set_files.py` there and
  every approval read as missing. The second pass now writes the files the
  new list adds before anything else. The `staging` engine reaches DONE on
  the same copy; this branch's now does too.
