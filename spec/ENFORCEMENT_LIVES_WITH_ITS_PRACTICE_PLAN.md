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

Status: plan, 2026-10-16. Parts 1, 2 and 4 are built; part 3 started
2026-10-17 on Morgan's go-ahead (strength: decided): "starting with
section 3 now".

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
| `ladder_words.py` (moved 2026-10-17: the words are the set's own data now, read by the engine's [`set_words.py`](../tools/set_words.py)) | the stage words and every ladder practice slug |
| `precedent_others_did.py` | the `others-did` reply block |
| [`precedent_stale_branches.py`](../tools/precedent_stale_branches.py), [`precedent_gate.py`](../tools/precedent_gate.py) | the `stale-branch-cleanup` page and its reply requirement |
| `precedent_upstream_review.py` | Debut and Produce wording |
| [`precedent_branch_name.py`](../tools/precedent_branch_name.py) | the name builder (part 1) |

The 2026-10-03 decision kept these in the engine
([LADDER_OPT_IN_PLAN.md](LADDER_OPT_IN_PLAN.md), D4, strength: assented);
that predates this practice. The move, in outline:

1. Split [`precedent_branches.py`](../tools/precedent_branches.py) into what any repository needs (its
   landing branch, a lock, composing a merge in a worktree, pushing it)
   and what only the ladder needs (staging, pre-staging, Promote, Debut,
   Produce). The first stays; the second ships from the ladder set.
2. `ladder_words.py`, `precedent_others_did.py` and the stale-branch page
   ship from the ladder set as they are.
3. The reply gate learns its ladder requirements from the set (its
   `reply_check.json` already exists), instead of from engine code.
4. Each piece lands with its engine copy removed in the same release, so a
   consumer's Update Vendors takes both halves at once.

This is a restructuring of its own, several sessions long. Morgan gave
the go-ahead on 2026-10-17 (strength: decided).

### 3a. The step-by-step (Morgan's go-ahead 2026-10-17)

Morgan, 2026-10-17, strength: decided: "Keep the branch name builder in
the engine (only activated if configure). Push access approved. Go ahead
with the plan. Booked." Read here as: the builder stays, and the engine's
own steps use its dated names only when a person's config turns them on.

Measured on staging at `8e122175`: the inventory names 23 ladder names
in engine code -- 16 in `ladder_words.py`, 2 each in
[`precedent_branches.py`](../tools/precedent_branches.py) and `precedent_upstream_review.py`, 1 each in
[`precedent_gate.py`](../tools/precedent_gate.py), `precedent_others_did.py` and [`verify_harness.py`](../tools/verify_harness.py).
[`precedent_branches.py`](../tools/precedent_branches.py) is about 5,000 lines, imported by 19 engine
tools, and its tests are a few hundred references in [`verify_harness.py`](../tools/verify_harness.py).

**Two facts shape the order.** A set's `ships:` path may not be an engine
file (`build_views.ship_path_problem`), so the set copy takes a new path:
everything lands under the set's own `tools/ladder/`. And BestPractice
runs its own ladder steps from the copy it materializes out of the
ladder set's clone, so the engine may drop a piece only once the set's
copy is on the set's `main`.

**So each piece goes in two halves, set first:**

1. *Set half.* The new file under `tools/ladder/` plus its tests, in the
   ladder set. Additive: nothing calls it yet, so a consumer that takes it
   alone carries one unused file. Booked on the set's `staging`, then
   Produce into its `main` on Morgan's word.
2. *Engine half.* Callers switch to the set copy (or to a generic seam),
   the engine copy is deleted, its tests leave [`verify_harness.py`](../tools/verify_harness.py), and the
   inventory loses that file's names. Booked on BestPractice `staging`;
   Produce on his word, never before the set half is on the set's `main`.

A consumer that runs Update Vendors after both Produces takes both
halves at once, as part 3's outline asks; one that takes only the set
half loses nothing.

**The pieces, smallest first:**

| # | Piece | Set gets | Engine keeps | Names gone |
|---|---|---|---|---|
| 0 | Delete pre-staging (Morgan, 2026-10-17, decided; [its open item](../todo/todo-2026-10-14-delete-pre-staging-code.md)) | -- | nothing of it but one migration (done 2026-10-17): `--sync-pre-staging`, Promote's pre-staging path and the full tier for staging are gone, and no mention is left in active use. The step that moves a repository off it became [tools/migration_retire_pre_staging.py](../tools/migration_retire_pre_staging.py), which Update Vendors runs without naming it | 0, but less to move |
| 1 | Stage words (built 2026-10-17) | its words as data: `owned_words` in its precedent-source.json, each pattern with the examples it must and must never match | a general check, `set-words-stay-in-their-set`, and its matcher [`set_words.py`](../tools/set_words.py): every set is held to the words the other sets in force declare. The ladder's own check would have guarded the ladder set, the one place its words are allowed | 16 |
| 2 | others-did (built 2026-10-17) | `tools/ladder/others_did.py` and its test, wired by the practice's own SessionStart and UserPromptSubmit hooks; the first prompt runs the day's check itself if the start-up hook missed it | [`precedent_commit_owners.py`](../tools/precedent_commit_owners.py): who made each commit, which Update Vendors' upstream note also reads | 1 |
| 3 | Branch-cleanup note (built 2026-10-17) | `tools/ladder/branch_page_note.py` and its test, named in its `reply_check.json` as `note_from_tool` | a general `note_from_tool` key: the reply gate runs a tool a set ships and prints what it says. The page itself, [`precedent_stale_branches.py`](../tools/precedent_stale_branches.py), stays: its delete button runs on GitHub, where nothing a set ships is present, and it names no set's rule. This piece's engine half lands first: an older engine only reports the new key, never refuses on it | 1 |
| 4 | Upstream review (built 2026-10-17) | `tools/ladder/upstream_review.py` and its test, named `step_review` in its precedent-source.json | [`load_set_tool`](../tools/precedent_resolve.py): Update Vendors and the stages ask for whatever step_review a set in force names, and write its lines into the commit | 2 |
| 5a | A seam, no behaviour change | -- | a branch-policy hook: a set that provides the `ladder` capability names a module, and the engine asks it for the tier branches, each one's check level and whether it is promote-only; with none, the landing branch and the trunk are all there is | 0 |
| 5b | Promote, Debut, Produce, `--land`, `--run-tests`, the tiers | `tools/ladder/ladder_branches.py`, built on the engine core | landing branch, lock, composing a merge in a worktree, pushing it | 2 |
| 5c | Their tests | the ladder tests from [`verify_harness.py`](../tools/verify_harness.py), beside the code | engine tests against a planted policy with made-up names | 1 |
| 6 | Close | -- | part 3's files off the held-on-purpose list; the inventory reads clean | -- |

**Kept in the engine (Morgan, 2026-10-17, decided, "only activated if
configured"):** [`precedent_branch_name.py`](../tools/precedent_branch_name.py)
stays in the engine. It enforces nothing and names no set's practice;
Update Vendors and the source bootstrap, which every repository runs,
name their branches with it. The ladder already ships the guard that
enforces the naming (part 1). It comes off the held list in piece 6.

**The push-check levels.** Morgan answered on 2026-10-17 (decided): a push
to `main` runs the quick checks and the full suite runs after (built on
staging at `71bbcc47`); pre-staging's own spot goes with piece 0. 5b
carries both as they stand.

**Before piece 0 deletes the step that moves a repository off
pre-staging**, every repository was checked on 2026-10-17. Four still
have a `pre-staging` branch, all of it already in their `staging`.
One of Morgan's private repositories still declares `landing_branch:
pre-staging` and has two commits only there; they move into its
`staging` first.

**The step that moves a repository off pre-staging is not deleted.**
It became a migration on 2026-10-17
([tools/migration_retire_pre_staging.py](../tools/migration_retire_pre_staging.py),
which Update Vendors runs without naming it), so each repository is
moved at its own next Update Vendors and no repository has to be checked
from here first. A sweep across many repositories is never part of this
plan: attaching or opening more than two beyond the ones a session
started with waits for Morgan's approval, naming each (Morgan,
2026-10-17, decided: "ANYTHING TO OPEN ALL THE REPOS MUST GET SESSION
USER APPROVAL"). The 2026-10-17 sweep above ended with 21 repositories
attached to one session, which is why.

**Two suggestions for 5b**, from another session's Root issues list
(2026-10-17), to weigh when the code moves:

- Produce's other-work note (`_other_work_note`) tells a session to name
  others' commits "when asking to approve this move", but Produce is
  itself the go-ahead. Name them in the reply that reports the move, and
  tell the person's own other sessions apart from other people with
  [tools/precedent_commit_owners.py](../tools/precedent_commit_owners.py).
- `--land` lands a commit from a hand-named branch that the ladder set's
  branch-name guard refused at `git push`, because `--land` pushes
  staging instead. Whether the naming rule holds at `--land` too is
  decided with 5b, through the generic hook point, never as engine code
  that names the ladder.

**Piece 5 waits for the copied-in shared sets work** (Morgan,
2026-10-19: "Your plan is fine", strength: assented). That plan asks
whoever lands its Step 1 to tell the session holding piece 5. Another session's plan, kept in
Morgan's individual set because it names private repositories, has as
its Step 1 a change to this engine: a shared set may be copied into the
repository that uses it, refreshed and checked for freshness, instead of
attached beside it at session start; and the ladder becomes binding in a
repository when one of its code owners says so. That session writes the
engine half into `spec/` here when it builds it. Piece 5 touches the same
places, so the two never run side by side:

- 5a's seam finds the ladder's module through the set that provides the
  `ladder` capability. Step 1 changes where that set's files are and
  whether the ladder applies in a repository at all. Built after Step 1,
  5a asks the resolver where the set is, copied in or attached, and
  treats a repository whose code owners have not bound the ladder like
  one with no ladder. Built before it, 5a would be built twice.
- 5b's code goes to `tools/ladder/` in the ladder set, which since
  2026-10-19 also holds thirteen rules moved there from Morgan's
  individual set (`promote-only`, `stage-words` and `ladder-required`
  among them). 5b reads them where they live now.

**Pre-staging in the practice sets.** BestPractice was cleared on
2026-10-17 (piece 0). The sets' engine copies clear as each set takes
the engine; what is left is in their own files, nearly all of it in the
ladder set, including the rules moved there on 2026-10-19. That cleanup
runs after the other session's 2026-10-19 Produces of both sets, both
done, and never while that session is editing the same files.

**Small calls, noted.** The set's tests for a tool that is not a check
go in `tools/checks/tests/` beside the rest, since that is where the set's
runner already looks; piece 1 confirms a consumer's sync skips a test
with no check beside it instead of complaining about it.

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
