---
slug:        item-closes-on-its-condition
title:       "Work that moves an open item records it there; only its stated condition closes it"
tier:        on-demand
severity:    default
applies_to:  ["TODO.md", "**/TODO.md"]
occasion:    "work touches an open item's subject, or a branch merges"
gates:       ["merge"]
index_required: true
index_clause: "record findings in the item; close only on its condition"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-13"
approved_by: "Morgan, 2026-09-13 -- chose this shape over 'finishing it closes it' from the two laid out"
---
## Rule
When a session does work that bears on an open item — whether or not anyone
framed it that way — **it writes what it established into that item, in the
same turn.** A measurement, a refusal it can quote, a claim it disproved: into
the item, dated.

**Closing is the separate, stricter act.** An item closes only when the session
can **name the item's own stated condition** and say that condition is now met.
Resembling the item is not meeting it.

## Detail
**The two halves fail differently, which is why they are separate.** Not
recording loses a measurement nobody will take again. Closing on a resemblance
loses the item's actual question while looking like progress, and the loss is
silent — a closed item is not re-read.

**The hard part is the noticing, not the closing.** No session reads eighty
open items asking what it might have finished, so the rule leans on
[tools/todo_progress.py](https://github.com/alex137/BestPractice/blob/staging/tools/todo_progress.py)
rather than on attention: `--changed BASE..HEAD` lists items naming a file the
change touched, and stays **silent** when none do. It reports a resemblance and
says so in its own output; the reading is yours.

**An item you cannot close, you can still sharpen.** If the work narrowed the
question, say how, and leave the item open. That is the common outcome and it
is not a failure to close.

## Why
An open item is a question somebody wrote down because it could not be answered
yet. Work that answers part of it, in passing, is the cheapest evidence the
project will ever get about that question — the session holds the context, the
commands, the exact error text — and by the next session all of it is gone. The
queue then keeps asking something that has already been half-answered, and the
next session pays again to learn what this one knew.

Closing is the opposite risk, and a rule that said "finishing the work closes
the item" would cause it. Two things can look identical from outside — an item
asking *"re-test the fresh-session case"* and a session that hit the same
refusal in a different case — and only the item's own words tell them apart.

## Story
**Coined by Morgan, 2026-09-13**, as a question rather than a rule: *"if a
session does something that completes a TODO (even if we never explicitly said
it was to complete it), does it close that corresponding TODO?"*

The honest answer was that **nothing made it happen** — not the catalogue, not
the merge gate, not `TODO.md`'s own header.
[todo-is-a-handoff](todo-is-a-handoff.md) governs writing an item and
[open-item-disposition](open-item-disposition.md) governs raising one; neither
covers completion. An item closed that day only because the session that
finished it had also written it, an hour earlier, and remembered.

**The live case arrived in the same thread and argued against the simple
rule.** Answering an unrelated question about whether a new check had reached
the practice sets, the session called `add_repo` and was refused across owners.
An open item asked exactly that: whether the refusal is a first-call artifact.
Nobody had framed the work as touching it. The refusal was **evidence** — a
third data point, at the opposite end of a session's life from the two already
recorded — and it was written into the item. It did **not** close it: that item
asks for something else. A rule of "finishing closes it" would have invited the
session to decide those were the same question.

Morgan chose this two-part shape over the simple one, from the two the session
put to him.

## Install
An open-items file whose items carry anchors, plus
[tools/todo_progress.py](https://github.com/alex137/BestPractice/blob/staging/tools/todo_progress.py)
— `--changed BASE..HEAD` at the merge moment, and a bare run in the deep read.
A repo with no `TODO.md` needs nothing: the tool says so and exits.
