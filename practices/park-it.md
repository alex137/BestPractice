---
slug:        park-it
title:       "\"Park it\" marks an item parked and ends the subject"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Park it\" about an open item or a question"
gates:       ["reply"]
index_clause: "\"Park it\" -- mark the item `parked` now; never raise it unprompted again"
checked_by:  null
defines:     ["Park it"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08 -- coined the same day, moved up to universal the same day"
---
## Rule
When the person says **"Park it"**, write
`**Disposition:** parked (<date>, <who said it>)` into the item they mean,
**in that same turn**, and no session raises that item unprompted again --
not this one, and not a later one that decides it has become urgent.

**They owe no explanation for parking something, and the session asks no
follow-up question about it.** The phrase exists to end a conversation, not
to open one. The response is to do it and say which item was marked.

## Detail
**The item they mean is the one the thread is about.** If two are genuinely
in play, park the one under discussion and say in one line which anchor was
marked -- a wrong guess then costs three words to correct rather than a
re-explanation.

**"Park it" can arrive about something not yet written down at all.** Then
write the item first and mark it `parked` in the same commit:
[repo-is-memory](repo-is-memory.md) does not bend, and parked is not the
same as forgotten.

**Unparking belongs to the person who parked it.** A later session that
thinks a parked item has become urgent may act on the item's content if the
work in front of it needs that, but does not put the question back to them.

What `parked` then means, and the two other dispositions an open item can
carry, is [open-item-disposition](open-item-disposition.md)'s: an item with
no disposition is `wait`, and a session raises an item only if it says
`ask`.

## Why
A standing phrase costs two words instead of a re-explanation, and it
survives the session that heard it. The failure worth not repeating is the
one "Go merge" already recorded: a session that had not read the definition
went and asked what the phrase meant, which is precisely the interruption
the phrase was invented to stop. **So a phrase is only worth having if it is
written where a session reads before it works** -- which is the argument for
shipping it with the engine rather than leaving each person to invent and
document their own.

The problem it solves is narrower than "stop asking me things": a minor,
genuinely undecided question raised repeatedly in one day by parallel
sessions, each of which was individually behaving correctly. Nothing was
wrong with any one of them. The fix has to be a mark on the item, because
that is the only thing all of them read.

## Story
**Coined by Morgan, 2026-09-08**, in the conversation that produced
[open-item-disposition](open-item-disposition.md). Offered a phrase for
setting an item to `parked`, he answered: *"'Park it' is a fine phrase, and
put it in the glossary."*

**The glossary half was reversed later the same day** -- *"Don't put it in
the glossary"* -- which is why this practice's `defines:` was cleared once
and then restored on the move: the phrase is a term this catalogue defines,
and what he declined was a separate list of disposition words. Recorded
because the two instructions read as contradictory unless the order is
stated.

It lived for one day as a repo-local practice in Precedent's own tree, with
a paragraph in its own Detail explaining that it was at the wrong level on
purpose -- one person's phrase, recorded there only because a session rooted
in that repository could not reach the private individual set to put it
anywhere better. **Moved to universal 2026-09-08**, along with `go-merge`,
on Morgan's decision that these are the project's own commands rather than
one person's habits: *"we should have our own commands we use for people who
live in our universe."*

## Install
Nothing mechanical checks that the phrase was *honoured* -- like `go-merge`,
that lives in the conversation rather than in the tree. What a repository
can check is that the phrase is documented where its own sessions actually
read, which is what Precedent's own repo-local `check_park_it.py` asserts
against its `AGENTS.md`. An adopter needs no equivalent: the phrase reaches
every session through the occasion index above, which is generated.
