---
slug:              todo-2026-11-22-shared-openings-keep-the-opening-stable-and-measure-it
kind:              decision
domain:            engine
severity:          low
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "yes to the short thread (Alex, 2026-11-23: \"Yes on both\")"
decision_strength: assented
waiting_on:        null
noted:             2026-11-22
closed:            null
---
## What

- [ ] **Shared openings: is there anything to build?** Alex asked, 2026-11-22, whether Precedent could host openings that many people share so their sessions start faster, as a feature or a separate product. The research and the pick are in [spec/SHARED_OPENINGS.md](../spec/SHARED_OPENINGS.md): no provider shares a cache across customers, so there is nothing to host; what is left is keeping Precedent's own always-loaded text identical and first. (needs: decision -- Alex)

**If the answer is yes to the short thread, it is three steps, in order:**

1. **Measure.** Start two sessions back to back in one checkout and read, from the first reply of the second, how many tokens came from cache; compare with the tracked-files figure [spec/shared_openings_figures.py](../spec/shared_openings_figures.py) prints. Do it once on a person's own computer and once in two cloud sessions. This says whether the opening is already being read warm, which nothing here established.
2. **If it shows a miss inside Precedent's text:** session start prints its stable text first and its status lines last, with no time of day above stable text; and the resident block's heading stops carrying counts that change whenever any practice is added.
3. **Stop.** No hosted service, no per-repository opening, unless the measurement shows something the note did not expect.

**Found on the way, larger than the opening:** the text printed at the start of every turn measured 2,177 tokens on one turn of the session that wrote the note; three turns of it outweigh the whole opening. Whether that text can be shorter after its first printing is a load-budget question ([session-load-budget](../practices/session-load-budget.md)), and is the better use of the same effort.

**The cost of leaving it:** small. At most about 6,700 to 11,500 ordinary input tokens per session start here, and only when a second session starts inside the cache's lifetime.

## How It Closes

`status` becomes `done` when Alex has said yes or no. On a yes, when the measurement is recorded in the note's "What Is Not Known" section and steps 2 and 3 are done or declined with the reason.

## Notes

- Nothing in the engine was changed by the session that wrote the note.
