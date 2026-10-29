---
slug:              todo-2026-10-20-set-tests-and-engine-contract
kind:              manual
domain:            engine
severity:          high
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          "the revised plan: BestPractice first, set tests run at Update Vendors, set-words reads the printed words, sound-checker item dropped"
decision_strength: decided
waiting_on:        null
noted:             2026-10-20
closed:            2026-10-28
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

- [x] Ladder: drop the four cases' engine halves and the
  `FileNotFoundError` catch; move the cases file beside its test and out of
  promote.md's `ships`. The "calls only declared names" test became a
  general engine check instead (below), so the ladder carries none.
- [x] Writing: its reply rules carry `_examples`, run by a general engine
  check, instead of a test file of its own.

Done 2026-10-28, generalized on Morgan's word that day (strength: decided):
"Make sure these are root fixes. Delete the duplicate test parts. And the
fixes shouldn't just be hardcoding for particular repos but the general
pattern etc. Booked." 

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

## The general versions (2026-10-28)

- **Bound set tools.** [precedent_resolve.py](../tools/precedent_resolve.py)'s
  `BOUND_SET_TOOLS` maps each key the engine hands itself to (today
  `branch_moves`) to the tuple declaring what such a tool may call. The
  check `bound-set-tool-calls-only-declared-names` reads it in any set; the
  harness holds every set cloned beside BestPractice. A new bound tool is
  one line in the registry, no new test.
- **Reply rules carry examples.** Any requirement in any reply_check.json
  may carry `_examples` (replies it refuses and lets through);
  `reply-rules-hold-their-examples` runs them through the real checker
  wherever a reply_check.json exists, and the advisory
  `reply-rules-carry-examples` names requirements with none. The
  underscore keeps an older engine reading the file live from warning. This
  replaced the 2026-10-20 special case for a set's own
  `test_reply_check.sh`, removed.
- **A skipped case is not a pass.** Measured: five of the ladder's cases
  had reported "not applicable" in its own repository since they moved
  there, two through guards written for BestPractice, two through the
  2026-10-19 stopgap, one pairing them. Update Vendors' run of a set's own
  tests now counts a not-applicable case as red, with its reason: that run
  is in the set's own repository on a fresh engine, where a skip means the
  case never runs anywhere that matters.
