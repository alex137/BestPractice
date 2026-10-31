---
slug:              todo-2026-10-30-root-issues-from-the-vendor-update-fixes-session
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       null
remind_on:         null
blocked_on:        "out of scope for the session that found them (session_01Xcy6U1UBGg4Vvg5QFAE1Mz, which was finishing a Produce); handed on as a Prompt Please"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-30
closed:            null
---
## What

Root issues found by the session that fixed the 2026-10-30 vendor-update
problems ([PR #1440](https://github.com/alex137/BestPractice/pull/1440),
[PR #1441](https://github.com/alex137/BestPractice/pull/1441),
precedent-shared-ladder
[PR #150](https://github.com/themorgan/precedent-shared-ladder/pull/150) and
[PR #152](https://github.com/themorgan/precedent-shared-ladder/pull/152)).
Ordered by harm.

- [ ] **1. Broke: `--run-tests BRANCH` reports FAILED and skips the tests
  when the branch is high-risk.** `_run_tests` in
  [tools/precedent_branches.py](../tools/precedent_branches.py) runs the
  check with `dest=staging`, so the ladder set's `check_landing_takes_a_pr`
  judges the branch as a landing and says "take a pull request". The check
  fails fast, the suite stops before `run_all.sh`, and the run is recorded
  FAILED for a branch whose tests all pass. Seen on precedent-shared-ladder
  PR #152; only `PRECEDENT_PUSH_CHECK_ALL=1` showed the tests passing. Fix:
  a `--run-tests` run is not a push, so the check stands aside there (the
  engine marks the run, the check skips on the mark); the pre-push hook
  still enforces at the real landing. Lands in BestPractice's engine and
  precedent-shared-ladder's check.
- [ ] **2. Could break: a reply example's verdict depends on which folder
  runs it.** precedent-shared-writing's rule-links example
  ("See practices/rule-links.md before merging", with the path in code font) is refused only when that
  file exists under the project folder the reply checker reads
  (`CLAUDE_PROJECT_DIR`, else the working directory). Run from anywhere but
  the set, it is let through and the example "fails". BestPractice's new
  `reply-checker-keeps-set-examples` works around this by running each
  set's examples in a subprocess rooted in the set: a band-aid. Fix:
  `_reply_example_problems(root)` in
  [tools/precedent_check.py](../tools/precedent_check.py) evaluates
  examples with the project folder set to `root`, for every caller; then
  drop the subprocess in the new check.
- [ ] **3. Could break: a seeded handoff that needs push access, or a
  reply, has no route when the sender cannot give one.** The handoff into
  this session said "attach these two sets with push access" and "send
  your reply to session_01Xcy6U22RkC3KXewuqpCQVf". Auto mode refused the
  attach as access added on another session's say-so, which cost a round
  trip to Morgan, and the sending session had ended, so the reply could not
  be sent. Fix, in [prompt-please](../practices/prompt-please.md) and the
  seeded-prompt practice: a handoff that needs push access says in its
  first lines that the person must approve the attach, and one that wants
  a reply names a fallback (an open item in the root repository) for when
  the sender is gone.
- [ ] **4. Warning: "it carries the merge too" in [AGENTS.md](../AGENTS.md)
  reads as if [`precedent_update.py`](../tools/precedent_update.py) merges.** It ends at "DONE -- commit,
  then land", so every set needed the same branch, commit, landing and
  Produce by hand, four times today. Fix: the tool makes the update branch
  and commits it, and prints the landing command; AGENTS.md says the phrase
  carries the authorization and the tool stops before landing.

Considered and left out: BestPractice's main went red after a Produce on a
check this session added (issue #1443). The quick tier skips the harness by
decision ("merge and get notified"), and that is what happened; the miss
was this session's, which could have run `verify_harness.py --for-change`
by hand.

## Closes when

Every box above is ticked, each in the repository it names.
