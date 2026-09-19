---
slug:              todo-2026-09-08-split-team-sets-by-subject
kind:              analysis
domain:            content
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-08
closed:            2026-09-09
---
## What

- <a id="split-team-sets-by-subject"></a>**Sort the existing team and individual rules into subject-scoped team
  sets.** Decided 2026-09-08, after the cross-team drift question: a rule
  several teams need does **not** go to universal — universal is for
  opinionated rules Precedent tells the world, and a house design style is not
  one. It goes into **one team set named for its subject**, which every team
  that needs it declares alongside its own. The naming convention already
  points here: a team set is named for its **purpose**, and a roster-shaped
  name is stale the moment somebody joins. Nothing new has to be built — a
  repo can already declare several team sets, and two of them defining one
  slug is a loud refusal, which is the guard that stops a local copy creeping
  back in.

  **What is left to do is the sort itself**, one rule at a time, across
  `precedent-team-repo-maintenance`, `precedent-team-tms` and
  `precedent-individual`: which rules are genuinely one team's, which are
  subject-scoped and want a set of their own, and which are personal to
  Morgan rather than to any team. The test per rule: *who breaks if this is
  wrong?* One team → that team's set. Everyone doing a kind of work,
  regardless of team → a subject set. One person → individual. Only this
  repository → repo-local.

  **DONE 2026-09-09**, from a session rooted in a `themorgan/` repo with all
  five sets and this repo on disk — the route
  [`attach-private-sources`](todo-2026-09-06-attach-private-sources.md) names, and it
  worked exactly as written.

  **The sort, and the count that made the case.** Of
  `precedent-team-repo-maintenance`' 40 practices, 19 were about something other
  than maintaining a repository. 16 went to a new `precedent-team-writing`
  (the craft of writing for a human reader: length and emphasis, when a list
  is really a list, drafting markers, citation and linking, keeping a
  reader's material out of a deliverable that is not for them) and 3 to a new
  `precedent-team-working-style` (how a session paces work with the person).
  21 stayed. Two moved up from the individual set; **three more were proposed
  and reversed on reading the rules rather than their slugs**, each of which
  says in its own text that it is not team policy — one of them outright
  ("my preference for my own repositories, not a default I ask anyone else to
  adopt"). Moving that one would have contradicted the rule while claiming to
  enforce it.

  **The strongest single finding.** The two practices that fire on *every
  turn of every session* — the only two `tier: resident` rules in the whole
  40 — were reachable only by a repository that also declared twenty-odd
  rules about syncs, gates and branch setup. A document project therefore
  declared none of them, and the team that most needed the writing rules had
  one practice of its own. **Reach is what a set is worth, not how many files
  it holds**, which is why a 3-practice set earns its own repository here.

  **Migration for repos already on the old system is the two-step move
  [spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md) prescribes**, applied
  19 times: land at the destination first, verify it there, deduplicate at
  the source second. Nothing was deleted and no rule left force for a moment.
  Every moved practice keeps its file in the old set as `status:
  deduplicated`, with `in_force_at:` naming the same slug and a `## Story`
  line saying which set now holds it. So a repo that has not yet updated its
  `precedent.json` resolves fewer practices — and the ones it no longer gets
  are each sitting in the set it still declares, saying by name where they
  went. That is the difference between a migration and a disappearance.

  **What made it safe to do at all** is the guard this item already named:
  two team sets defining one slug is a hard refusal, so one rule has exactly
  one home by construction. Verified across all four team sets after the
  move: no collisions.

  **Left alone, and NOT a duplicate — this one is worth reading before the
  next audit re-raises it.** `catalogue-carries-stories` is `active` in
  `precedent-team-repo-maintenance` *and* `active` at universal, which every
  slug-overlap scan reports and `no-duplication` appears to condemn. It was
  in fact deduplicated on 2026-09-07 and **re-activated the same day**, for a
  mechanical reason the practice file now records in its own `## Story`: **a
  source repo consumes no catalogue**, so universal's copy never reaches a
  set like that one, and `precedent_check.py` gates every check on its
  practice being in force *there*. Deduplicating it did not defer enforcement
  to universal — it switched enforcement off.

  So the same-slug copy is not a restatement; it is the mechanism by which a
  source set puts a universal rule in force on its own catalogue, and any
  audit that reasons from the slug overlap alone will keep proposing the
  round trip that was already made and reversed. The general wart — **a
  source set must re-declare a universal practice to enforce it on itself** —
  was real, and **is addressed as of 2026-09-12**: `binds_publishers` (#261)
  is exactly that fix, so re-declaration is no longer the mechanism and a
  session reading this passage should not reach for it. The counter-example
  still belongs to
  [`practice-consistency-across-team-repos`](todo-2026-09-07-practice-consistency-across-team-repos.md),
  whose own note that "a copy is usually the bug" needs it attached — but
  attached as history now, not as live guidance: the copy that motivated it
  was retired on 2026-09-13 once the flag reached that set.

  **One half of the wart is genuinely still open**, and it is worth not
  losing in the correction: `binds_publishers` teaches a CHECK to bind a repo
  that publishes practices, and there is no equivalent for PROSE. Universal
  guidance text still never reaches a source set, which is why a set keeps
  hand-copied restatements of universal rules it cannot resolve. Filed as
  [`universal-prose-does-not-reach-a-source-set`](todo-2026-09-13-universal-prose-does-not-reach-a-source-set.md). And item 7 stays parked: nothing in this split expresses
  a preference between two disagreeing team sources, because nothing here
  produced two sources that disagree.

## How It Closes

Already closed 2026-09-09: the sort was done, from a session rooted in a
`themorgan/` repo holding all five sets and this repository at once,
following the `attach-private-sources` route. Nothing further was ever
asked of a session rooted here.

## Notes

2026-09-19: this item, like
[`todo-2026-09-10-source-checks-adopt-engine-helpers`](todo-2026-09-10-source-checks-adopt-engine-helpers.md),
was never carried into the 2026-09-16 `todo/` migration (`9a08363b`) —
it existed as an unnumbered item in `TODO.md` immediately before that
commit, already marked `DONE 2026-09-09`, with no row in
[`spec/TODO_GOTCHA_MIGRATION_MAP.md`](../spec/TODO_GOTCHA_MIGRATION_MAP.md)
and no file under `todo/` or in [`todo/CLOSED.md`](CLOSED.md). Recreated
here from the pre-migration text (`git show 9a08363b^:TODO.md`, lines
1638-1735), unchanged except for repointing its four in-repo links from
old-style `TODO.md` anchors to the sibling `todo/` files and `spec/` path
those anchors now resolve to.

Found while investigating a report, from a session rooted in
`precedent-team-writing`, that this item's old anchor
(`split-team-sets-by-subject`) was cited and dead in that repo's own
practice files. Tracing it here turned up more than this one gap: a
systematic sweep of every anchor in the pre-migration `TODO.md` against
the migration map found **51 of 148 items missing**, not just this one and
`source-checks-adopt-engine-helpers` — filed in full as
[`todo-2026-09-19-migration-dropped-54-items`](todo-2026-09-19-migration-dropped-54-items.md)
rather than reconstructed one-by-one here. This file and
`source-checks-adopt-engine-helpers` are the two of the 51 reconstructed
so far, both because something outside this repository was actively
blocked on tracing them.
