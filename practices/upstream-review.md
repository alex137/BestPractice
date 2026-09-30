---
slug:        upstream-review
title:       "After an update or a stage lands, review what it ran into and hand the fixable part upstream"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "An OPERATION finishing -- Update Vendors, a migration or an upgrade, and the Booked, Debut and Produce stages -- touches any file, so no path narrows it. Routed by the `merge` gate, the moment each of them ends in, and by the review block the tools print themselves. Decided: 2026-09-30, when the practice landed."
occasion:    "Update Vendors, a migration or an upgrade finishes, or a Booked, Debut or Produce lands"
gates:       ["merge"]
gates_why:   "Each of the five operations ends in a merge into a branch tier -- Update Vendors carries its own Booked -- so the merge gate is where the review is due."
index_clause: "after an update or a stage lands, hand its fixable warnings upstream"
checked_by:  null
defines:     ["Upstream review", "Upstream-seen"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-30"
approved_by: "Morgan, 2026-09-30 -- asked for it (\"What if every time an update vendors or migration update or upgrade finishes, explicitly review the warnings, errors, bugs you found, whether you fix them or not ... and you write a prompt for it\"), chose the record's shape (\"I like the ledger idea, I'm sold. Let's do it with C. Act\"), and set the audience (\"those users should never see this nor ANY of these sorts of 'mechanics' issue\")"
strength:    decided
---
## Rule
**When Update Vendors, a migration or an upgrade finishes, and when a
Booked, Debut or Produce lands, review everything that step ran into** --
every warning, error, bug, note, new exemption, kept local edit and
workaround, **whether it was fixed or not** -- and ask of each: **could it be
fixed upstream**, in BestPractice or a precedent-* set, so nobody meets it
again?

**Only what is within reasonable reach counts.** An item is a candidate when
both hold: **the cause lives somewhere we own or pin** (BestPractice, a
practice set, the repo's own templates, a version we choose), and **the fix
is a bounded change** a session could make without a design call from the
person. A third-party library's deprecation, a GitHub platform notice, a
network or proxy blip, a container limit or a lost runner is not one: say so
in one line and move on. **A warning our own tool prints every time with
nothing for anyone to do is a candidate**: the fix is to stop it printing.

**Hand each candidate off, one [Prompt Please](prompt-please.md) block per
upstream repository**, not one per warning, after checking that no live
session is already on it. That holds even where
[upstream-fix](upstream-fix.md) would have this session fix the root itself:
a session finishing an update or a Promote does not widen its own scope.
The reply carries it as a short **Upstream review** section before
[The Boildown](the-boildown.md) -- one line when there is nothing ("Reviewed
N items, nothing worth fixing upstream") -- and Boildown item 1 points at the
blocks.

**Each stage reviews only what is new since the stage before**, and the
record is the commits themselves, never a list. A stage writes one
`Upstream-seen: <fingerprint> <line>` line per item it reviewed into the
commit it lands; the next stage reads those lines from exactly the batch it
moves and skips them. [tools/precedent_upstream_review.py](../tools/precedent_upstream_review.py)
does the mechanical half:

- **Update Vendors** prints the review at DONE, with the lines to put at the
  end of the update's commit message.
- **Booked**: `python3 tools/precedent_upstream_review.py --stage booked
  --note "what you met" [--from CHECK-OUTPUT]` prints the same, for the
  commit or pull-request merge that lands the work.
- **Debut** and **Produce**: Promote prints the review itself, from its full
  check, less what the batch already records. Debut writes the new lines
  into its own merge commit; Produce is the last stage and records nothing.

**A content-only reader never sees any of it.** The review still runs and
its lines still go into the commit, so the next technical person's stage
raises what it found; the reply to a content-only reader says nothing about
it. Until a person can declare this directly, treat as content-only a
reader whose declared register is non-technical, or who has declared none
(the `default-register` fallback).

## Why
[upstream-fix](upstream-fix.md) and Boildown item 4 ask about a fix somebody
made. The warnings nobody acted on -- passed over, exempted, worked around
locally -- had no moment where anyone asked whether they could be fixed at
the source, and an update or a Promote is exactly where they pile up. The
record rides the commits so that three stages, often run from three sessions
on three days, raise each item once, and so that nothing grows beyond the
git history that is kept anyway.

**No check enforces it, and that is considered, not skipped.** What a check
could see -- whether a reply carried an Upstream review section -- is the
part that does not matter; whether each item was judged fairly is judgment.
The mechanical half is a tool instead: the review block is printed by the
very commands the step runs, so it is in front of the session at the moment
it is due, which a check reading the reply afterwards could not do.

## Story
Morgan, 2026-09-30, in a planning session: updates, migrations and
promotions keep surfacing minor bugs and warnings that get fixed locally,
exempted or ignored, and he wanted each one treated as an opportunity to fix
it upstream -- after an update, and at each of the three landings, only for
what is new since the one before. Three places for the record were weighed:
a committed file (grows, and would need commits mid-Promote), a side branch
(no growth, more machinery), and lines on the commits themselves. He chose
the commits. Keeping a list of outside warnings judged "not ours" was
dropped on purpose: re-judging one costs a line, and a list of dismissals
would grow forever and hide a warning that later becomes fixable.
