---
slug:            gotcha-2026-09-19-verify-harnesss-fresh-container-check-can-fail-tempdir
status:          live
noted:           2026-09-19
severity:        null
retired:         null
retires_when:    null
---
## Symptom

`python3` [`tools/verify_harness.py`](../tools/verify_harness.py) crashes with an
uncaught `OSError: [Errno 39] Directory not empty` from inside Python's own
`tempfile.TemporaryDirectory.__exit__`, rather than printing a `FAIL` line —
the whole run dies mid-suite instead of reporting the one check that owns
the failing directory.

## Story

`check_leak_gate_refuses_a_fresh_container` builds and tears down three
throwaway git repos, one per `with tempfile.TemporaryDirectory() as tmp:`
block, to prove the leak gate still requires a blocklist in a container that
has never seen this machine's config. On GitHub's hosted runner, one of
those three cleanups threw `OSError: [Errno 39] Directory not empty:
'/tmp/tmpzlr973qo/r'` on exit from the `with` block, which Python does not
catch — it propagated straight out of `main()` and took the whole 172-check
run down with it, on [PR #457](https://github.com/alex137/BestPractice/pull/457),
a change that touched only [practices/the-boildown.md](../practices/the-boildown.md)
and nothing this check exercises.

Nothing in the check itself keeps a handle open in that directory — every
git call is a synchronous `subprocess.run` that has already returned by the
time cleanup runs — and the identical check passed clean on the identical
commit, both in a local run before the push and in a same-branch re-run of
the same CI job a few minutes later. That combination (fails once,
passes on immediate retry with no code change) is what makes this read as a
transient filesystem race on the runner rather than a real resource leak.
**The actual mechanism was not measured** — it was not reproduced under
`lsof`/`fuser` at the moment of failure — so treat "something transiently
held the directory open" as a hypothesis, not a diagnosis. One plausible
candidate, also unmeasured: newer git can auto-start a per-repo background
filesystem-monitor daemon that outlives the `git` subprocess that spawned
it and keeps a socket file open under `.git/` until stopped.

**The fix is `_rmtree_retrying()`** ([tools/verify_harness.py](../tools/verify_harness.py), next to `check()`):
retry the delete a few times with a short pause before giving up, and if it
is still not empty after those retries, raise anyway with the directory's
remaining contents attached as evidence — a real, persistent leak still
fails loudly, it just fails with something to root-cause instead of a bare
`ENOTEMPTY`. `check_leak_gate_refuses_a_fresh_container`'s three
`tempfile.TemporaryDirectory()` blocks (and its `_fixture_home` one) were
the only ones converted to it — the one check that has actually hit this,
not a blanket rewrite of the file's other 130+ temp-directory uses, which
have not shown the symptom. `ignore_cleanup_errors=True` was considered and
rejected: it would have made this indistinguishable from a real leak by
silently discarding both.

If this recurs on a *different* check, that is itself new evidence — it
would argue for moving `_rmtree_retrying` into a shared context manager
other checks opt into, rather than converting each site one at a time as it
happens to fail.

## Resolution (2026-09-19, a Different Session, Same Day)

**The "unmeasured hypothesis" above almost certainly named the wrong
mechanism.** A separate session fixing
[gotcha-2026-09-18-verify-harnesss-stress-checks-can-oom-kill-the-bash-tools.md](gotcha-2026-09-18-verify-harnesss-stress-checks-can-oom-kill-the-bash-tools.md)
found that `check_leak_gate_refuses_a_fresh_container` — the exact check
this file is about — was fanning out into an unbounded recursive chain of
[precedent_session_practices.py](../tools/precedent_session_practices.py)
subprocesses, all writing inside the same kind of fixture tree this check
tears down, and measured that check dropping from 241.8s to 1.72s once the
recursion was fixed (an env-var reentrancy guard in
[precedent_resolve.py](../tools/precedent_resolve.py)'s
`_self_heal_stale_render()`).
241.8s is within a second of the 243.3s this check took in the very run
that hit the `ENOTEMPTY` documented above — the "transient filesystem race"
was almost certainly hundreds of concurrent orphaned subprocesses
contending for the same directory tree, not a git filesystem-monitor daemon.

**`_rmtree_retrying()` stays** — it is still correct general hardening
(retry over crash, evidence over silence) independent of which mechanism
caused the one directory it has actually seen fail to be transiently
non-empty. But the specific hypothesis in the Story above is superseded by
this dated, measured finding, not merely unconfirmed.
