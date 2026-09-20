---
slug:              todo-2026-09-06-materialized-links-dead
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
noted:             2026-09-06
closed:            2026-09-06
---
## What

- <a id="materialized-links-dead"></a>~~**A materialized practice's relative links are dead in the consuming    repo.**~~ **Done (2026-09-06.)** Every consuming repo was shipping ≈60
    practice files whose internal links resolved to nothing:
    [tools/precedent_materialize.py](../tools/precedent_materialize.py) copied
    practice bytes verbatim, so `../tools/very_deep_check.py` and
    `../spec/ATTENTION_CEILING.md` — real paths here — pointed at nothing
    there. It now repoints each link for where the file actually lands: a
    commit URL into the source repository (the commit, not a branch, since
    the tree is a snapshot and a branch can be deleted), or a recomputed
    relative path when the target is inside the consuming repo. A sibling
    practice citation, an external URL, a link that already resolves where
    it lands, and a link already broken at the source are each left exactly
    as they are. Verified against a real four-source install: **0 broken
    links**, 39 distinct sibling citations all still resolving. The
    `blocked-on` this item carried turned out to be wrong — nothing
    compared a materialized practice's bytes to its source; that
    byte-identity audit is about check scripts. `precedent-team-repo-maintenance`'
    own light check has dropped the exemption it needed to stay green, and
    its test case for that path now requires a finding instead of silence.

## How It Closes

Already closed 2026-09-06 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
