---
slug:              todo-2026-09-12-roll-binds-publishers-out-to-the-source-sets
kind:              verify
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
noted:             2026-09-12
closed:            2026-09-13
---
## What

- <a id="roll-binds-publishers-out-to-the-source-sets"></a>~~**Roll `binds_publishers`
  out to the four practice sets — it finds a real broken link in one of them the
  moment it arrives.**~~ **Done (2026-09-13)**, and the prediction below held
  exactly. The engine change landed here 2026-09-12 (PR #261), and a
  source set only gets it by refreshing its vendored engine. Until each did,
  the three flagged checks went on skipping in exactly the repositories that
  publish practices.

  **What the rollout reported.** Three sets refreshed their vendored engine to
  a commit carrying the flag and merged; the fourth was already on a later
  engine and needed no change. Each of the three went from more skips to more
  checks actually running, with **0 violations** in all three — the measured
  prediction in the table below, held. The `blocked-on` paragraph resolved the
  way it predicted: sessions rooted under that owner did the work, since
  `add_repo` refuses cross-owner.

  **This closure rests on a report, not on a check run from here, and that is
  the honest limit of it.** Those four repositories are private and
  cross-owner, so no session rooted in this repo can read their merged state
  to confirm it — including this one, which did not try
  ([no-invented-specifics](../practices/no-invented-specifics.md)). Anyone who
  can reach them and wants the closure verified rather than reported should
  check the four merges directly.

  **Measured 2026-09-12**, by copying this repo's `precedent_check.py` into a
  throwaway copy of each set and running it — so this is what the refresh will
  actually report, not a prediction. All four declare `kind: source`:

  | Set | Result |
  |---|---|
  | `precedent-team-repo-maintenance` | 0 violations |
  | `precedent-team-writing` | **1 violation** — fixed before the rollout, see below |
  | `precedent-team-working-style` | 0 violations |
  | `precedent-individual` | 0 violations |

  **The live one, and it is the exact bug class the flag exists to catch
  — since repaired.** `practices/deliverables-carry-no-process.md:26` in
  `precedent-team-writing` linked `file-header.md`, which does not travel with
  the practice file — live in that set and dead in every repository that
  received its catalogue. It was found and fixed in that set's own pull
  request *before* the 2026-09-13 rollout, which is why that set needed no
  engine change on the day: it was already on a later engine. The repair is
  reported, not verified from here, for the same cross-owner reason as above. Either
  repair the rule itself names works: drop the link markup and keep the
  backticked path, or make it an absolute URL on that set's own base branch.
  **Prefer dropping the markup** — the set is private, and an absolute URL into
  it ships into every consumer, which `private-repo-scrub` exists to stop.

  **Two workarounds became removable once a set refreshed**, and both were
  retired in `precedent-team-repo-maintenance` in a separate commit from the
  engine refresh, as this item asked — reported, not verified from here. They
  were: `precedent-team-repo-maintenance` carries
  `.github/workflows/practice-links-travel.yml`, written to call the check
  directly precisely because the engine skipped it, and a re-declared
  same-slug copy of `catalogue-carries-stories` that exists only to defeat the
  gate. That copy has never agreed with universal's and its `checked_by: null`
  now misstates its own coverage twice over, since the universal check reaches
  it either way. Its own header says a workflow per rule does not scale, so
  retiring it is the point rather than a tidy-up.

  **Blocked on / out of scope (resolved):** every one of these was a change in
  a repository the filing session could not push to. Measured rather than
  assumed — `git push --dry-run` from the clone on disk returned *"access
  denied by the git proxy: ... not in this session's authorized repository
  set"* and HTTP 403, and `add_repo` refuses cross-owner. The route named here
  is the route that worked: sessions rooted under that owner, per
  [`attach-private-sources`](todo-2026-09-06-attach-private-sources.md). The item carries
  no disposition because it is no longer an open item — the broken link is
  repaired and all four sets carry the flag.

## How It Closes

Already closed 2026-09-13 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
