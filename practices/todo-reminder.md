---
slug:        todo-reminder
title:       "\"Todo reminder\" writes the item and marks it to be raised"
tier:        on-demand
severity:    default
applies_to:  ["todo/todo-*.md"]
occasion:    "a person says \"Todo reminder\", or asks to be reminded of something"
gates:       ["reply"]
index_clause: "\"Todo reminder\" -- write it, set disposition ask and remind_on, never a trigger"
checked_by:  null
defines:     ["Todo reminder"]
command:     {"Todo reminder": "Write the thing into the open-items file AND mark it as something to remind you about, so later sessions bring it up rather than waiting to be asked."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-13"
approved_by: "Morgan, 2026-09-13 -- coined and placed at universal in the same message.
  Amended 2026-09-16, on the open-item format migration landing the same day and on his
  own instruction the same turn: the mechanism moved from a `**Remind:**` line
  in a single TODO.md to `disposition`/`remind_on` frontmatter on a
  todo/todo-*.md item, and a standing prohibition on using a scheduled
  trigger for this was added, on \"let's use that as the default reminding
  system, not the reminders customer to Claude, so anything that needs to be
  reminded should become a Todo with the reminder defined\" (strength: decided)."
---
## Rule
When the person says **"Todo reminder"** — or anything that plainly means it —
write or update a `todo/todo-<date>-<slug>.md` item **in that same turn**,
with the content in `## What`, in their own words, and set two frontmatter
fields together:

```yaml
disposition: ask
remind_on:   <date, or the item's own `noted` date if none was given>
```

**Both fields, not one.** `disposition: ask` is what
[open-item-disposition](open-item-disposition.md) reads, and without it the
item defaults to `wait` and no session raises it — the exact opposite of what
was asked for. `remind_on` is what makes it a Reminder rather than an
ordinary `ask` item, per
[spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)'s
**Reminders** section: unset, it defaults to the item's `noted` date, which
reproduces "eligible immediately" — never leave it unset meaning "sometime."
Saying "Todo reminder" **is** the person setting `ask` on that item, which
only they can do.

Then say which item was written, and where.

**Never reach for a scheduled trigger to do this.** A tool that fires a
message back into a session later — `send_later`, `create_trigger` with
`run_once_at`, `ScheduleWakeup` — is not this practice, even when its own
description says "remind." The Todo item above is the one standing
mechanism, on every provider, whether or not this session's harness happens
to offer a scheduler: **pull, not push**, as
[spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)'s
**Reminders** section settles it. A scheduled trigger is a live resource
tied to one session's lifecycle — archived, and it silently stops firing —
where a Todo item just sits in the repository until a session, any session,
reads it.

## Detail
**Write what to remind them of, not only the subject.** *"Remind me about the
vendoring decision"* is a heading; *"still undecided whether a set gets the
whole deep check or a named subset"* is what makes the reminder usable months
later, by a session that was not here.

**It is a reminder, not a deadline.** Nothing fires on a schedule. What the
fields do is make the item visible to the two places that look:
[three-things](three-things.md), which weighs marked items when choosing what
matters now, and the **Due Reminders** table in generated
[todo/TODO.md](https://github.com/alex137/BestPractice/blob/staging/todo/TODO.md)
(built by
[tools/build_todo_index.py](https://github.com/alex137/BestPractice/blob/staging/tools/build_todo_index.py)),
which lists every `disposition: ask` item whose `remind_on` has actually
arrived — not merely every marked item, the way the older, date-blind
listing once did.

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

**Amended 2026-09-16**, the same day the open-item format migration (Part 1
of
[spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md))
landed and retired the single [TODO.md](https://github.com/alex137/BestPractice/blob/staging/TODO.md)
this practice's Rule had described since 2026-09-13, in favor of one file per
item under [todo/](https://github.com/alex137/BestPractice/blob/staging/todo/)
carrying `disposition` and `remind_on` as real fields rather than a
`**Remind:**` prose line. In the same conversation, asked to remove
Claude-only functionality from the practice layer more broadly — spawning
sessions, first — Morgan named this practice as the standing answer to what
a scheduled reminder should be instead: *"I think yesterday we added Todos
that can have reminders - let's use that as the default reminding system,
not the reminders customer to Claude, so anything that needs to be reminded
should become a Todo with the reminder defined."* (strength: decided). The
practice already said *"nothing fires on a schedule"*; what was missing was
the explicit prohibition on reaching for a scheduled-trigger tool instead,
now in the Rule above, and the mechanical detail — this practice had not yet
caught up to the frontmatter format the migration introduced.

## Install
Nothing beyond the open-items directory itself. `disposition` and
`remind_on` are frontmatter fields on the item;
[tools/build_todo_index.py](https://github.com/alex137/BestPractice/blob/staging/tools/build_todo_index.py)
regenerates [todo/TODO.md](https://github.com/alex137/BestPractice/blob/staging/todo/TODO.md)'s
Due Reminders table on every run, and the very deep check prints them under
OPEN ITEMS.
