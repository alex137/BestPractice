---
slug:            gotcha-2026-09-28-a-wait-loop-on-pgrep-f-finds-itself-and-never-ends
status:          live
noted:           2026-09-28
severity:        minor
retired:         null
retires_when:    null
---
## Symptom

A shell loop written to wait for a script to finish never ends, though the
script finished long ago:
`until ! pgrep -f scratchpad/x/runcases.py >/dev/null; do sleep 5; done`.
It sits in the process list, waking every five seconds, for as long as the
container lives.

## Story

On 2026-09-28 a fix agent in a very deep check started two such loops to
wait for its own test script, then finished its work and reported back.
Both loops ran for five more hours. `pgrep -f` matches its pattern against
every process's full command line, and the loop's own shell command line
contains the same text as the pattern, so the search always finds at least
the loop itself, and the exit condition never comes true. Nothing reported
it. The container check said the container was clean, because it looked
only at git checkouts; Morgan asked why two tasks were still running, and
a look at the process list found them.

## Fix

Wait on the process ID, never on a name search: start the script with
`cmd & PID=$!`, then `wait $PID` or `while kill -0 $PID 2>/dev/null; do
sleep 5; done`. Better still, don't write a wait loop: an agent harness
that runs commands in the background already reports when one finishes.
If a name search is unavoidable, the bracket trick keeps it from matching
itself: `pgrep -f '[r]uncases.py'`. And `tools/precedent_container_safe.py`
now lists any shell the session's agent started that is still running, so
a loop like this shows up at the next reply gate instead of five hours
later.
