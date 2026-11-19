---
slug:        name-the-target-case
title:       Name the case the work is for; a convenient case is a stand-in and is labeled as one
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Loads with prediction-before-the-run (adds_to), whose one index line covers testing a design; Morgan, 2026-11-19, option 2, to bring the universal occasion share back under its cap."
occasion:    "choosing which case, model, customer or dataset to test and optimize on"
gates:       []
index_clause: "name the target case; a convenient one is a labeled stand-in, checked early"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
adds_to:     prediction-before-the-run
added:       "2026-11-19"
approved_by: "Alex, 2026-11-19: 'yes to all if they are general and not specific to this project', to a list of practices proposed from two days of simulation work in a dependent repo"
strength: assented
---
## Rule
**Say which case the work is for, and test on it.** When a quicker or handier case is used in its place, call it a stand-in wherever its results appear, check early that it behaves like the target in the respect being tested, and return to the target before a result steers the design.

## Detail
The convenient case is the one already on disk, the one the tooling supports without an adapter, the one that runs in minutes. Using it is often right: more turns of the crank teach more. The failure is letting it become the subject by default, so that a day's effort goes into its particular weak point, which the target may not share.

**Three things keep a stand-in honest.** Its results are labeled with its name, never as "the result". One early run on the target shows whether the two fail in the same place. And the work plan says when the target is next run, so the stand-in cannot quietly hold the floor.

**The hardest case is not the target either.** Choosing the most demanding case because success there is safe is a different mistake with the same cost: effort spent on a difficulty the real target does not have.

## Why
Effort follows whatever is being measured. If that is a stand-in, the design improves for the stand-in.

## Story
2026-11-18 and 2026-11-19, in a dependent repo that models a piece of hardware and scores it by how much it degrades a set of published models. Most of two days went to the model that was quickest to run, which was also the least forgiving. The model the hardware was designed for took hours per run and needed its own adapter, so it was run rarely. The two turned out to have different limiting parts: work on the quick model's limit would not have helped the target at all. The person the work was for asked why the effort was centered where it was; the honest answer was convenience.

## Install
Nothing to install. A repository with a stated target says so in its map, so that a session picking a test case finds it.
