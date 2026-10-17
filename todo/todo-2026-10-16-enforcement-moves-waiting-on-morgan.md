---
slug:              todo-2026-10-16-enforcement-moves-waiting-on-morgan
kind:              manual
domain:            engine
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-16
closed:            null
---
## What

Three calls left by
[spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md](../spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md):

1. **The ladder's own steps** (part 3) -- moving `--land`, Promote, Debut,
   Produce, the stage words and the reply pieces into the ladder set. A
   restructuring of several sessions; it starts only on his go-ahead.
2. **The commit-identity checks** (part 4) -- keep them in the engine as
   generic plumbing with the set's practice slugs taken out of engine code
   (recommended), or move them into the individual set, which reverses
   the 2026-10-10 decision.
3. **The GitHub ruleset** that refuses `claude/**` and `session/**`
   branches -- built and tested in the ladder set
   ([`tools/precedent_branch_rules.py`](https://github.com/themorgan/precedent-shared-ladder/blob/staging/tools/precedent_branch_rules.py)), applied nowhere. He names the
   repositories; for BestPractice the call is Alex's.

## Closes when

All three are decided, and what was decided is built or parked.

## Notes

- 2026-10-16, Morgan, on part 3: "not yet" (strength: decided).
- 2026-10-16, Morgan, on part 4: "keep it in best practice" (strength:
  decided) -- and, his emphasis, "sets practice names should NOT be in
  BestPractice!!!". Measured the same day on staging: the three sets'
  names and practice slugs appear about 1,400 times in BestPractice, in
  code (string literals, comments, tests) and in docs (practices, specs,
  open items, gotchas). Removing them is its own piece of work, proposed
  to him the same day.
- 2026-10-16, Morgan, on the ruleset: make it something a person opts in
  to in their own settings, so nothing changes for anyone who has not.
- 2026-10-16, Morgan: comments and history may keep the names; logic and
  tests may not. Built: the individual set's practice names are out of the
  engine's logic (practice_checked_by), and the individual and writing
  sets' names out of its tests. The default name `precedent-individual`
  stays (Morgan, "keep the default name", strength: decided). The ladder's
  names in logic wait for part 3.
- 2026-10-16, Morgan, strength: decided: the GitHub branch ruleset is
  opt-in for anyone, "including Alex who may opt in, in one of their
  precedent config files". Built in the ladder set (its PR #98): opt in
  with `"github_branch_rules": true` in identity.json or the user-level
  config; `--apply` then touches only repositories the person's own
  account owns. Nobody has opted in yet; nothing is applied.
- 2026-10-17, Morgan, on part 3, strength: decided: "let's spawn a new
  session to continue with the enforcement lives plan including starting
  with section 3 now". A new session rooted in BestPractice and the ladder
  set does it, planning each step first and landing each piece on staging.
- 2026-10-17: the step-by-step for part 3 is written into the plan
  ([section 3a](../spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md)):
  six pieces, each set half first, then the engine half. Waiting on
  Morgan's go-ahead for it, and on his call to keep
  [`precedent_branch_name.py`](../tools/precedent_branch_name.py) in the engine.
