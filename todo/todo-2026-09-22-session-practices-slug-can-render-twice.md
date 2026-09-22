---
slug:              todo-2026-09-22-session-practices-slug-can-render-twice
kind:              analysis
domain:            engine
severity:          medium
status:            open
disposition:       raise
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-22
closed:            null
---
## What

**[tools/precedent_session_practices.py](../tools/precedent_session_practices.py)'s
`collect()` can render the same slug twice in front of a session** — once
from the TRACKED loader block ([AGENTS.md](../AGENTS.md), built by
[tools/build_views.py](../tools/build_views.py) straight off this repo's own
`practices/`) and once more from the DEFERRED, untracked
`.precedent/SESSION_PRACTICES.md` this module writes — with no tie-break
stated when it happens.

`collect()` filters `res['practices']` (the resolved, precedence-applied
set) down to the slugs whose WINNING file lives under a deferred source's
path (`_from_deferred_source`, line 130). That is the right question for a
slug whose only copy is in a deferred source. It is the wrong one for a
slug that ALSO has a same-named file in this repo's own tracked
`practices/`: resolution picks one winner by precedence, but
`sources_for_tracked_block()` renders the tracked file into `AGENTS.md`
independently, with no awareness of which source actually won. Two
renderers, each blind to the other's slug set — the same shape of gap
`code-cites-practice`'s own todo item just found on the checking side.

## Why it does not reproduce today

Four slugs are declared at both levels in this repo's own attached sources
(`go-merge`, `leak-gate-is-background`, `next-steps-after-commit`,
`practice-links-travel`), and all four avoid the duplicate only because the
local copy is hand-marked `status: deduplicated` in its frontmatter, which
[tools/build_views.py](../tools/build_views.py) reads and excludes from the
tracked block. That is a
**convention a person has to remember to apply to every new collision**, not
a mechanism that catches one — the same distinction the merge-target
incident this repo's own `AGENTS.md` opens with was built to stop repeating.

Unconfirmed beyond that: this was raised by a prior session's own quoted
"postcondition bug in collect() slug precedence" analysis, paused awaiting a
choice between "local wins + print note" and "warn-only". That analysis was
never pushed and is not readable from here — nothing above is inherited from
it, this item re-derives the mechanism from `collect()` and
`_from_deferred_source()` as they stand today.

## What would fix it

Have `collect()` (or `sources_for_tracked_block()` in
[tools/build_views.py](../tools/build_views.py), since it already knows
what the tracked block renders) check the slugs the two renderers would
BOTH cover, not just trust the `status: deduplicated` convention to have
been applied everywhere it is needed. On a real collision: either the local
copy wins and a note explains why the deferred one is suppressed, or both
render with a visible note that they are the same slug from two sources —
either beats the silent double render a new collision produces today.

## How It Closes

`status` becomes `done` once `collect()` (or its caller) detects a slug
rendered by both the tracked block and the deferred file and resolves it
one of the two stated ways, with a check or test that fails on a fresh,
unmarked collision — not one that only stays green because every existing
collision happens to carry `status: deduplicated` by hand.
