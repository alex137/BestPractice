---
slug:            gotcha-2026-10-01-a-wait-loop-on-pgrep-f-waits-on-itself
status:          live
noted:           2026-10-01
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A shell loop meant to wait until a long command finishes,
`while pgrep -f "tools/precedent_push_check.py"; do sleep 10; done`, never
ends. The command it waits on finished long ago, and the loop runs until
its own time limit kills it.

## Story

**2026-10-01, in this repository.** A session started the push check in
the background, then started a second background command to wait for it
and print the result. The check finished after 11 minutes. The waiter ran
on for another 20, until the harness stopped it at its time limit, and
Morgan asked why a pre-staging check was taking 29 minutes.

`pgrep -f` matches against each process's whole command line, and the
waiter's own command line contained the text it was searching for. So
`pgrep` always found one match, the loop itself, whether or not the check
was still running. The same session had already killed its own shell once
the same way, with `pkill -f` on the same pattern.

## Fix

**Don't write a wait loop.** Run the long command itself in the background:
the harness says when it finishes, and its output file holds the result.
Nothing needs to poll.

**If a wait is truly needed, wait on the process, not on its name**: keep
its process ID (PID), `cmd & pid=$!`, and use `wait "$pid"` in the same shell, or
`tail --pid="$pid" -f /dev/null` from another. Never `pgrep -f` or
`pkill -f` with a pattern that also appears in the command running them.
