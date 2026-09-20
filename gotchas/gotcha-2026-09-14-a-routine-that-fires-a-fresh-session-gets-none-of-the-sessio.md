---
slug:            gotcha-2026-09-14-a-routine-that-fires-a-fresh-session-gets-none-of-the-sessio
status:          live
noted:           2026-09-14
severity:        null
retired:         null
retires_when:    null
---
## Symptom

Measured 2026-09-14

## Story

**Measured 2026-09-14**, twice, in opposite directions on the same afternoon.

A scheduled Routine was created to sweep the fleet — list every session, keep
the ones blocked on the person, notify. `create_trigger` returned a warning
about Model Context Protocol (MCP) connectors that reads like boilerplate:
*"this trigger stores no MCP connectors, so the
sessions it fires will run without connector (`mcp__<server>__*`) tools."* The
Routine was fired once as a test. It completed in 32 seconds and exited 0, and
its recorded run status was `SUCCEEDED`. **The run succeeded at doing
nothing**: the fired session reported that `list_sessions` was not available to
it, which is the one tool the whole job rests on.

**Neither the warning nor the run status tells you this.** A Routine whose
session cannot do its work still fires, still finishes, still records success —
the failure is inside the turn, and `last_run` cannot see in there. Left alone
it would have reported quietly for as long as nobody opened a run.

**The remedy the warning names does not apply.** `connectors` resolves against
the person's connected claude.ai connectors — measured on this account: Gmail,
Google Calendar, Google Drive, and nothing else. The session-management server
is the harness's own, not a connector, so there is no name to pass and nothing
for the `connectors` argument to carry.

**What works is a STANDING session.** A session created with `create_session`
*does* get the tools — confirmed by creating one and watching it parse a saved
`list_sessions` result mid-sweep. So the shape is a standing session doing the
work, and a Routine bound to it with `persistent_session_id` waking it on the
schedule.

**That costs the Routine's own notifications**, which the server offers only to
a Routine that starts a fresh session on each firing. The way back is that the
standing session can send one itself: `PushNotification` with
`status: "proactive"` is available inside a session and reaches the person's
phone. So the notification moves from the Routine into the prompt.

**The generalization worth keeping: a scheduled job's capabilities are not the
capabilities of the session that scheduled it.** Test the fired session's
tools, in its opening turn, before building anything on top of it — and read
what the test run actually *said*, never its exit code.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
