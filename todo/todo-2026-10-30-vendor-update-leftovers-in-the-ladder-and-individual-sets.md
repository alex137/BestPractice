---
slug:              todo-2026-10-30-vendor-update-leftovers-in-the-ladder-and-individual-sets
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       null
remind_on:         null
blocked_on:        "a Produce of BestPractice staging into main, then Update Vendors in the ladder and individual sets: both sets run their vendored engine copy, which only takes BestPractice main"
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

- [x] **Ladder set:** `check_landing_takes_a_pr` no longer refuses a file
  already on main by its pull request, so a red-main fix stays green
  (precedent-shared-ladder
  [PR #150](https://github.com/themorgan/precedent-shared-ladder/pull/150),
  2026-10-30).
- [x] **Ladder set:** an unusable `--work` is PROMOTE REFUSED with exit 1,
  and [`produce.md`](https://github.com/themorgan/precedent-shared-ladder/blob/staging/practices/produce.md)
  says what `BRANCH` is (same pull request).
- [x] **Ladder set:** `test_landing_authority_reply_check.sh` reads
  `$PRECEDENT_SOURCE_DIR_PRECEDENT` first (same pull request).
- [ ] **Ladder set, once its engine copy carries `source_dir_env`:** retire
  that test's git-common-dir fallback; its comment says RETIRE.
- [ ] **Individual set, once its engine copy carries the narrower
  speculation-is-marked:** undo the band-aid rewording in its
  vendored-shared-sets plan ("after an exploratory session" back to "after
  a brainstorm"). Undoing it earlier turns that set's own check red.
- [x] **"MAIN'S TEST" warning:** the cause now leads the line instead of
  sitting in brackets at the end, where a relay dropped it (2026-10-30). The
  cause of the 2026-10-30 warning itself was never recorded; the next one
  carries it.

## Closes when

Every box above is ticked, each in the repository it names.
