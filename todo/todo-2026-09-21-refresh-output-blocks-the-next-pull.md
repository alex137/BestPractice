---
slug:              todo-2026-09-21-refresh-output-blocks-the-next-pull
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
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
