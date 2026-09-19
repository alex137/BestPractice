---
slug:            gotcha-2026-09-19-parallel-bash-calls-across-repo-directories-can-silently-drop-a-write
status:          live
noted:           2026-09-19
severity:        blocking
retired:         null
retires_when:    null
---
## Symptom

A batch of Bash tool calls issued together in one message, each `cd`-ing into a different repository checkout and running the same read-then-write sequence, reports success for every call individually — but a later `git status` in one of those checkouts comes back clean, as if the write step never ran, with no error anywhere in the transcript.

## Story

During an "Update Vendors" pass across four independent repo checkouts on
disk (no shared state between them), a session batched the per-repo refresh
step as three parallel Bash calls in one message, each `cd <repo> &&
python3 tools/precedent_vendor_engine.py refresh ... --force`. Every call
returned success with the expected output for its own repo. Several steps
later, after switching one of those repos onto a fresh branch, its working
tree was unexpectedly clean — the refresh's file changes had vanished
without ever being committed. This was only caught because the session
re-verified each repo's actual `git status` and history directly before
committing, rather than trusting the earlier calls' reported output. A
second, worse instance hit a different repo in the same batch: its refresh
and commit landed and were pushed and merged into `main`, but a
`build_views.py` regeneration step that should have updated `MAP.md` in the
same commit was silently lost before the commit was made — so a stale
`MAP.md` shipped to `main` and sat there, passing review, until the session
ran `build_views.py --check` against the merged `main` afterward, as an
unrelated final check, and caught the drift. It was fixed in a same-day
follow-up commit and pull request. No root cause was confirmed: the working
hypothesis is that several Bash tool calls run "in parallel" in one message
do not guarantee each one's `cd <dir> && <command>` executes against a
fully isolated shell and working-tree snapshot — something, possibly a race
in a shared underlying shell process, possibly an interleaving between
concurrent calls' file writes, let one directory's in-progress changes get
lost or clobbered by another's. This was not root-caused further because
deliberately reproducing it against real repositories risked doing more
damage than the answer was worth.

## Fix

Do not trust "success" output from a batch of parallel Bash tool calls that
write files across multiple directories. Before committing or pushing any
of them, re-verify each directory's actual state from a fresh, sequential
command (`git status`, `git diff <ref> --stat`, or the tool's own `--check`
mode) — apply this even to steps that look read-only or "obviously fine"
from their own printed output, per
[the verify-postcondition practice](../practices/verify-postcondition.md).
Until this is root-caused, prefer running write/build steps across multiple repos
sequentially rather than batched in parallel — the wall-clock time saved
was small next to the cost of one bad push that had to be caught after the
fact and fixed in a follow-up PR.
