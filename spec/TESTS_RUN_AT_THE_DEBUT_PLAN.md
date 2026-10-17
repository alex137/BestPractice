---
title:         Tests run at the Debut, never before a push
kind:          proposal
status:        accepted
opened:        2026-10-16
closed:        null
superseded_by: null
supersedes:    ["spec/CHANGED_CHECK_RUNS_ITS_TESTS_PLAN.md"]
audience:      contributor
summary:       "Before a push only the bare essentials run: the leak gate, the commit checks and the per-file checks. The practice checks on the changed files and every test moved to the Debut, and to GitHub's test after Produce (or the full local suite on main where that test is not due). The quick tier is closed: nothing joins it without the person's own words, and a harness test fails the moment it changes. A new test lands with its recorded time."
---

# Tests run at the Debut, never before a push

**Decided by Morgan on 2026-10-16 (strength: decided).** His words:
"all the testing EXCEPT THE BARE ESSENTIAL AND LEAK GATES SHOULD GO INTO
DEBUT, AND THE GITHUB TEST AFTER THE NEXT PRODUCE, AND THE MAIN TEST AFTER
THE NEXT PRODUCE IN THE CASES WHERE THE GITHUB ONE IS NOT RUN", and "LET'S
BAN ALL NEW TESTS BEFOREHAND EXCEPT WHEN EXPLICITLY DIRECTLY VERBALLY
AUTHORIZED". It reverses
[CHANGED_CHECK_RUNS_ITS_TESTS_PLAN.md](CHANGED_CHECK_RUNS_ITS_TESTS_PLAN.md),
which he approved on 2026-10-11.

## What happened

A landing on `staging` took 218 seconds of quick checks. Measured on a
small engine change, the quick check took 155 seconds:

| Step | Time |
|---|---|
| Leak gate | 18 s |
| Practice checks on the changed files (`precedent_check.py --changed-files-only`) | 42 s |
| Harness tests the change reaches (`verify_harness.py --for-change`) | 92 s |
| Everything else | under a second |

The harness step had a one-minute budget, read from
[tools/harness_check_times.json](../tools/harness_check_times.json). That
list was last recorded on 2026-10-09, a hundred tests had been added since,
and each one counted as 0.42 seconds. The five slowest of them took about a
minute between them; the slowest took 17.8 seconds. So 132 tests budgeted
at 60 seconds took 135.

## What runs before a push now

The basic tier, exactly the fourteen checks in
`BASIC_CHECKS_APPROVED` in
[tools/precedent_push_check.py](../tools/precedent_push_check.py), each with
the words that let it in. On a landing, the changed-files step adds only
per-file checks: a changed file compiles or parses, a new check has its test
and its planted case, a changed practice regenerated its views and counts,
and a new harness test carries its recorded time. It starts no test: a
changed check script's tests are named for the Debut, not run.

## What moved, and where it runs

The practice checks on the changed files and every test: the harness tests
a change reaches, each changed check script's `test_x.sh`, and the two split
checks. All of them are part of the full tier, which runs at the Debut
(`precedent_branches.py --run-tests`) and around Produce: GitHub's test
after the merge, or the full local suite on `main` where that test is not
due. A failure there is fixed on a feature branch and landed again.
`verify_harness.py --for-change REF` still says, and runs, what a change
reaches, when someone asks for it.

## Keeping it this way

- **The quick tier is closed.** `check_quick_tier_is_closed` in
  [tools/verify_harness.py](../tools/verify_harness.py) fails when
  `BASIC_CHECKS` differs from its list, when an approval carries no quoted
  words and date, or when the per-file step starts a test, the harness or
  the practice checks. A new entry needs the person's own words asking for
  that check before a push, and its time in seconds. Before asking, the
  session tells them that time and urges them to leave the check to the
  Debut instead (Morgan, 2026-10-16: "any new test beforehand needs to be
  explicitly approved and also have a time estimate and you need to
  strongly encourage the person to put it after and in debut etc"). The
  rule is [quick-tier-is-closed](../practices/quick-tier-is-closed.md).
- **A new test lands with its time.** The per-file step refuses a commit
  that adds a `check_` test to the harness without its entry in the timing
  list, and names `python3 tools/verify_harness.py --record-new-times`,
  which times only the missing tests. The hundred missing on 2026-10-16
  were filled in that way, in under two minutes.
