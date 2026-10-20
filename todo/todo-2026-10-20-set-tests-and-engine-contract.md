---
slug:              todo-2026-10-20-set-tests-and-engine-contract
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the set halves need push access to precedent-shared-ladder and precedent-shared-writing, which this session was refused; the prompt below carries them"
batch:             null
decision:          "the revised plan: BestPractice first, set tests run at Update Vendors, set-words reads the printed words, sound-checker item dropped"
decision_strength: decided
waiting_on:        null
noted:             2026-10-20
closed:            null
---
## What

Root issues from the 2026-10-19 enforcement-plan session, handed over as a
seven-item list and revised before any work started. Morgan, 2026-10-20
(strength: decided): "Let's do your version. Go act."

What changed from the list as handed over:

- **The order reverses.** Items 1(a), 3, 4 and 5 each have a set half that
  needs an engine change, and a set gets engine changes only through Update
  Vendors. So BestPractice goes first, then Update Vendors in each set, then
  the set halves.
- **1(b) moves to Update Vendors.** The break came from an engine refresh,
  which touches engine files, not a set test's own files, so "run the set
  tests a change touches" would not have caught it. A set's own tests run
  after its engine copy refreshes, before the update merges.
- **2 fixes the matcher, not the trigger.** Measured: the word was
  "staging", which the ladder set declares as an output-only pattern, and
  the quick check reads files with file patterns only. A universal
  practice's Rule and Detail are printed word for word by the gates, so
  they are read with the output patterns too.
- **7 is dropped.** The sound-checker set left the individual set's `brings` on
  2026-10-19 (precedent-individual spec/VENDORED_SHARED_SETS_PLAN.md,
  Step 4, ticked).

## Plan

BestPractice:

- [x] 6. Link the file names in
  [ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md](../spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md).
- [x] 2. set-words reads a universal practice's Rule and Detail with each
  set's output patterns.
- [x] 3. The engine declares the names the ladder's moves call
  (`MOVES_CORE` in [precedent_branches.py](../tools/precedent_branches.py)),
  and a harness case holds that each exists.
- [x] 1(a). A harness case holds Promote's copy names to the workflow
  templates, against the engine's own names.
- [x] 4. A set test claims a sibling helper,
  `tools/checks/tests/<name>_cases.py` beside `test_<name>.sh`.
- [x] 5. The materializer claims `tools/checks/tests/test_reply_check.sh`
  for a source with `reply_check.json`; BestPractice's own case says it
  tests the mechanism with planted patterns.
- [x] 1(b). Update Vendors in a practice set runs the set's own tests after
  the engine refresh, before the merge.

Sets, after Update Vendors brings them the engine above:

- [ ] Ladder: drop the four cases' template half and the
  `FileNotFoundError` catch; move [`ladder_branches_cases.py`](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/ladder/ladder_branches_cases.py) beside its
  test and out of promote.md's `ships`; a test that the moves module calls
  only declared `core.` names.
- [ ] Writing: `tools/checks/tests/test_reply_check.sh` with the
  discriminating cases from BestPractice's test.

## Findings

- Item 2 also found the full suite red on staging already:
  `check_ladder_off_engine_says_no_ladder_words` failed on the Rules of
  vendor-update-runbook and ci-workflow-approved. Fixed in the same commit.
- Item 1(a): `check_main_test_minutes_rule` had kept its engine half here
  all along; the set's copy duplicates it. The other two cases that read
  BestPractice's templates had moved whole, so their engine halves came
  back here. The fourth, `check_promote_branches_are_named_like_session_branches`,
  tests the set's own copy naming and only reads the light-check template
  as a fixture, so the set plants a workflow that carries
  `COPY_NAME_MARKER` instead.
- Item 3: 46 names, not the 29 first counted.
- Item 5: BestPractice's own case already said it tests the mechanism with
  planted patterns, so nothing changed there.

## Prompt Please

The set halves, for a session that can push to both sets. Push access to
them was refused in the session that built the BestPractice half
(2026-10-20).

**Paste into:** a new session rooted in BestPractice, with
precedent-shared-ladder and precedent-shared-writing attached with push
access, after the BestPractice half has reached the branch Update Vendors
follows.

```
From: the 2026-10-20 session that built the BestPractice half of todo/todo-2026-10-20-set-tests-and-engine-contract.md.
For: a new session rooted in BestPractice, with precedent-shared-ladder and precedent-shared-writing attached with push access.

Read todo/todo-2026-10-20-set-tests-and-engine-contract.md first. Its BestPractice boxes are ticked; do the two set boxes.

1. Update Vendors in each set, so each gets MOVES_CORE, the _cases.py helper rule and the reply-check test claim. The update now runs each set's own tests itself.
2. Ladder set:
   - Move tools/ladder/ladder_branches_cases.py to tools/checks/tests/ladder_branches_cases.py, point test_ladder_branches.sh at it, and take it out of practices/promote.md's ships.
   - In that cases file, drop the engine halves BestPractice now tests: check_main_test_minutes_rule keeps only part (3); check_private_repo_skipped_gate_is_not_main_test keeps only its wait cases; check_main_test_cadence keeps only the wait on a not-due copy and the _to_main_copy naming. check_promote_branches_are_named_like_session_branches plants a workflow carrying core.COPY_NAME_MARKER instead of reading templates/github-actions/light-check.yml.template.
   - Remove the FileNotFoundError catch in _run_all; nothing should need it.
   - Add a case: an ast scan of tools/ladder/ladder_branches.py finds every core.<name> in the engine's MOVES_CORE, with a planted undeclared name as the control.
3. Writing set: add tools/checks/tests/test_reply_check.sh, running precedent_reply_check.violations() on this set's own reply_check.json, with the discriminating cases from BestPractice's check_reply_check_refuses_an_unlinked_branch_or_file.
Then tick the boxes, close this item, and land each set the way it lands its work.
```
