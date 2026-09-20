---
slug:              todo-2026-09-11-individual-copy-points-at-a-retired-slug
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
noted:             2026-09-11
closed:            2026-09-11
---
## What

- <a id="individual-copy-points-at-a-retired-slug"></a>**`precedent-individual`'s `match-parsed-id-not-prefix` points at a retired
  slug.** That practice moved from the individual set to
  `precedent-team-repo-maintenance` in the 2026-09-09 subject split, leaving the
  individual copy as `status: deduplicated` with `in_force_at:` naming the
  team slug — which is what
  [spec/PRACTICE_FORMAT.md](../spec/PRACTICE_FORMAT.md)'s status table requires:
  a slug that **resolves in force**. On 2026-09-11 the team copy was retired,
  so it no longer does. The individual copy now claims a rule is in force
  somewhere it is not, which is the one thing that status is not allowed to
  say.

  **DONE 2026-09-11**, the same day it was raised, from a session that could
  reach the set after all: `add_repo` for `themorgan/precedent-individual`
  succeeded from a session already holding `alex137/BestPractice`, which is
  the cross-owner add the [AGENTS.md](../AGENTS.md) gotcha records as refused in
  three separate measurements and permitted in two others. **One more data
  point for a contradiction nobody has explained, not a resolution of it** —
  call it and read what it says, as that gotcha already advises.

  The copy was **retired**, not re-pointed and not re-activated. A
  deduplicated copy does not become the surviving copy when the surviving
  copy is withdrawn: re-activating it would have kept a rule the person had
  just decided to withdraw, on the technicality that the individual set is
  where it was written first. `bestpractice-sync`'s copy in the same set had
  the identical problem the same day, for the same reason, and went the same
  way.

## How It Closes

Already closed 2026-09-11 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
