---
slug:        park-it
title:       Park it — the phrase that marks an item parked and ends the subject
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "Morgan says \"Park it\" about an open item or a question"
gates:       ["reply"]
index_clause: "\"Park it\" -- mark the item `parked` this turn, and never raise it unprompted again"
checked_by:  "local/tools/checks/check_park_it.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08"
---
## Rule
When Morgan says **"Park it"**, the session writes
`**Disposition:** parked (<date>, Morgan)` into the item he means, in that
same turn, and no session raises that item unprompted again. He owes no
explanation for parking something, and the session asks no follow-up
question about it — the phrase exists to end a conversation, not to open
one.

## Detail
The item he means is the one the thread is about. If two are genuinely in
play, park the one under discussion and say in one line which anchor was
marked, so a wrong guess costs him three words to correct rather than a
re-explanation.

"Park it" can also arrive about a question that is not yet in
[TODO.md](../../TODO.md) at all. Then the session writes the item first —
[repo-is-memory](../../practices/repo-is-memory.md) does not bend, and parked is not the same as
forgotten — and marks it `parked` in the same commit.

Unparking is his alone. A later session that thinks a parked item has become
urgent may act on the item's content if the work in front of it needs that,
but does not put the question back to him.

**This practice is at the wrong level on purpose.** It is one person's
standing phrase, which belongs in his individual set, exactly as
`go-merge` does — the same reasoning that retired the universal
`merge-authorization-keyword` on 2026-09-07. It is repo-local here because a
session rooted in this repository cannot attach the private sets at all
(`add_repo` refuses every cross-owner add, measured both directions on
2026-09-07 — see [AGENTS.md](../../AGENTS.md)'s gotchas), so the alternative was
recording it nowhere. Moving it is [TODO.md](../../TODO.md)'s `park-it-to-individual-set`
item, and the individual copy wins the moment it exists.

## Why
The value of a standing phrase is that it costs him two words instead of a
re-explanation in every session, and that it survives the session that heard
it. "Go merge" already proves both halves. The failure that phrase's own
history records is the one worth not repeating: a session that had not read
the definition went and asked what it meant, which is precisely the
interruption the phrase was invented to stop. So a phrase is only worth
having if it is written where a session reads before it works — which is why
this practice is checked on [AGENTS.md](../../AGENTS.md) rather than left as prose.

## Story
Coined by Morgan on 2026-09-08, in the conversation that produced
[open-item-disposition](../../practices/open-item-disposition.md). Offered a phrase for setting an item to
`parked`, he answered: *"'Park it' is a fine phrase, and put it in the
glossary."* The problem it solves is in that practice's own Story — a minor,
genuinely undecided question raised at him repeatedly in one day by parallel
sessions, each of which was individually behaving correctly.

## Install
The phrase is defined in [AGENTS.md](../../AGENTS.md) beside the "Go merge" paragraph, which
is where a session actually reads it; `local/tools/checks/check_park_it.py`
fails if it is not. The disposition it writes, and everything about what
`parked` then means, is [open-item-disposition](../../practices/open-item-disposition.md)'s.
