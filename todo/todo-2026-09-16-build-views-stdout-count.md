---
slug:              todo-2026-09-16-build-views-stdout-count
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-16
closed:            2026-09-07
---
## What

- <a id="build-views-stdout-count"></a>**Done 2026-09-07 — `build_views.py`'s summary line reported a different
  practice count than the block it had just written.** Found merging
  [precedent-beta-v01](https://github.com/alex137/BestPractice/tree/staging)
  into a feature branch: the regenerated `AGENTS.md` header read *7 of 72
  practices* while the same run printed *resident 7/69* to stdout. The
  committed artifact was the correct half; the line a session reads to
  confirm the run was the wrong one, which is the worse half to have wrong.

  The cause was a **second** `build_loader_block()` call at the end of
  `main()`, given the single-source catalogue where the block itself had
  been built from the multi-source resolve — so the token count and
  resident count were re-derived from the wrong list too, and happened to
  agree by coincidence. Fixed by removing the second computation rather
  than making the two agree:
  [build_views.py](../tools/build_views.py)'s `render_agents_md()` now returns
  its own figures alongside the text, and `main()` prints those. A harness
  case runs a real write against a copy of the tree and compares all three
  printed figures against the `AGENTS.md` header it produced; reverting the
  fix makes it fail with `printed (7, 70, 377), wrote (7, 73, 377)`.

## How It Closes

Already closed 2026-09-07 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
