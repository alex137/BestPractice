---
slug:        checkable-gets-checked
title:       A new practice gets a mechanical check before it gets left advisory
tier:        on-demand
severity:    default
applies_to:  ["practices/**", "PRACTICES.md"]
occasion:    "writing a new convention or rule"
gates:       ["review"]
index_clause: "attempt a mechanical check before leaving a new practice advisory-only"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "pending review"
---
## Rule
Before a new practice is left `checked_by: null`, actually try to write
the check — don't stop at the first plausible-sounding reason it can't be
done, and don't wire one in without running it against the whole tree
first: a check that fires on legitimate, correct work is worse than no
check, because it teaches the next session to ignore the gate. If a real
check exists and stays clean on the unplanted tree, wire it in with a
firing test, the same discipline every enforced practice already carries.
If it genuinely doesn't, say so in the practice file, with the specific
reason (not "too hard to check"), so the next session can tell a
considered "no" from an unexamined one.

## Detail

## Why
This catalogue's own enforcement channel makes the tradeoff explicit:
`checked_by` is strictly better than prose whenever it's honest, because a
checked practice is never loaded and never competes for a session's
attention at all — the routing/attention-ceiling problem this catalogue's
whole loader architecture exists to manage simply does not apply to it.
Every practice a session has to notice and judge for itself is a practice
that can be missed under load; every practice with a working check is not.
So "no mechanical check exists for this" is a claim with real cost if it's
wrong — not a formality, and not something to accept from a first pass
that stopped at the first plausible no. Two failure modes look identical
from outside: **stopping early** (a first pass finds 3 of 30 convertible
and calls the rest "prose-only," when a second, harder pass finds several
more) and **stopping unsafely** (wiring in a check that fires on correct
work, which defeats the practice's own purpose). Guarding against the
second is why the Rule requires testing against the whole tree before
wiring anything in.

## Story
A session doing an enforcement sweep converted 3 practices, checked the
remaining ~30 against a mental list of "reasoning-quality, no signature,"
and reported the sweep as complete — 21 of 52 enforced, the rest correctly
resistant. Asked to look again rather than accept that verdict, a second
pass found two more that were genuinely convertible
(`two-check-levels`, needing only a naming decision the repo had already
half-made; `index-remembers-past`, needing a narrower design with an
explicit exemption list after its first version false-positived on a
file's legitimate use of the exact phrase it was written to catch). A
third practice thought tractable (`volatile-rules-carry-dates`) was
re-examined and confirmed genuinely unsafe to enforce only after grepping
the repo's own prose and finding a dozen ordinary sentences that would
have false-positived — a considered no, arrived at with evidence, not the
same as the first pass's assumed no for the same practice. The gap between
the first pass's stopping point and the second pass's was real practices,
not a rounding error.

## Install
No check exists for this practice itself, and probably can't: whether a
mechanical check is genuinely impossible for another practice is a
judgment call, the same class the proportionality guard in
`mistakes-become-rules` already names as resistant to automation. It
fires at the `review` gate instead — [tools/precedent_gate.py](tools/precedent_gate.py)
review — so a session reviewing a newly written practice is handed this
Rule at exactly the moment it matters. [spec/ENFORCEMENT.md](spec/ENFORCEMENT.md)'s
"What phase 5 inherits" section already named the shape of this gap
before this practice existed: "the creation pipeline should ask for a
check, not a `checked_by`... a promotion step that accepts a string has
re-created the problem." This practice is that ask, made explicit and
loadable.
