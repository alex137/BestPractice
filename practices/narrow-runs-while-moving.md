---
slug:        narrow-runs-while-moving
title:       While a design is still changing, run the few tests that can change a decision; keep the wide grid for regression
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Choosing how a result will be tested is a moment, not a file; the occasion index reaches it."
occasion:    "planning a batch of test runs while the design under test is still changing"
gates:       []
index_clause: "while the design moves, run what can change a decision; grids are for regression"
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
**While the design is moving, each run should be able to change a decision.** Ask of every run what would be done differently on each outcome; if nothing, drop it. The exhaustive grid of every case against every configuration is a regression check for a design that has settled, and is run then.

## Detail
A grid feels thorough and is cheap to specify, so it gets launched. While the design is changing it mostly re-confirms answers already known, across variants that barely differ, and by the time it finishes the configuration it tested has been replaced.

**The questions that matter are few.** Most of what a project learns comes from a small number of pointed runs: one part switched off, one input swept, one variant against its neighbor. Those can be listed, and the list is short.

**Cost multiplies quietly.** Cases times configurations times repeats times the size of the test data is hours where each factor looked small. Before launching, read the tool's own estimate of the whole batch ([answer-first-ask-before-long-work](answer-first-ask-before-long-work.md)).

**One repeat is enough to tell pass from fail unless the result sits near the line.** Repeat the cases near the line, not the whole batch.

**Keep the grid.** Once the design settles, the same grid, run in full and unattended, is what catches a later change that breaks an earlier result. It is the right tool at that point.

## Why
Machine time spent confirming what is known is time the next real question waits. And a wide batch on a moving design produces results about a configuration that no longer exists.

## Story
2026-11-18 and 2026-11-19, in a dependent repo that models a piece of hardware and scores it by how much it degrades a set of published models. A suite was built to run every model against every configuration, fifty-four per model, and one worker started ninety-nine more. Meanwhile each thing actually learned had come from a handful of runs. The person the work was for asked whether all the testing was needed to learn. The batches were cut to the cases whose outcome would change a decision, and the pace of findings went up, not down.

## Install
Nothing to install.
