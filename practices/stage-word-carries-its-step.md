---
slug:        stage-word-carries-its-step
title:       "A stage word carries its step number the first time a reply uses it"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A habit of the reply text itself, which no file path reaches. Routed by the `reply` gate. Decided: 2026-09-29, when the practice landed."
gates:       ["reply"]
gates_why:   "It governs how a reply is written, so the reply gate is the only moment it can fire."
index_clause: "the first stage word in a reply says its step: Booked (step 3 of 5)"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-29"
approved_by: "Morgan, 2026-09-29"
strength:    decided
---
## Rule
**The first time a reply uses a stage word, put its step right after it in
parentheses: Consider (step 1 of 5), Act (step 2 of 5), Booked (step 3 of
5), Debut (step 4 of 5), Produce (step 5 of 5).** Later uses in the same
reply stay bare. Each reply starts over, since the reader may have skipped
the last one.

**The other names for a stage count too.** "Go update", "Book it" and
"Approved" are step 3; "Test Readiness" is step 4; "Make live" is step 5. A
bare "Promote" names a move rather than one step, so it says which one:
Promote (step 4 of 5) or Promote (step 5 of 5).

**Only for the stage, not the everyday word.** "Act on it" and "consider
this" are ordinary English and get nothing.

## Detail
The five stages and their names are defined in [promote](promote.md). This
practice decides nothing about what a stage does; it only makes each reply
say where on the ladder a word sits.

**Not checked by a tool, on purpose.** "Act" and "consider" are common words,
so a check that looked for them would fire on ordinary sentences and teach
sessions to ignore it. Telling the stage apart from the word is judgment,
and the reply gate is where that judgment is asked for.

## Why
The stage names are new, and a name alone does not say where it sits. A
reader who sees "Booked" has to remember it is step 3 to know what came
before it and what comes next; the number says so in the reply itself, at
the cost of a few characters once.

## Story
On 2026-09-29, a day after the five stage names landed, Morgan said they
were still a little confusing because they were new, and asked for every
use to carry its place in the ladder. He picked the lighter version: once
per reply, at the first use, not on every repeat. In the same message his
own example put "book" at step two, which is the confusion this is for:
Booked is step 3.

## Install
Nothing to install. It reaches a session through the `reply` gate, which is
generated from this file's front matter, and nothing mechanical checks it,
for the reason in Detail above.
