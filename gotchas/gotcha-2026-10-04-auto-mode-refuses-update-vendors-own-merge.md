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

**A second consumer, the same day, saw it spread.** After the merge was
refused, auto mode went on refusing in that repository: plain reads
(`git rev-parse`, `precedent_show.py the-boildown`) and then the first
command of the next turn, until the person named the stage ("Book"). So a
refusal can leave the session unable to look, not only unable to merge.
That is the classifier's own state, not anything the repository set, and
the in-session fix below is the same: say what stopped, and ask for the
step in words that name it.

**2026-10-07, a consumer, measured in order.** The person said
"Update Vendors"; the update ran to DONE and opened its pull request into
pre-staging.

1. The merge of that pull request: refused, `[Merge Without Review]`.
2. `git rev-parse HEAD`, a read: refused.
3. The person said "promote". The session's first command,
   `python3 tools/precedent_show.py promote` -- reading the practice's text,
   nothing more -- was refused.
4. The person said "promote" again. The same merge call went through.

The runbook's advice, to ask for the merge by name ("Merge PR #N into
<branch>"), was not needed that time: a second plain "promote" cleared it.
That is one observation of a classifier whose state nobody here can read,
not a rule to rely on. What it does confirm is the second consumer's: a
refused merge can leave the next turn unable even to read.

**2026-10-08, a third consumer.** The same order again: the merge refused
as `[Merge Without Review]`, then `git rev-parse HEAD` and a token count
refused under the same reason, until the person spoke. Three repositories
now, so it is the classifier's ordinary behaviour, not a fluke: after a
refused merge, anything the session runs before the person's next message
is likely refused too, and only spends the turn.

**2026-10-08, a consumer: a merge that fails starts it too.** This
time auto mode let the merge call through, and GitHub refused it: the
session had passed a 7-character expected head SHA, and the merge tool
takes all 40 characters or none. After that failed call the same refusals
followed, reads included. So the spiral does not need the classifier to
refuse the merge first; a merge that fails for any reason can set it off.
Since that day the update's DONE says to merge with the full 40-character
head (`git rev-parse HEAD` right after the push) or none, every merge line
Promote prints carries the head in full, and
[vendor-update-runbook](../practices/vendor-update-runbook.md) step 12 says
the same.

It is the merge-shaped twin of
[the refusal of a bare Promote into main](gotcha-2026-09-30-auto-mode-refuses-a-bare-promote-into-main-as-a-production.md),
and the same fix applies.

## Fix

**In the session:** stop at once, run nothing else, and end the turn
asking for the merge by name: one line that Claude Code's own safety check
stopped it, not the repository's rules, and the words that name it, "Merge
PR #N into <landing branch>". A check, a read or a count run first is
refused under the same reason and only delays the ask. Never route around
it: no other merge route, no handoff to another session, no settings edit
of the session's own.

**The durable fix is the person's**: an `autoMode.allow` entry in managed
settings or `~/.claude/settings.json`, as the gotcha above describes, with
`"$defaults"` kept in the list.
