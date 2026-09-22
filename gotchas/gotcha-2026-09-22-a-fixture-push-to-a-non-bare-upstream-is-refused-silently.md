---
slug:            gotcha-2026-09-22-a-fixture-push-to-a-non-bare-upstream-is-refused-silently
status:          live
noted:           2026-09-22
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A test fixture builds an upstream with `git init`, clones it, commits in the
clone and pushes — and the push is refused every single time, on every
machine, with nothing reporting it. The fixture then asserts against a state
it never reached.

## Story

`git init` makes a repository **with a working tree**, and git refuses a push
to the branch such a repository currently has checked out — *"failed to push
some refs"*. Only a **bare** repository accepts that push by default.

Two fixtures in [tools/verify_harness.py](../tools/verify_harness.py) did
exactly this: `git init -b main` for the upstream, clone, commit, then
`git push origin main`. The push had never once succeeded. Nobody knew,
because the fixture helper returned the `CompletedProcess` and every caller
threw it away. Both checks passed anyway — they happened to assert things
that were true regardless — so the broken setup sat there green.

It surfaced on 2026-09-22 only because the fixture helper was changed to
raise on a non-zero exit. Two checks immediately reported
`fixture setup failed -- git push -q origin main ... exited 1`, which is the
entire value of that change: a setup that cannot work now says so, in the
words of the command that failed, instead of being absorbed.

**The same hazard is latent wherever this pattern appears.** Eleven fixtures
in that file build an upstream this way; only two pushed to it, but any of
the other nine would hit it the moment somebody added a push.

## Fix

**Give the fixture's upstream `receive.denyCurrentBranch=ignore` right after
`git init`**, which is what all eleven now do:

    _git(up, 'init', '-q', '-b', 'main')
    _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')

`ignore` leaves the upstream's own working tree stale, which is correct here —
these fixtures read refs afterwards, never files. Use `updateInstead` if the
fixture does need the upstream's working tree to move. A genuinely bare
upstream (`git init --bare`) is the other right answer, and is better when the
fixture never needs to commit *in* the upstream.

**The general rule this is an instance of:** a fixture's setup commands must
fail loudly. The underlying cause was not git's push rule — it was that
nothing looked at the exit code. See
[practices/fixture-owns-its-state.md](../practices/fixture-owns-its-state.md).
