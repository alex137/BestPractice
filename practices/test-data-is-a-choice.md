---
slug:        test-data-is-a-choice
title:       "The data a result is scored on is a choice: name it, hold some out, and include a hard case"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Choosing how a result will be tested is a moment, not a file; the occasion index reaches it."
occasion:    "choosing the data a result will be scored on, or reporting a result scored on it"
gates:       []
index_clause: "name the test data, hold some out, include a hard case; say which a result used"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-11-19"
approved_by: "Alex, 2026-11-19: 'yes to all if they are general and not specific to this project', to a list of practices proposed from two days of simulation work in a dependent repo"
strength: assented
---
## Rule
**A result is a result on some data, and says which.** Name the data it was scored on wherever it is quoted. Anything fitted, calibrated or chosen from data is scored on data it did not see. And before a pass is reported, the same test is run on at least one kind of data that is harder or different in kind.

## Detail
Test data picked for convenience, small, clean and on hand, tends to flatter. That is fine for iteration and misleading as a verdict, and the two uses are easy to confuse because the number looks the same.

**Held out means held out from everything.** A threshold set from the test data, a range calibrated on it, a configuration selected because it scored best on it: each makes the score optimistic. If the effect turns out to be small, say so with the measurement; do not assume it.

**Different in kind, not only unseen.** Fresh samples of the same easy data test whether the result is overfitted. They do not test whether it holds where conditions differ. One run on something of another kind does, and when the result changes there, splitting the hard data by type usually shows that a small part of it carries the difference.

**Short data hides slow effects.** If anything in the system accumulates, drifts or saturates, a test shorter than that process cannot see it.

Where a constant nobody decided sits in a comparison, [constants-are-risk-inputs](constants-are-risk-inputs.md) applies; the choice of test data is the same kind of unexamined input.

## Why
A pass on easy data, quoted without the data's name, is read as a pass. The discovery that it was easy then arrives late and from outside.

## Story
2026-11-18 and 2026-11-19, in a dependent repo that models a piece of hardware and scores it by how much it degrades a set of published models. Every pass for a day and a half was scored on a few thousand words of very simple text, with the hardware's settings calibrated on that same text. When asked why the test text was so short, the session could give no reason but run time. Scored on varied text, results were two to seven times worse. Splitting that text by kind then showed most of the extra cost came from two passages the models may have known by heart; ordinary text cost only somewhat more than the simple text. Neither the flattering figure nor the alarming one had been the true picture.

## Install
Nothing to install.
