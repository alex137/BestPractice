---
slug:              todo-2026-09-11-deduplicate-practice-links-travel
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

- <a id="deduplicate-practice-links-travel"></a>**Deduplicate
   `practice-links-travel` in `precedent-individual`, now that it is in force
   at universal.** Landed here 2026-09-11 as
   [practices/practice-links-travel.md](../practices/practice-links-travel.md),
   with a check in [tools/precedent_check.py](../tools/precedent_check.py) and
   134 links repaired across 42 practice files.

   **This is step 2 of [spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md)'s
   two-step, and it is deliberately not done.** Step 1 lands at the
   destination; step 2 sets the source copy to `status: deduplicated` with
   `in_force_at: practice-links-travel` and one line in its `## Story` naming
   where it went. Skipping it leaves two copies of one rule at two levels,
   with individual precedence quietly winning — the state the ordering exists
   to pass through briefly, not to sit in.

   **What the other session needs to know before it does it.** The universal
   text is NOT the individual text carried across: the session that landed it
   could not reach that repository, so it wrote the rule fresh from a
   measurement and a description of the original. Read both before
   deduplicating — if the individual copy says anything the universal one
   does not, that sentence has to move up, not disappear. The one place the
   two are known to differ on purpose is the remedy: a private set de-links
   and keeps the backticked path, because an absolute URL would publish the
   private repository's name into every consumer; this repository is public
   and links absolutely. The universal file says so in as many words, so the
   individual set is not losing that reasoning by going away.

   **Its check script goes too.** `tools/checks/check_practice_links_travel.py`
   in that set skips every practice whose source is not the individual set,
   which is what made the universal catalogue unexamined by anything for as
   long as the rule has existed. Once the universal check is in force there
   is nothing left for it to look at.

   **DONE 2026-09-11.** The copy in `precedent-individual` is
   `status: deduplicated`, `in_force_at: practice-links-travel`, and its
   check script and that script's own test are gone from that set's
   `tools/checks/`. Its `## Story` records the line-by-line comparison this
   item asked for and raised four things the universal text was missing.
   **All four are up as of [PR #197](https://github.com/alex137/BestPractice/pull/197)**,
   across three pull requests: #194 carried the `../tools/checks/` clause and
   the failure shape where a link *resolves* in the consumer to that
   consumer's own file; #198 widened the clause to a check's own test and
   summarized the private refusal in the Rule; #197 added the two that were
   still missing — the Detail paragraph quoting `precedent_materialize.py`'s
   own line, with the standing instruction that a session finding such a link
   must not make it absolute, and the 2026-09-06 incident that is the
   evidence for that half of the rule.

   One of the four was a real defect: the universal check did not know a
   check script's own test travels, measured against that set as 12 false
   violations across 6 practice files, each one repaired by an absolute URL
   into a private repository.

   **What unblocked it, and it is worth knowing for the next cross-owner
   item:** `PRECEDENT_GIT_TOKEN` reached a session rooted here for the first
   time, so the private sources clone at session start. A session in this
   repository can now READ that set directly and does not need a person to
   carry findings between windows
   ([findings-return-through-repo](../practices/findings-return-through-repo.md)).
   Pushing to it is still cross-owner and still needs a session rooted there.

   **Historical blocked-on:** `precedent-individual` is under a different
   owner and could not be attached to the session that landed this — the standing cross-owner
   `add_repo` refusal, and no `PRECEDENT_GIT_TOKEN` in that environment. It
   needs a session rooted in that repository, which is a person's act
   ([cross-source-rollout](../practices/cross-source-rollout.md): not attached,
   so it is queued rather than done).

   **Three corrections made while carrying the last two, all deliberate.**
   The check-script clause as #194 landed it matched `check_*.py` only;
   #198 then widened it to anything under `tools/checks/` at any depth.
   Neither is what `precedent_materialize.py` does — it copies two globs,
   `check_*.py` and `tests/test_*.sh`, not a subtree — so the check now
   matches exactly those two **and** requires the target to exist in the
   tree being scanned, which a depth-anything pattern would not catch.
   #198's harness control planted a test named `t.sh`, which materialize
   would not copy at all; it is `test_x.sh` now, and the fixture creates the
   files it links instead of only linking them. And the original's own
   incident arithmetic does not close — it names three links, then seven
   more, then two found long-dead, and totals them as "nine" — so the stages
   are carried and the total is not, rather than guessing which figure was
   wrong ([no-invented-specifics](../practices/no-invented-specifics.md),
   [verify-decomposition](../practices/verify-decomposition.md)). **If someone
   can settle that count from `precedent-individual`'s history, the number
   belongs back in.** The private set's own practice slugs were left out of
   the universal text as well: they name nothing the rule needs, and this
   repository is public.

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
