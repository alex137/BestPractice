---
slug:        prediction-before-the-run
title:       Write down what you expect a decisive run to show, and fix its settings, before it runs
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Choosing how a result will be tested is a moment, not a file; the occasion index reaches it."
occasion:    "testing a design, or choosing what a result is scored on"
gates:       []
index_clause: "predict first; its additions cover pass marks, data, stand-ins, batches"
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
**Before a run that will decide something, commit two things: the settings it will use, and what you expect it to show.** The settings go in the repository before any result exists. The prediction goes where the result will be reported, with the reasoning in a line.

## Detail
Settings chosen after seeing results are tuned to them, whatever the intent. Committing the configuration first, in its own commit, is what lets a later reader trust that it was not adjusted until it passed. When a configuration has to change after results are in, the change is recorded as a change, with its reason, and the earlier results stay.

**A prediction makes a result informative either way.** If it holds, the reasoning behind it gains weight. If it fails, the failure points at what was misunderstood, which a result with no expectation attached cannot do. Say afterwards, plainly, whether it held, and by how much it was off.

**Do not tune toward the prediction.** Its value is that it can be wrong.

This is the experimental form of [verify-postcondition](verify-postcondition.md): name the state you expect before the operation, then test for that.

## Why
Without a recorded expectation every outcome can be explained afterwards, and a team that can explain anything has learned nothing it can rely on.

## Story
2026-11-18 and 2026-11-19, in a dependent repo that models a piece of hardware and scores it by how much it degrades a set of published models. The hardware's configurations were committed on their own before any run used them, and later additions were logged as additions. A proposed design change was recorded as a prediction, with the figure a fast test gave for it, before the slow test ran. The slow test confirmed the direction and came in somewhat short of the predicted size. Because both were on record, the shortfall was itself useful: it measured how optimistic the fast test was.

## Install
Nothing to install.
