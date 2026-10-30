---
slug:              todo-2026-10-30-vendor-update-leftovers-in-the-ladder-and-individual-sets
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       null
remind_on:         null
blocked_on:        "push access to themorgan/precedent-shared-ladder and themorgan/precedent-individual (attach refused in session_01Xcy6U1UBGg4Vvg5QFAE1Mz)"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-30
closed:            null
---
## What

The 2026-10-30 Update Vendors in the precedent-* sets hit five problems.
BestPractice's share landed in staging by
[PR #1440](https://github.com/alex137/BestPractice/pull/1440). The rest lives
in the ladder and individual sets, which the session could not push to.

- [ ] **Ladder set, after the engine reaches it:**
  `tools/checks/tests/test_landing_authority_reply_check.sh` defaults
  `UNIVERSAL_REPLY_CHECK` to `$PRECEDENT_SOURCE_DIR_PRECEDENT/reply_check.json`
  (exported by the push check since PR #1440) and drops its git-common-dir
  fallback from precedent-shared-ladder PR #148.
- [ ] **Ladder set:** `check_landing_takes_a_pr` exempts the pull request that
  fixes a red main, so `--run-tests main` does not go red again until the fix
  also reaches staging. The check and [`landing_pr_guard.py`](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/landing_pr_guard.py) exist only in the
  ladder set; BestPractice holds untracked copies.
- [ ] **Ladder set:** [`produce.md`](https://github.com/themorgan/precedent-shared-ladder/blob/main/practices/produce.md) explains or drops `--work BRANCH`, and
  Promote exits non-zero on a ref that does not exist instead of printing
  "NOTHING TO PROMOTE" with exit 0.
- [ ] **Individual set, after the engine reaches it:** undo the band-aid
  rewording in its vendored-shared-sets plan ("after an exploratory
  session" back to "after a brainstorm"); speculation-is-marked no longer
  flags it.
- [ ] **"MAIN'S TEST: could not read GitHub's issues"** did not reproduce
  on 2026-10-30: all four repositories read their issues. The message carries
  the cause in parentheses; get that text from the next session that sees it.
  Not measured: precedent-individual's clone had no credential helper until
  session start wrote one that day.

## Closes when

Every box above is ticked, each in the repository it names.
