---
slug:              todo-2026-09-11-cross-source-resident-block-over-cap
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          ""I want to remove both. The other session is removing buenos-aires-date." -- Morgan chose to demote both buenos-aires-dates and small-calls from the resident block."
decision_strength: decided
waiting_on:        null
noted:             2026-09-11
closed:            2026-09-11
---
## What

- <a id="cross-source-resident-block-over-cap"></a>~~**The resident block is
   over its 2,000-token cap once the private sources resolve, and has been
   since before this item was written.**~~ **CLOSED 2026-09-11: both demotions
   landed, and the block measures 1,695 tokens across 15 practices,
   `over_budget: false`.**

   `buenos-aires-dates` is `tier: on-demand` on `precedent-individual`'s
   `main`, and `small-calls` is `tier: on-demand` on
   `precedent-team-working-style`'s `main`. **Neither practice moved
   repository and neither was deleted** — both are `status: active`, in the
   same file in the same set they have always been in, with
   `buenos-aires-dates` keeping its `checked_by` script and both keeping
   `applies_to: ["**"]`. The only field that changed is `tier:`, so each is
   now reached through the occasion index and the path-trigger channel
   instead of being loaded into every session before it starts.

   The original finding follows, kept for what it measured.

   `python3 tools/precedent_resolve.py --repo . --json` reported
   **2,047 tokens across 17 resident practices** on a session where
   `precedent-individual` and the three `precedent-team-*` sets are attached
   — seven of the seventeen come from those sources
   (`audience-register`, `buenos-aires-dates`, `default-register`,
   `half-the-words`, `nonblocking-questions`, `reply-is-short`,
   `small-calls`). This repository alone is at 876 tokens and clean; the
   overflow only exists in the combination, which is exactly the case
   [spec/PRIVATE_SETS_BRIEF.md](../spec/PRIVATE_SETS_BRIEF.md) flagged as the
   open gap and the cross-source cap was built for.

   **The fixture half is fixed, 2026-09-11.** All three of that check's
   directions are synthetic now — this repo named as the only declared
   source, a single source over the cap, and a multi-source combination over
   it — so the harness result no longer depends on what a container has
   attached. It passes on a container with all four sets attached and over
   budget, which is where it used to fail. A real combination going over is
   not that check's business: `precedent_resolve.py` exits 1 and
   `build_views.py` refuses to write an over-budget block, which is a harder
   stop than a harness line, and the reduction is the owner's to choose.
   What follows is the description of the defect as it was found.

   It showed up as `verify_harness.py`'s **cross-source resident budget**
   check failing its FIRST direction — *"this repo's own resolved set was
   wrongly flagged over budget"*. That wording was wrong twice over: the
   flag was correct, and the fixture was not measuring "this repo's own set"
   at all. It called `precedent_resolve.py --repo <this repo>` with the
   container's real sources attached, so its result depended on which machine
   it ran on — the
   [fixture-owns-its-state](../practices/fixture-owns-its-state.md) shape, one
   level out from the three instances already in
   [AGENTS.md](../AGENTS.md)'s gotchas. Fixing the fixture and fixing the
   overflow were separate pieces of work and neither substituted for the
   other; the first is done.

   **Morgan picked, 2026-09-11 (`decided`): `small-calls` comes out of the
   resident block.** Measured with the change applied to the attached clone
   and reverted: **1,855 tokens across 16 practices**, under the cap, so this
   one demotion closes the overflow on its own and nothing else needs to
   move. The whole edit is one word in
   `precedent-team-working-style/practices/small-calls.md` — `tier: resident`
   becomes `tier: on-demand` — followed by that set regenerating its own
   views. The practice stays in force and stays where it is; only the loading
   channel changes, from resident to the occasion index.

   **Two decisions were recorded on 2026-09-11, in two different threads,
   naming two different practices. Both are Morgan's; neither session could
   see the other; this paragraph does not rank them.**

   *Thread A — `buenos-aires-dates`, and already in flight.* Shown the
   seventeen with what each costs, Morgan chose to demote
   `buenos-aires-dates` (individual, ≈159 tokens). It is the one resident
   rule with mechanical backstops — its own
   `tools/checks/check_buenos_aires_dates.py`, the `pre-commit` hook that
   refuses a wrong commit offset, and the zone ladder deriving from
   `identity.json` — and it already carries an `occasion` and an
   `index_clause`, so demoting moves it into the occasion index rather than
   dropping it, and `applies_to: ["**"]` keeps the path-trigger channel
   firing it. **The reply-register practices were explicitly ruled out** in
   that thread: all four are `checked_by: null`, they bind every reply, and
   this repository's own gotchas record what a session's replies look like
   when one of them silently fails to load. The edit is one frontmatter line
   in `precedent-individual`; it was handed to a session rooted there.

   *Thread B — `small-calls`.* Asked directly to drop `small-calls` from the
   resident block and consider moving it to the writing set. Measured with
   the change applied to the attached clone and reverted: **1,855 tokens
   across 16 practices**, under the cap. The edit is
   `tier: resident` → `tier: on-demand` in
   `precedent-team-working-style/practices/small-calls.md`, followed by that
   set regenerating its views. `small-calls` is not one of the four
   reply-register practices thread A ruled out, so the two decisions do not
   contradict each other — they overlap.

   **Both. Morgan, 2026-09-11 (`decided`), asked which he wanted:**
   *"I want to remove both. The other session is removing
   buenos-aires-date."* So the two demotions are one decision in two threads,
   not a collision to resolve — each set's edit proceeds independently, and
   the paragraphs above are kept because they record what each thread
   measured and ruled out, which is the part a later session would otherwise
   re-derive.

   Combined effect, from the two measurements above: the resident block goes
   from 2,047 tokens across 17 practices to roughly **1,696 across 15**. Both
   demoted practices keep an `occasion` and an `index_clause`, so each moves
   into the occasion index rather than out of force, and both keep
   `applies_to: ["**"]`, so the path-trigger channel still fires them.

   **The move to the writing set was declined**, on two grounds worth
   keeping so nobody re-proposes it. `small-calls` is about judgment calls in
   any work — filling in a default, picking between two implementations — and
   `precedent-team-writing` is seventeen practices about prose and documents;
   it already sits in `precedent-team-working-style` beside
   `default-register`, `nonblocking-questions` and `quiet-checks`, which is
   its subject. And the move would not have achieved the thing anyway:
   **residency is the `tier:` field, not the level**, so a resident practice
   carried from one team set to another is still resident and still in every
   session's block.

   **blocked-on:** a session that can PUSH to the set being edited — neither
   `precedent-individual` nor `precedent-team-working-style` is writable from
   a session rooted here. Measured 2026-09-11, both routes: `git push` inside
   the attached clone is refused by the git proxy (`not in this session's
   authorized repository set`, 403), and `add_repo` with `access: "push"`
   refuses with `cross-tier adds are not supported in v1 ... session already
   has repos from owner(s) [alex137]`. Same wall as
   [`views-drift-gate-rollout-to-existing-sets`](todo-2026-09-11-views-drift-gate-rollout-to-existing-sets.md).

   **One of the two has landed, and it was enough on its own.**
   `buenos-aires-dates` is `tier: on-demand` on `precedent-individual`'s
   `main` as of 2026-09-11. Measured here with every source clone pulled
   current: **1,887 tokens across 16 practices, `over_budget: false`** — so
   the cap is cleared already, and the full harness is back to `0 failed`.
   `small-calls` is still `tier: resident` on
   `precedent-team-working-style`'s `main`; its edit was handed off the same
   day and had not landed at that measurement.

   **So the second demotion is now elective, and that is worth saying
   plainly rather than letting it read as outstanding work.** Morgan asked
   for both, so the handoff stands; but nothing is red while it is pending,
   and a session finding this item open should not treat `small-calls` as a
   blocker or re-raise the budget as a problem. The overage that opened this
   item is gone.

   **Closed.** Both pushes landed on 2026-09-11, in their own repositories,
   by sessions rooted at each. Measured here with every source clone pulled
   current: 1,695 tokens across 15 resident practices, `over_budget: false`,
   and the full harness at `0 failed`.

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
