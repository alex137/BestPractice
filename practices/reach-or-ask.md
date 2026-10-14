---
slug:        reach-or-ask
title:       When something needed is out of reach, get access or ask for it -- never just report it
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus: the moment is a tool or check answering that it could not reach a repository, host or credential, in any repository and about any file. The occasion index is the channel. Decided: 2026-10-08, when the practice was written."
occasion:    "a tool, check or task cannot reach a repository, service, credential or file it needs"
gates:       []
index_clause: "take read access a tool can grant; ask for anything wider; never just report it"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-08"
approved_by: "Alex, 2026-10-08: \"Why not adopt a practice of asking if you need access rather than simply passively announcing you can't\" (strength: decided); amended 2026-10-14, Morgan -- ask for push access by name before trying, and stop at a safety-check refusal -- from a handoff he confirmed as his (\"you said that you're stopped from doing something that shouldn't be stopped. So include this issue and your suggested fixes\"; strength: assented)"
---
## Rule
**A reply never stops at "could not reach it."** When a check, a tool or
the task itself cannot reach something it needs -- a repository not
attached to the session, a host the network denies, a missing credential
or connector -- do one of these in the same turn:

1. **Read access a tool in this session can grant** (attaching a
   repository read-only, for one): take it, carry on, and say in one line
   that you did.
2. **Anything wider** -- push access, a new connector, a credential, a
   setting only the person can change: **ask**, naming what you need, why,
   and the one step they take. **Ask before trying, in words that name
   it**: *"Reply 'attach BestPractice with push access' and I'll do the
   root fix there."* The person's own words then carry the grant, and
   Claude Code's auto mode clears it; a push attach tried first is refused
   as a permission grant nobody asked for.
3. **Not needed for the task:** say so plainly, and still offer to get it.

**When the safety check refuses a call, stop there.** Run nothing else in
that batch and do not retry it, alone or reworded. Three refusals in a row
pause auto mode and put a dialog on the person's phone, whatever the third
call was. Ask the person in one line, naming the exact action and the words
that would clear it, and keep working on whatever does not depend on it.

"Not verified", "unknown this session" and "could not reach" are findings
to act on, never a final answer.

## Why
A bare report leaves the person to notice that the gap is fixable and to
ask for the fix, a round trip that decides nothing. Most gaps are one
attach or one setting away, and the session usually knows which.

## Story
2026-10-08, a consuming repository: a merge reported that one of its
declared shared sets was "NOT VERIFIED -- could not reach" its upstream,
and the session passed that on as a closing note. The set had simply never
been attached to the session; a read-only attach, available all along,
answered the question in seconds (the copy was current). The person:
"Why not adopt a practice of asking if you need access rather than simply
passively announcing you can't."

2026-10-14, a consuming repository's Update Vendors: asked for a root fix
upstream, the session attached BestPractice with push access unasked, and
in the same batch ran a read-only `precedent_show.py`. Auto mode refused
the attach as a permission grant, took the read down with it, refused the
read again when it was retried alone, and the third refusal in a row put an
"Allow once / Always allow / Deny" dialog on the person's phone for a read
([gotcha-2026-10-14](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-10-14-auto-mode-refusal-cascades-into-a-phone-dialog-over-a-read.md)).

## Install
Nothing to install, and no mechanical check: whether a gap was one a tool
could close, or needed the person, is the judgment itself. The occasion
index carries the trigger, so the line reaches every repository with its
next catalogue refresh.
