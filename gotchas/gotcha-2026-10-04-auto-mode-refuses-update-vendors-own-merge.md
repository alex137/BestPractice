---
slug:            gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge
status:          live
noted:           2026-10-04
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

"Update Vendors" runs to DONE, opens its pull request, and the merge that
the phrase carries comes back `Denied by auto mode classifier` with the
reason `[Merge Without Review]`. Nothing in the repository refused it, and
the same merge goes through once the person's message names it.

## Story

**2026-10-04, a consumer.**
[vendor-update-runbook](../practices/vendor-update-runbook.md) says the
phrase carries the merge, so the session merged its own pull request into
the landing branch. Claude Code's auto mode refused it: a soft block clears
only when the person's own message "directly and specifically describes
the exact action", and "Update Vendors" names an update, not a merge. After
the person said "Promote", the same merge went through.

It is the merge-shaped twin of
[the refusal of a bare Promote into main](gotcha-2026-09-30-auto-mode-refuses-a-bare-promote-into-main-as-a-production.md),
and the same fix applies.

## Fix

**In the session:** say in one line that Claude Code's own safety check
stopped the merge, not the repository's rules, and ask the person for it in
words that name it: "Merge PR #N into <landing branch>". Never route around
it: no other merge route, no handoff to another session, no settings edit
of the session's own.

**The durable fix is the person's**: an `autoMode.allow` entry in managed
settings or `~/.claude/settings.json`, as the gotcha above describes, with
`"$defaults"` kept in the list.
