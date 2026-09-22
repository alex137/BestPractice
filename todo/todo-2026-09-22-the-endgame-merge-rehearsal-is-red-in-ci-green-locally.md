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

## Next step

Reproduce it against the runner's git version rather than the container's,
then fix the check or the rehearsal — whichever turns out to be wrong. The
check asserts a real distinction (a file touched since the merge base is a
conflict, not a silent drop), so it is worth keeping.
