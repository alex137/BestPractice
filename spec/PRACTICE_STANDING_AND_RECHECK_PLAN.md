---
title:         "Practice Standing and Recheck: The Plan"
kind:          proposal
status:        drafted
opened:        2026-10-05
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Two ideas of Morgan's, worked through with a second session's critique and adopted on 2026-10-05: every practice carries a standing (Protocol, Principle or Preference) that says how binding it is and who may set it, and practices that may have stopped mattering get rechecked instead of staying in force by default. Part 1 fixes three things found on the way; Part 2 builds the standing field, promotion and the recheck."
---
# Practice Standing and Recheck: The Plan

**Part 1 is built (2026-10-05); of Part 2, step 5's engine half is built (2026-10-05) and steps 6 to 8 are not.** This file is the
plan adopted in the session "Practice categorization and lifecycle"
(2026-10-05), after a second session critiqued it over several rounds. It
records what was decided, how strongly, and why the first draft changed.

## The two ideas

1. **Every practice says what kind of rule it is.** A **Protocol** is a
   rule that must be followed; a **Principle** is a standing philosophy
   applied with judgment; a **Preference** is someone's way of doing
   things, followed by default and set aside when a session says why.
2. **Practices get rechecked, not expired.** A rule that stopped mattering
   stays in force in name only unless something asks whether it is still
   needed. Different rules age at different speeds, and a
   [very deep check](../practices/very-deep-check.md) reading everything at
   once is the weakest place to notice it
   ([ATTENTION_CEILING.md](ATTENTION_CEILING.md): a one-pass whole-catalogue
   judge scored 54% recall).

## Decisions

| Decision | Strength |
|---|---|
| Three standings: Protocol, Principle, Preference | decided |
| The field is `standing:`; absent means Protocol | decided |
| Preferences are kept even though few exist today | decided |
| A preference that keeps being restated is suggested for promotion to Protocol | decided |
| A Protocol that keeps getting in the way is suggested for relaxing to Preference; a safety rule never is | decided |
| Rechecks run during Update Vendors and during a very deep check | decided |
| Every warning-only check is marked temporary or permanent | decided |
| Morgan and Alex approve Protocols and Principles in the universal set | decided |
| Approving a list of items a session proposed is `assented` for each item | decided |
| The routing audit is shown whenever a practice file is edited | assented |
| Recheck lines: at most 3, only in the reply that says the session can be archived | assented |
| GitHub-enforced approval (CODEOWNERS) waits until there is a team with its own accounts | assented |
| The approver field is `standing_by:`, separate from `approved_by` | assented |
| Constants: 3 restatements, 6 months unused, 12 months quiet after "keep" | assented |
| A format rule never stops an old practice or record; it warns and the tooling tidies (reverses the hard field-order check) | decided |

## How the first draft changed

The first draft labelled every practice with a three-way `nature:` field
and rechecked each on a calendar. A second session attacked it and most of
the calendar half fell:

- **A calendar recheck would not run.** At three to twelve months across
  some 150 rules, about 25 rechecks a month come due with nobody assigned.
  The rotating routing audit already proved this: its state file was
  seeded on 2026-09-04 and never touched again, because the only route to
  it was editing its own files.
- **Evidence about private work cannot live in this public repo**, so a
  per-practice log here was never possible.
- **A start-of-session line** would have raised an item no todo marked
  `ask`, against [open-item-disposition](../practices/open-item-disposition.md).

The labels came back after Morgan's own argument, which changed the
author's mind: *"It's okay if a Preference is weaker and can be violated,
that is the point!"* A preference he keeps restating "should not be a
preference but a protocol so it can be enforced", and he may not have
made it one yet only because he hadn't thought to. He added authority:
in a team, the boss sets Protocols and employees cannot, though they still
have preferences. That turned the labels from a description of how a rule
is applied into a statement of **how binding it is and on whose
authority** -- which answered the second session's objection that the
three-way split mixed two questions.

A trial sort of 40 practices found the distinction real but lopsided:
about two thirds Protocols, a handful of Principles, one clear Preference
(most of Morgan's tastes were already written as enforced rules). Hence
**Protocol is the default** and only the exceptions carry a label.

## Part 1: fixes that stand on their own

One branch, landed first.

1. **This plan, committed.**
2. **"Drop it" is recorded reliably.** Today a session writes a park by
   hand, and the practice text named only the body line while the tools
   read only the frontmatter `disposition:` field. Nothing checked that the
   two agreed, and two parked items recorded nobody's name, one no date
   either.
   - [tools/todo_disposition.py](../tools/todo_disposition.py) `park SLUG
     --by NAME` writes both copies in one go.
   - A check reports a per-item todo whose two copies disagree, the
     frontmatter being the copy that counts; hardest when the body says
     parked and the frontmatter still says `ask`.
   - The unattributed items are stamped `who not recorded`, never a guessed
     name ([no-invented-specifics](../practices/no-invented-specifics.md)).
   - **A park that conflicts with a practice** is carried out first, then
     the conflict is raised once -- should the practice change, or is this
     a one-off? -- and recorded as asked, so the question never repeats.
3. **A warning-only check says whether it is temporary.** The field-order
   check was made warning-only on 2026-09-26 "until the practice sets have
   taken the engine update", a condition written only as prose, with no
   date and no owner; and nothing in any update ever ran the tidy it was
   waiting for, so it could not come true. Fix:
   - Every warning-only check declares **permanent** (it flags a judgment
     only a person can make) or **temporary** (it should stop work one day,
     but switching that on now would break what nobody can fix yet).
   - A temporary one records what it waits for, who does it, and a date to
     look again. Past that date it says so, and someone switches it on,
     moves the date with a reason, or makes it permanent. It never switches
     itself, the same design as a practice's `expires:` field.
   - The machine-wide pre-commit hook puts staged practice files in field
     order, before the person's own header fixer runs, only in a repository
     that declares itself a practice source, only on a file whose working
     copy equals what is staged, and never on a file carrying a field the
     local tool does not know.
   - The private sets are tidied once, and the field-order check becomes a
     hard check. **Reversed the same evening:** a project repo had to stop
     and reorder its own practices before it could push, and Morgan ruled
     that old practices are tidied, never stopped. The check is a permanent
     warning, Update Vendors tidies a repo's own practice files, and the
     rule is [format-rules-grandfather](../practices/format-rules-grandfather.md).
4. **The routing audit's blind spot is closed in the existing check.**
   `layered-practice-packs` counts a practice as reachable when an
   `applies_to` glob can fire. The routing audit's globs named only its own
   tool and state file, so only a session already running it was told to
   run it. A route that fires only on the practice's own files no longer
   counts.

## Part 2: standing, promotion and recheck

A second branch, built after Part 1.

5. **`standing: protocol | principle | preference`**, absent meaning
   Protocol. Protocols and Principles are set only by someone with
   authority -- Morgan or Alex in the universal set, a set's owner
   elsewhere. A Preference can be anyone's, and a session that sets one
   aside says why. `approved_by` gains a structured approver a check can
   read. A session never sets Protocol or Principle on its own say-so: an
   approval counts only as the person's own message in that session, never
   a summary relayed from another.

   **Built 2026-10-05, engine half only:** the two fields are in
   [spec/PRACTICE_FORMAT.md](PRACTICE_FORMAT.md) as `standing:` and
   `standing_by:` (the structured approver, named for what it attests),
   [tools/practice_standing.py](../tools/practice_standing.py) holds the
   words and reads authority from the registry
   [tools/precedent_audience.py](../tools/precedent_audience.py) already
   reads for code owners, the `practice-standing` check enforces it, every
   channel that shows a practice marks a Principle or a Preference, and
   [practice-standing](../practices/practice-standing.md) carries the rule.
   No practice carries either field yet: step 9 comes first.
6. **Labelling.** A session drafts every label, Protocol unless shown
   otherwise. Morgan reviews only the doubtful ones (about 15) and a random
   spot check of about 10 others, widened if it finds mistakes. Individual
   rulings are `decided`; the rest, approved as a batch, `assented`.
7. **Up and down.** A restated preference is noted in the person's own
   private set (a date and a session link, never their words); after a few,
   a session suggests a Protocol and drafts it. A Protocol that keeps
   needing exceptions is suggested for relaxing to Preference -- never a
   safety rule. Both are suggestions; Morgan or Alex decide.
8. **Recheck.** During Update Vendors and a very deep check, the consuming
   repository's own history picks practices with no sign of use there for
   months. Each is asked: does what it guards against still exist, when did
   it last matter, what breaks without it, whose call is it, and is
   enforcing it still worth it? Outcomes: keep, narrow, merge, demote, relax
   to Preference, or retire -- **never applied automatically**. At most
   three lines, in the reply that says the session can be archived, carried
   until answered. "Keep" quiets a practice for a registered period;
   "Drop it" stops rechecks in that repository until un-parked. Evidence
   stays in the private repository it came from.
9. **Order.** The engine reaches `main`, every consumer, and each private
   set's own `tools/` copy before any practice carries `standing:`, so an
   older copy never meets a field it does not know.

## Not doing

Calendar recheck dates; a new line at every session start; removing or
relaxing a rule automatically; CODEOWNERS enforcement for now; a general
scanner for "temporary" wording (marking each warning-only check covers it).

## Constants

Set 2026-10-05, Morgan (strength: assented -- *"use your picks for the
numbers"*, a session's three proposals accepted as one): **3**
restatements before a Preference is suggested for Protocol, **6** months
without use before a practice is a recheck candidate, and **12** months
that a "keep" quiets it. They live in `CONSTANTS` in
[tools/practice_standing.py](../tools/practice_standing.py) and nowhere
else, as inputs to revisit under
[constants-are-risk-inputs](../practices/constants-are-risk-inputs.md),
not settled values.
