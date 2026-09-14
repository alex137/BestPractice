---
slug:        todo-reminder
title:       "\"Todo reminder\" writes the item and marks it to be raised"
tier:        on-demand
severity:    default
applies_to:  ["TODO.md", "**/TODO.md"]
occasion:    "a person says \"Todo reminder\", or asks to be reminded of something"
gates:       ["reply"]
index_clause: "\"Todo reminder\" -- write the item, mark it `**Remind:**`, set disposition `ask`"
checked_by:  null
defines:     ["Todo reminder"]
command:     {"Todo reminder": "Write the thing into the open-items file AND mark it as something to remind you about, so later sessions bring it up rather than waiting to be asked."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-13"
approved_by: "Morgan, 2026-09-13 -- coined and placed at universal in the same message"
---
## Rule
When the person says **"Todo reminder"** — or anything that plainly means it —
write the thing into the open-items file **in that same turn**, and mark it as
one they want raised:

```
**Remind:** <what to remind them of, in their words> (<date>, <who asked>)
**Disposition:** ask (<date>, <who asked>)
```

**Both lines, not one.** `**Remind:**` says a session should bring it up;
`ask` is what [open-item-disposition](open-item-disposition.md) reads, and
without it the item defaults to `wait` and no session raises it — which is the
exact opposite of what was asked for. Saying "Todo reminder" **is** the person
setting `ask` on that item, which only they can do.

Then say which item was written, and where.

## Detail
**Write what to remind them of, not only the subject.** *"Remind me about the
vendoring decision"* is a heading; *"still undecided whether a set gets the
whole deep check or a named subset"* is what makes the reminder usable months
later, by a session that was not here.

**It is a reminder, not a deadline.** Nothing fires on a schedule. What the
mark does is make the item visible to the two places that look:
[three-things](three-things.md), which weighs marked items when choosing what
matters now, and
[tools/todo_progress.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/todo_progress.py),
which lists every marked item on a full run.

**Marked is not the same as urgent, and a reminder is not a recurring alarm.**
A session raising the same marked item in three consecutive replies has turned
a reminder into nagging. Raise it when it bears on what is in front of them.

## Why
An open item has one bit about attention — `wait`, `ask`, `parked` — and it
answers *may a session raise this*. It does not answer *should it*. The gap
matters for the small set of items the person is actively carrying: they do not
want to be the one who remembers, and an `ask` item sitting among eighty others
is indistinguishable from one nobody has looked at since it was written.

The phrase exists because the alternative is the person holding it in their
head, which is the thing this whole system is for not doing.

## Story
**Coined by Morgan, 2026-09-13**, in the message that also asked for the
`Three Things` weighting, and phrased as the mechanism rather than the name:
*"If I say 'Todo reminder' or something similar, then: the thing I want you to
remind me on, put it into the TODO file, and note that you should remind me of
that."*

It landed on a day that had already produced two other reminder-shaped
moments. Earlier in the same thread he asked to be reminded, after a merge, to
talk about further reductions — and that reminder survived only because the
session happened to still be running. Nothing had written it down, so a
container restart would have taken it.

## Install
Nothing beyond the open-items file itself. `**Remind:**` is a line in the item;
[tools/todo_progress.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/todo_progress.py)
lists every marked item on a bare run, and the very deep check prints them
under OPEN ITEMS.
