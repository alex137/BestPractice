---
slug:              todo-2026-10-30-vendor-update-leftovers-in-the-ladder-and-individual-sets
kind:              manual
domain:            engine
severity:          medium
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-30
closed:            2026-10-30
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
- [x] **Ladder set:** the reply test's git-common-dir fallback is retired,
  after Update Vendors brought engine d21c1f11e875
  ([PR #152](https://github.com/themorgan/precedent-shared-ladder/pull/152));
  the full suite passed without it in a /tmp worktree.
- [x] **Individual set:** the band-aid rewording in its vendored-shared-sets
  plan is undone, after Update Vendors brought the same engine; its
  speculation-is-marked passes on the original words (2026-10-30).
- [x] **"MAIN'S TEST" warning:** the cause now leads the line instead of
  sitting in brackets at the end, where a relay dropped it (2026-10-30). The
  cause of the 2026-10-30 warning itself was never recorded; the next one
  carries it.

## Closes when

Every box above is ticked, each in the repository it names.
