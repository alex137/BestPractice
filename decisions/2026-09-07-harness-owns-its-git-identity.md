---
date: '2026-09-07'
question: |
  A session that exports GIT_AUTHOR_NAME/GIT_AUTHOR_EMAIL made
  verify_harness.py's check_identity_reaches_a_repo_that_did_not_exist_yet
  fail 4 of its 11 stated cases, none of them real: those variables outrank
  `git config --global user.*`, so the fixture's own planted identity never
  became the author. Should this be documented as an environment gotcha with
  an `env -u` workaround, or fixed so the harness owns the identity its
  fixtures assert on?
decision: |
  Fixed, not documented-around. tools/verify_harness.py drops
  GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL and GIT_AUTHOR_DATE from os.environ once
  at module scope, beside the existing PRECEDENT_ALLOW_ANY_AUTHOR line that
  solved the mirror-image problem. GIT_COMMITTER_* is deliberately left
  alone. AGENTS.md's gotcha entry is kept, rewritten from a workaround into
  the story plus the general rule, because an old container can still carry
  a checkout that predates the fix.
alternatives: |
  ["Leave it documented with the `env -u GIT_AUTHOR_NAME -u
  GIT_AUTHOR_EMAIL` workaround, as originally recorded -- rejected because
  the failure impersonates the exact bug the check exists to catch, so every
  session that meets it pays the diagnosis again, and a workaround only helps
  the session that already knows",
  "Pop the variables inside
  check_identity_reaches_a_repo_that_did_not_exist_yet alone, the minimal
  edit -- rejected because the dependency is invisible: a fixture written
  later inherits it and the next session pays the same hour. The measurement
  that only one check fails today is a fact about today's checks, not a
  property of the harness",
  "Also drop the GIT_COMMITTER_* trio for symmetry -- rejected as a
  guess at a problem nobody has had. Nothing in the harness or in
  commit-identity.sh reads the committer; the hook resolves `git var
  GIT_AUTHOR_IDENT`. Verified by grep before deciding",
  "Set the identity the fixture wants via GIT_AUTHOR_* instead of global
  config -- rejected because the check's whole subject is what a repository
  inherits from GLOBAL config when nothing else is set, which is the
  wrong-author incident it was written for. Asserting it through the
  variables that outrank global config would test the opposite thing"]
decided_by: Morgan, in session, after the gotcha was written
---

## Why the fix rather than the note

The entry had already been written the honest way -- trigger named, four
failing cases named, `env -u` invocation given -- and it was still the wrong
artifact. The failure's name is *"the commit identity reaches a repo attached
after the hook ran"*, and three of the four failing cases fail because a bot
identity the fixture plants in local config is no longer the author, so the
refusal each case waits for correctly does not fire. **A working backstop
therefore reads as a broken one, in the check written for the wrong-author
incidents that produced six bad commits.** A session meeting that cold has to
rule out a real identity regression before it can reach the environment, and
the note only helps a session that already suspects the environment.

The general rule is worth more than this instance: **a fixture that asserts on
identity must own identity**. This is the second ambient variable to turn a
green gate red here -- `precedent.requireVocabulary` was the first -- and both
have the same shape, two mechanisms wanting opposite environments with neither
saying so.

## What was measured, not assumed

- The mechanism, in an isolated temp `HOME`: with the variables unset a commit
  is authored by the global identity; with them set, by the environment's.
  Same repository, same command.
- The blast radius: a full run with both exported was `1 failed` -- one check,
  4 of its 11 cases -- so the targeted fix would have been sufficient *today*.
  That is what argued for the module-scope fix instead: the number is a
  property of the current check list, not of the harness.
- CI supplies no git identity at all (no `user.email`, no `GIT_AUTHOR_*` in
  any workflow), so dropping the variables cannot break it. Checked before
  changing anything, because a central env change that breaks CI is the
  obvious way this fix could have gone wrong.
- After the fix, with all three variables exported and `GIT_AUTHOR_DATE` set
  to a `+0000` that would independently have broken the timezone case, the run
  is `0 failed`.

## What this does not close

The harness now ignores the ambient author identity, but **nothing asserts
that it still does.** A future edit could reintroduce the dependency and only
a session running in an exporting environment would find out. A regression
check was considered and not written: the honest version has to run a fixture
under a polluted environment, which is most of the cost of the check it
guards. Left here rather than in TODO.md because it is a judgment call about
whether the guard earns its cost, not queued work.
