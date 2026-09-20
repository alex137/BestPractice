---
slug:            gotcha-2026-09-07-a-test-fixture-that-asserts-on-commit-identity-must-own-that
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

A test fixture that asserts on commit identity must OWN that identity,

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A test fixture that asserts on commit identity must OWN that identity,
  or the session's environment silently becomes part of the test.** FIXED
  2026-09-07 in [verify_harness.py](../tools/verify_harness.py) and recorded
  here for the story, not for a workaround -- if you hit it, your checkout
  predates the fix. `check_identity_reaches_a_repo_that_did_not_exist_yet`
  built its fixture by copying `os.environ`, pointing `HOME` at a temporary
  directory, setting a global identity inside it and asserting that commits
  there used it. It popped `PRECEDENT_ALLOW_ANY_AUTHOR`,
  `PRECEDENT_COMMIT_EMAIL` and `PRECEDENT_COMMIT_TZ`, but NOT the
  `GIT_AUTHOR_*` variables -- and those outrank `git config --global
  user.*`. So in a session that exports them (the individual practice set's
  `.claude/settings.json` does) every fixture commit was authored by the
  real person, and **4 of that check's 11 stated cases failed, none of them
  real**: *a repo created AFTER the hook commits as the person*, *a
  bot-authored commit is refused there*, *and the refusal names itself as
  the global backstop*, *a correct commit is not blocked*. **Three of the
  four failed in the direction that wastes the hour** -- a bot identity the
  fixture plants in LOCAL config was never the author any more, so the
  refusal each case waits for correctly did not fire, and a working backstop
  read as broken in a check whose name is *"the commit identity reaches a
  repo attached after the hook ran"*. That is the wrong-author incident this
  check exists to catch, so the failure impersonates the bug. Measured
  2026-09-07, same tree, no code change: `1 failed` with the variables
  exported, `0 failed` under `env -u`. **The fix drops the author trio once
  at module scope**, beside the `PRECEDENT_ALLOW_ANY_AUTHOR` line that
  solved the mirror-image problem, rather than in the one fixture that
  happened to notice -- a fixture written later would inherit the same
  invisible dependency. `GIT_AUTHOR_DATE` goes too (the same check asserts
  on the author-date offset); `GIT_COMMITTER_*` deliberately does not,
  because nothing here or in
  [commit-identity.sh](../.claude/hooks/commit-identity.sh) reads the
  committer. Verified against the hostile case: with all three exported,
  `GIT_AUTHOR_DATE` set to a `+0000` that would independently have broken
  the timezone case, the run is `0 failed`. The reusable half is the first
  sentence -- this is the second time an ambient variable turned a green
  gate red here, after the `requireVocabulary` entry above, and both cost an
  hour to the same shape: two mechanisms wanting opposite environments,
  neither saying so.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
