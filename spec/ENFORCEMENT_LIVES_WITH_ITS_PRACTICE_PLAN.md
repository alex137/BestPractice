---
title:         "Enforcement lives with its practice: the move plan"
kind:          proposal
status:        accepted
opened:        2026-10-16
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Moves each practice set's enforcement out of Precedent's engine and into the set: built for the ladder's branch-naming rule and go-update's high-risk line; the ladder's own steps wait on Morgan's go-ahead; the commit-identity checks wait on one decision of his."
---
# Enforcement lives with its practice: the move plan

Status: plan, 2026-10-16. Parts 1, 2 and 4 are built; part 3 waits on
Morgan's go-ahead ("not yet", 2026-10-16).

The rule is
[enforcement-lives-with-its-practice](../practices/enforcement-lives-with-its-practice.md):
a practice's checks, tools and hooks live in the repository the practice
lives in, and the engine knows how to run them, never what any one set's
rule is. Its check, `python3 tools/precedent_check.py --only
enforcement-lives-with-its-practice`, is the inventory this plan works
from. It warns, without refusing, until the moves below land
(`revisit: 2026-11-16`).

**Every very deep check reads it again** (from 2026-10-17): its `SET
INDEPENDENCE` section runs the inventory, lists part 3's files as held on
purpose, and has the session fix the rest in the same pass
([very-deep-check](../practices/very-deep-check.md), Pass 2's question
26). The inventory reads every Python file under `tools/`, the harness
and BestPractice's own checks included, plus test scripts, universal
practices' rules, and whether each set check has its test in the set.
Names kept on purpose are in its `_SET_NAMES_KEPT`.

## 1. Built: the ladder's branch-naming rule

The ladder set's `act` now ships its enforcement:
[`tools/branch_name_guard.py`](https://github.com/themorgan/precedent-shared-ladder/blob/staging/tools/branch_name_guard.py) refuses a push to the harness's own branch
name, or a new branch named by hand, and notes the first commit on a
harness-named branch; [`tools/precedent_branch_rules.py`](https://github.com/themorgan/precedent-shared-ladder/blob/staging/tools/precedent_branch_rules.py) reports, and with
`--apply` adds, the GitHub ruleset that refuses creating `claude/**` and
`session/**` branches. The engine's naming refusal, push note, commit-note
hook and Update Vendors line are gone. What the engine gained is generic:

- a `pre-push` hook event a practice can declare, run by the global
  pre-push through [`precedent_hooks.py --git`](../tools/precedent_hooks.py), in every session shape
  (Morgan, 2026-10-16: approved "just for the branch related check"; each
  further pre-push hook is his call);
- a refusal of every push while a declared or brought source did not
  load, and a session start that opens with the `add_repo` call for each;
- `PRECEDENT_PUSH_DESTINATION` and `PRECEDENT_CHANGED_SINCE`, set for the
  checks a push check runs, so a set's check can judge a push by where it
  goes.

**Left in the engine on purpose:** [`precedent_branch_name.py`](../tools/precedent_branch_name.py)'s name
builder. It enforces nothing, and the engine's own ladder steps (a
landing, a Promote, Update Vendors) name their branches with it. It moves
with them in part 3.

**The GitHub ruleset is opt-in, per person** (Morgan, 2026-10-16): anyone
turns it on in their own identity.json or user-level config, and
`--apply` then touches only repositories their own account owns. Nobody
has opted in yet, so it is applied nowhere.

## 2. Built: go-update's high-risk line

[`check_landing_takes_a_pr.py`](https://github.com/themorgan/precedent-shared-ladder/blob/staging/tools/checks/check_landing_takes_a_pr.py), in the ladder set, refuses a push straight
to the landing branch that changes a CI workflow, the gating engine files
or `tools/checks/`, and prints the pull-request route. An engine file
byte-identical to what the engine manifest recorded vendoring from
BestPractice's main is exempt (Morgan, 2026-10-16); a workflow never is.
Update Vendors' DONE says when an update takes a pull request.

## 3. Waiting on Morgan: the ladder's own steps

The ladder's stages run on engine code today, and the inventory names it:

| Engine file | What is the ladder's |
|---|---|
| [`precedent_branches.py`](../tools/precedent_branches.py) | `--land`, `--promote`, `--run-tests`, the tier branches, promote-only, the Debut and Produce steps |
| [`ladder_words.py`](../tools/ladder_words.py) | the stage words and every ladder practice slug |
| [`precedent_others_did.py`](../tools/precedent_others_did.py) | the `others-did` reply block |
| [`precedent_stale_branches.py`](../tools/precedent_stale_branches.py), [`precedent_gate.py`](../tools/precedent_gate.py) | the `stale-branch-cleanup` page and its reply requirement |
| [`precedent_upstream_review.py`](../tools/precedent_upstream_review.py) | Debut and Produce wording |
| [`precedent_branch_name.py`](../tools/precedent_branch_name.py) | the name builder (part 1) |

The 2026-10-03 decision kept these in the engine
([LADDER_OPT_IN_PLAN.md](LADDER_OPT_IN_PLAN.md), D4, strength: assented);
that predates this practice. The move, in outline:

1. Split [`precedent_branches.py`](../tools/precedent_branches.py) into what any repository needs (its
   landing branch, a lock, composing a merge in a worktree, pushing it)
   and what only the ladder needs (staging, pre-staging, Promote, Debut,
   Produce). The first stays; the second ships from the ladder set.
2. [`ladder_words.py`](../tools/ladder_words.py), [`precedent_others_did.py`](../tools/precedent_others_did.py) and the stale-branch page
   ship from the ladder set as they are.
3. The reply gate learns its ladder requirements from the set (its
   `reply_check.json` already exists), instead of from engine code.
4. Each piece lands with its engine copy removed in the same release, so a
   consumer's Update Vendors takes both halves at once.

This is a restructuring of its own, several sessions long. Nothing in it
starts without Morgan's go-ahead.

## 4. Decided and built: the commit-identity checks stay in the engine

The individual set's commit-author and date-zone practices point
`checked_by` at the engine's [tools/check_commit_author.py](../tools/check_commit_author.py) and
[tools/check_commit_dates.py](../tools/check_commit_dates.py), which name no one: they read the person
from their declared identity. Morgan, 2026-10-16, strength: decided:
"keep it in best practice" -- and "sets practice names should NOT be in
BestPractice". So the engine no longer names those practices anywhere in
its logic: the checks and the push check ask
[`precedent_identity.practice_checked_by()`](../tools/precedent_identity.py) which practice in force names
the script, and the engine's tests use planted practice names. The same
pass took the writing set's names out of the engine's tests; that set has
no logic in the engine.

What stays, on purpose: comments (Morgan: "I don't really care if they're
mentioned in comments"), history, `go-merge` (a name BestPractice itself
retired, used by the tests of retirement), and the default individual set
name below.

## 5. Not a finding: the default individual set name

A handful of engine files name `precedent-individual` as the default name
of a person's individual set, the convention a fresh install uses when
nothing else is declared. That is a convention every person shares, not
one set's rule (Morgan, 2026-10-16, strength: decided: "keep the default
name"), and the inventory check does not count it.

## 6. How it reaches consumers

Every piece above reaches a consuming repository through Update Vendors:
the engine half when it refreshes the engine, the set half when it syncs
the set. For part 1 both halves landed together, so a consumer that takes
both stays enforced throughout. One that takes only the engine half loses
the old engine refusal before it has the set's guard. Taking both in the
same Update Vendors run avoids that gap.
