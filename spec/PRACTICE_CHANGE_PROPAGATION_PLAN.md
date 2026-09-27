---
title:         Practice change propagation
kind:          proposal
status:        accepted
opened:        2026-09-27
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "When a practice is renamed, retired, deleted or reworded, every citation of it -- here, in every declared practice set, and in every consuming repo -- is found and fixed, or handed off. A lookup tool that travels with the engine, a blocking check that runs wherever the engine does, a merge-moment prompt, an Update Vendors step, and practice files retired in place rather than deleted."
---

# Practice change propagation

**Adopted 2026-09-27, Morgan: "I agree with the two calls you made. Go
update."** (strength: assented -- agreement with a plan this session
proposed.) The rule it produced is
[practices/practice-change-propagates.md](../practices/practice-change-propagates.md).

## The problem

**When a practice was renamed, retired or reworded here, nothing looked for
its citations anywhere else.** The go-merge -> go-update rename (2026-09-26)
landed cleanly in BestPractice. The private sets kept citing `go-merge` as
the rule in force, and it surfaced a day later when Morgan used them.

Some pieces already existed, and none of them covered this:

| Existing piece | Why it did not cover this |
|---|---|
| `cross-source-rollout` | a judgment rule, no check; scoped to mechanism changes, and said outright it excluded "this repo's own prose" |
| `rename-updates-links` | checks one repository only |
| `practice-links-travel` | checks links inside the publishing set; a link to a stub passes because the stub file exists; never reads a backticked name |
| stub forwarding in the engine (2026-09-26) | makes a stale link *work* in a consumer; never fixes the text in the set |
| `very-deep-check`'s cross-source item | on request only |
| Update Vendors step 10 | retires hooks, workflows and branch names; never a practice's old name |

**Why the drift builds up: the session that changes a practice usually
cannot write to the sets.** Measured 2026-09-27: this session fetched all
four sets and a push to one was refused, because they belong to a different
owner than BestPractice. So the fix cannot rely on the changing session
cleaning up. It makes the drift visible in the repository that can fix it,
and it writes the handoff.

## What was built

1. **The lookup, [tools/precedent_practice_refs.py](../tools/precedent_practice_refs.py).**
   Given slugs, or `--changed-since REF` (what this branch renamed,
   withdrew, deleted or reworded), or `--withdrawn` (everything in force
   nowhere), it reads the repository and every source it declares and lists
   each citation as **live** or **history**. `--handoff` prints a
   paste-ready block for the repositories a session cannot push to. It
   travels with the engine, to sets and consumers alike.
2. **The check, `practice-change-propagates`** in
   [tools/precedent_check.py](../tools/precedent_check.py). It refuses a
   live link or [`precedent_show.py`](../tools/precedent_show.py) lookup naming a practice in force
   nowhere, or one that only forwards to another slug; any such mention
   inside an in-force practice's `## Rule`; and deleting or renaming away a
   practice file. It reads only files the repository owns.
3. **The merge moment.** The practice declares `gates: ["merge"]`, so the
   merge gate prints it: run the lookup on what the branch changed, fix what
   is reachable, hand off the rest.
4. **The consuming side.** [tools/precedent_update.py](../tools/precedent_update.py)
   runs the lookup after the refresh, as the `citations` step, and
   [vendor-update-runbook](../practices/vendor-update-runbook.md) step 10(i)
   says what to do with it.
5. **`cross-source-rollout`** now names a practice's slug, status and Rule
   as mechanism, not prose.
6. **Tests** in [tools/verify_harness.py](../tools/verify_harness.py):
   `check_practice_refs_sorts_live_from_history` and
   `check_practice_change_propagates_refuses`, each with a negative control.

## The two calls (Morgan agreed, 2026-09-27)

- **The check blocks rather than warns.** A warning gets scrolled past, and
  the fix is always small.
- **A practice file is retired in place, never deleted.** Without the stub,
  nothing can tell a withdrawn name from an unrelated word in backticks.

## What the check does not refuse, and why

A bare backticked name outside a Rule section. *"Exactly as `session-text`
drew this line"* is lineage, and no pattern tells it apart from a live
citation. The lookup lists those for a session to read. A **reworded** Rule
keeps its slug, so no check can judge whether a citation still describes it;
the lookup lists every citation of it as `read`.

## The one-time cleanup

The first run found six live citations: three in BestPractice, fixed in the
same change, and one in each of three sets:

- `precedent-individual`: its README links `next-steps-after-commit` (now
  `the-boildown`)
- `precedent-shared-repo-maintenance`: its `vendor-neutral-by-default`
  practice links `session-text` (now `prompt-please`)
- `precedent-shared-writing`: its `name-the-branch` practice links
  `go-merge` (now `go-update`)

Those went out as a handoff to a session rooted in `precedent-individual`.
The sets pick up the check when their engine next refreshes from `main`, and
it will go red on any of the three still unfixed.
