---
slug:              todo-2026-09-21-refresh-output-blocks-the-next-pull
kind:              manual
domain:            engine
severity:          high
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            2026-10-01
---
## What

**The session-start refresh leaves its own output uncommitted in every source
clone, and that uncommitted output is exactly what stops the next session
pulling the clone current.** Four sources, measured 2026-09-21 against their
own `origin/main`:

| source | behind | ahead | dirty files |
|---|---:|---:|---:|
| individual | 34 | 31 | 2 |
| shared/writing | 17 | 0 | 1 |
| shared/working-style | 28 | 0 | 3 |
| shared/repo-maintenance | 28 | 0 | 3 |

**Every dirty path is vendored engine output** -- `tools/ENGINE_MANIFEST.json`,
[tools/precedent_check.py](../tools/precedent_check.py),
[tools/precedent_reply_check.py](../tools/precedent_reply_check.py). Nobody
hand-edited any of them.

## The loop

1. Session start runs the refresh with `--apply`, which writes fresh engine
   files into each source clone.
2. Nothing commits them. The tool says so itself, by design: *"this tool never
   publishes."*
3. The clone is now dirty.
4. Next session: the bootstrap's `git pull --ff-only` fails on the dirty tree,
   and the refresh hits its own dirty-guard and prints `SKIP refresh`.
5. The clone falls further behind. Nothing exits non-zero; the run's closing
   line reads `applied.` either way.
6. The catalogue is read off that stale tree --
   [tools/precedent_materialize.py](../tools/precedent_materialize.py) contains
   **zero** fetch calls, so whatever is checked out is what becomes the
   practices in force.

The guard in step 4 is right and should stay. Its own comment says what it is
for: *a person's own uncommitted edit in this source -- a new practice file, a
hand fix mid-review*. The defect is that it cannot tell a person's edit from
the tool's own output, so the tool's output disarms the tool.

## The shape of the fix

Three parts, smallest first.

1. **A skip must not report success.** The closing `applied.` line and the exit
   code both ignore skips today. A silent decline is how four sources drifted
   17 to 34 commits without anyone noticing.
2. **Distinguish the tool's dirt from a person's.** Paths listed in that
   clone's own `ENGINE_MANIFEST.json` are the refresh's own output; dirt
   confined to those is safe to overwrite, and the pull may proceed. Anything
   else keeps today's SKIP exactly as it is.
3. **Then make it current, and check that it became current.** Bringing the
   clone to `origin/<pinned branch>` is the first action of the runbook rather
   than an instruction in its prose; verifying it arrived there is what stops
   step 2 reading a stale catalogue.

## Why the wording fix alone would not have worked

The first reading of this was that the runbook's step 1 needed a postcondition.
Morgan, 2026-09-21: *"would this force it to clone the most updated version
first thing? I think that's what we need."* He is right, and the measurement
above is why -- a check that refuses on a stale clone would have fired on all
four sources every session for weeks and changed nothing, because nothing in
the sequence was ever going to make them current.

## Closed

2026-10-01, on all three parts of the fix above, each checked rather than
assumed:

1. **A skip does not report success.** A refresh that leaves a clone behind
   ends `NOT APPLIED to N of M`, naming each clone
   ([tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)).
2. **The tool's output is told apart from a person's edit.**
   `classify_dirt()` counts the manifest's files, hooks, generated views and,
   since #805, its `engine_paths` (while each still has the hash it was
   written with) as engine output. The last gap was there: precedent-individual's
   `bootstrap/commit-identity.sh` and `bootstrap/freshness-guard.sh` counted as
   a person's work, which both stopped the pull and made
   [tools/precedent_container_safe.py](../tools/precedent_container_safe.py),
   which asks the same function, call every container unsafe.
3. **The clone is made current, and checked.** With engine dirt only,
   `make_current()` discards it, fast-forwards to the clone's own branch,
   and the refresh writes the engine again over the new tree.

Measured live the same day, in a session rooted above every repo: the
session-start refresh left 36 and 37 uncommitted engine files in three set
clones; `classify_dirt()` counted none of them as a person's, and the
container check said "nothing uncommitted". A hand edit still stops both:
check_a_stale_source_clone_is_made_current_not_reported_clean (23 cases,
two of them refusals), check_refresh_sources_pulls_a_set_behind_its_own_origin
and check_archive_line_is_refused_when_the_container_holds_only_copy_work
all pass. Reached the practice sets with the 2026-10-01 Produce, on their
next session-start refresh; nothing to migrate.
