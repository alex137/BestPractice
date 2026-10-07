---
slug:              todo-2026-10-06-upstream-fix-pr-meets-upstream-bug-stops-here
kind:              manual
domain:            practice
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "a decision by Morgan (owner of upstream-bug-stops-here) and Alex (who approved the todo-is-a-handoff change) on which of the two wordings governs"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-06
closed:            null
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
