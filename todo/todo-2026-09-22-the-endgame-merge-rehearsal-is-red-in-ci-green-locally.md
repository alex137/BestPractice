---
slug:              todo-2026-09-22-the-endgame-merge-rehearsal-is-red-in-ci-green-locally
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-22
closed:            null
---
## What

**`verify_harness (everything else)` has been failing on
`precedent-beta-v01` itself, on one check, and every pull request opened
against it inherits the red.** The failing check is
`check_endgame_merge_finds_the_silent_drop` in
[tools/verify_harness.py](../tools/verify_harness.py):

    the endgame-merge rehearsal names the silently-dropped path (6 stated
    cases; the drop/conflict split is the controlling one) -- the file
    touched since the merge base is a CONFLICT, not a drop; work newer than
    the merge base arrives cleanly, in neither set; undoing the revert makes
    the same merge come back clean -- dropped=['drop.txt', 'keep.txt',
    'later.txt'], conflicts=[]

Everything else passes: **250 passed, 1 failed, 5 not yet applicable**, and
the other three jobs of the Deep check are green.

## Why it matters

It is red on the base branch, so it is nobody's pull request to fix and
every pull request has to establish that separately before it can merge —
which is exactly the reading that makes a standing red stop being read at
all. Runs 1692 through 1696 of `Deep check` all conclude `failure` on this
one check; work has been landing through it.

## What is known

**It does not reproduce locally.** A full
[tools/verify_harness.py](../tools/verify_harness.py) run in a hosted
session container on 2026-09-22 exits 0 on the same tree that CI fails.
`dropped` coming back with all three fixture paths and `conflicts` empty
says the rehearsal's own merge behaved differently on the runner than it
does here — a git version difference (the runner reports git 2.55.0) or
something about the fixture repo's construction under that git is the
first place to look, not the practice the check enforces
([very-deep-check](../practices/very-deep-check.md), pass 4).

## Diagnosed 2026-09-22 — it is not the git version, and the rehearsal is the thing that is wrong

**Reproduced locally on git 2.43.0, byte-for-byte the same failure text, by
removing one thing: the global git identity.**

    GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null \
      python3 -c "...check_endgame_merge_finds_the_silent_drop()"
    -> dropped=['drop.txt', 'keep.txt', 'later.txt'], conflicts=[]

So the runner's git is a red herring. **A CI runner has no global git
identity; this container does** (the session-start backstop writes one), and
that is the whole difference.

**What actually happens.** `endgame_merge` in
[tools/very_deep_check.py](../tools/very_deep_check.py) runs
`git merge --no-commit --no-ff` in a throwaway worktree. Its own comment
says *"`--no-commit` never writes a commit, so git never asks for one"*.
**That claim is false.** Git checks the committer identity before it merges
and refuses outright:

    Committer identity unknown
    fatal: unable to auto-detect email address (got 'root@vm.(none)')
    exit=128

**And the tool cannot tell that apart from a real finding**, because the
merge's return code is deliberately ignored — the next comment says *"the
return code says nothing here -- what the merge DID is read out of the
index."* With no merge having run, the index still holds only the base
branch's files, so `expected - present` names **every file on the
integration branch** and `conflicts` is empty. A refusal to run is reported
as the most alarming possible finding.

**This is a live defect in a vendored tool, not a test artifact.**
[tools/very_deep_check.py](../tools/very_deep_check.py) ships to
consuming repos. Any session running a very
deep check where no global git identity is set gets `status: findings`
naming every file on the integration branch as silently dropped. The check
is right; the rehearsal is wrong.

## Next step

Two parts, and the second is the one that lasts.

1. **Give the throwaway merge an identity**, on the invocation rather than
   in config — `git -c user.name=... -c user.email=...`. Note the existing
   comment's warning: an address literal in this public tree is a leak-gate
   finding, so use a non-address form or the `GIT_COMMITTER_*` environment.
2. **Stop swallowing the merge's return code.** A merge that could not run
   is not a merge that dropped everything, and today those are the same
   answer. Distinguish them and report the first as `error` with git's own
   message, so the next environment difference produces a complaint rather
   than a confident wrong finding.

Both belong to [checks-plant-their-state](../practices/checks-plant-their-state.md),
whose Story cites this as its second instance — with the git-version reading
that this section corrects.
