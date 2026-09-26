---
slug:        dated-list-runs-forward
title:       A dated list runs oldest first, and every entry carries its own date
tier:        on-demand
severity:    default
scope:       any-adopter
applies_to:  ["practices/*.md", "local/practices/*.md", "decisions/*.md"]
occasion:    "a document carries a list of dated entries that will be added to over time"
gates:       []
index_clause: "a dated list runs oldest first; new entries append and carry a real date"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-23"
approved_by: "Morgan F, 2026-09-23 -- he asked how to stop a dated list's
  order getting mixed up again, was shown the choice between a prose note
  and a mechanical check, and said \"please fix\" (strength: decided; the
  mechanism is the session's, the requirement is his)"
strength:    decided
---
## Rule
**A list of dated entries runs oldest first, a new entry is APPENDED at the
bottom, and every entry carries a real date of its own.**

**Never date an entry by pointing at another one** — no *"same day"*, no *"in
the same turn"*, no *"the following week"*. That is a **positional**
reference: it is unreadable on its own, and it silently repoints the moment
anything is inserted, removed or sorted. An entry has to survive being read
by itself and being moved.

**Mark the list so the check can see it**, with the sentinel on its own line
directly above the first entry:

    <!--dated-list-->
    - **2026-09-05, who** — what changed
    - **2026-09-06, who** — what changed next

The mark is opt-in on purpose. Plenty of lists carry dates and are ordered
by something else entirely — severity, topic, the order an argument needs —
and a check that guessed which was which would fire on correct work, which
is worse than no check at all
([checkable-gets-checked](checkable-gets-checked.md)).

**An undated entry is allowed only before the first dated one**, for the
state a list starts in — *"originally: pending review"* — where there is no
date to give. After that, every entry has one.

## Detail
**What the check enforces**, `python3 tools/precedent_check.py --only
dated-list-runs-forward`: inside a marked block, the dates run
non-decreasing, and no entry after the first dated one is missing a date.
It names the offending row and the two dates that are the wrong way round.

**Two entries may share a date.** Same-day order is not recoverable from a
date and the check does not pretend otherwise — it asserts non-decreasing,
never strictly increasing.

**Resolving a relative date later is a recovery, not an invention**
([no-invented-specifics](no-invented-specifics.md)). The date a *"same day"*
entry meant is whatever the entry above it says, and that is readable as
long as nothing has moved yet. Where it genuinely is not — the antecedent is
itself relative, or the entry's own text carries a different date — the
resolved date is marked as a read and the ambiguity is said in place. **Do
not sort a list that still holds relative entries.** Date them first, in
their own change; sorting them together destroys the evidence the dating
depends on.

## Why
Append order and date order agree right up until somebody adds an entry at
the top because that is where the cursor was. Nothing objects, so both
orders are now live in one list and every later entry picks whichever end it
lands nearest.

## Story
**BestPractice's own `very-deep-check` approval history, 2026-09-22/23.**
Moved out of an `approved_by:` frontmatter field that had reached 2,024
words, it carried the field's order with it — and that order ran in two
directions at once. Recent approvals had been prepended at the top as they
were written; the original chain ran forward from the bottom. A reader met
2026-09-23 first, then 2026-09-22, then seven 2026-09-21 entries, then
2026-09-14, then jumped back to 2026-09-05 and read forward to 2026-09-19.
**The two 2026-09-14 entries sat seventeen rows apart.**

**Sorting it was blocked, and the reason is the rule's other half.** Six
entries dated themselves *"same day"* or *"in the same turn"*, meaning the
entry directly above. Two ADJACENT entries both saying *"same day"* meant
two different days: the first one's text ran on into a clause carrying
2026-09-07 while the change that entry itself recorded happened on
2026-09-06. A first attempt to sort chronologically filed that entry a day
late, silently, in a record of who approved what — and it was caught only
because the run printed its computed dates.

So the repair took two changes, in this order: date every entry from what
the text already meant, marking the one that was a read rather than a
derivation; then sort. Morgan asked, in the same breath, how to stop it
happening again. **A note saying "new entries go at the bottom" was the
obvious answer and the wrong one** — this catalogue had recorded, eleven
days earlier, a rule written as prose that went on instructing sessions
after the practice it copied had changed, because prose is invisible to
every mechanism that would have retired it. The note is still there, and the
check is what makes it true.

## Install
Checked by [`tools/precedent_check.py`](../tools/precedent_check.py), scope
`tree`: it reads every marked block in the files `applies_to` names and
asserts the two properties in Detail. It is deliberately **blind to
unmarked lists** — a dated list nobody marked is not checked, which is the
cost of not firing on lists that are correctly ordered by something other
than date. It is also blind to whether a date is the RIGHT one: nothing
mechanical can read the conversation an entry records, so an entry dated
plausibly and wrongly passes cleanly. Two-direction planted case in
[`tools/verify_harness.py`](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py).
