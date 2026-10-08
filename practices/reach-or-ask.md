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
approved_by: "Alex, 2026-10-08: \"Why not adopt a practice of asking if you need access rather than simply passively announcing you can't\" (strength: decided)"
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
   and the one step they take.
3. **Not needed for the task:** say so plainly, and still offer to get it.

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
