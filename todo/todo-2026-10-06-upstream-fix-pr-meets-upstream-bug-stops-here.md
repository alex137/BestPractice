---
slug:              todo-2026-10-06-upstream-fix-pr-meets-upstream-bug-stops-here
kind:              manual
domain:            practice
severity:          null
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          "S. Alexander Jacobson, 2026-10-06: \"Yes. Opening a pr counts as asking.\""
decision_strength: decided
waiting_on:        null
noted:             2026-10-06
closed:            2026-10-06
---
## What

Two practices in force now read differently on the same moment.
[todo-is-a-handoff](../practices/todo-is-a-handoff.md) (Alex, 2026-10-06,
decided) says a fix that belongs in another repository is opened as a pull
request there in the same turn, access requested if needed.
[upstream-bug-stops-here](../practices/upstream-bug-stops-here.md) (Morgan,
2026-09-28, decided) says a session that could fix the upstream repository
itself still stops and asks, handing back a Prompt Please block, because the
person wants to see an upstream bug before anyone patches anything.

The change that added the first wording reads them together this way: the
local copy is never patched, and the pull request upstream is where the
person sees the fix before it lands. That reading is in todo-is-a-handoff's
Install section, but upstream-bug-stops-here's paragraph "It holds even
where the session could fix the upstream repository itself" still says to
stop first. One of the two should say how it relates to the other.

My pick: amend upstream-bug-stops-here so "stop and ask" covers the local
edit and the landing, and opening the upstream pull request in the same turn
counts as showing the person; the pull request is reviewed before it lands.

## Notes

2026-10-06: closed. Decided as the pick above: upstream-bug-stops-here now says the local copy is never patched, the fix opens upstream as a pull request in the same turn, and that pull request is the ask; a Prompt Please remains for an owner that cannot be reached.
