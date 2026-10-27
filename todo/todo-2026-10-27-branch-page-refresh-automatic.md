---
slug:              todo-2026-10-27-branch-page-refresh-automatic
kind:              manual
domain:            engine
severity:          low
status:            open
disposition:       ask
remind_on:         2026-11-10
blocked_on:        "Morgan's call (needs: decision -- Morgan), asked again on 2026-11-10"
batch:             null
decision:          "not automatic for now (2026-10-27)"
decision_strength: decided
waiting_on:        null
noted:             2026-10-27
closed:            null
---
## What

Should the branch cleanup page refresh itself again at the close of every
session, now that a refresh is cheap? Morgan, 2026-10-27: "The branch
refresh should not be automatic but have a todo ask me in two weeks."

Until then it refreshes only when he says "Branch cleanup" (the ladder
set's
[stale-branch-cleanup](https://github.com/themorgan/precedent-shared-ladder/blob/main/practices/stale-branch-cleanup.md)).

## What to weigh when it comes up

Since 2026-10-27 the page's rows live in its own database
([`tools/precedent_stale_branches.py`](../tools/precedent_stale_branches.py)),
so a refresh is a listing, one tool run and one batch of writes: a few
thousand tokens, where the old rebuild cost about 98,000. Automatic would
keep the page current without being asked. The cost to check first: whether
writing to the page's database asks him to approve it in his sessions,
since an approval prompt in nearly every session is why the automatic
rebuild was turned off on 2026-10-20. Over the two weeks, note whether he
says "Branch cleanup" often (an argument for automatic) or rarely.

## Done when

Morgan says yes or no. On yes, the ladder set's stale-branch-cleanup and its
note tool go back to refreshing at the close, and the page's refresh steps
run then; on no, this closes and the keyword stays the only trigger.
