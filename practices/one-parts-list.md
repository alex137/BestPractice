---
slug:        one-parts-list
title:       Anything built or tested in pieces keeps one parts list, and what a run left out goes there
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Loads with prediction-before-the-run (adds_to), whose one index line covers testing a design; a parts list is recognised by what it is for, not by a path."
occasion:    "building or testing something in pieces, or being asked what is left before the whole thing runs"
gates:       []
index_clause: "one parts list: real, stand-in or missing; what is left is read from it"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
adds_to:     prediction-before-the-run
added:       "2026-11-24"
approved_by: "Alex, 2026-11-24: 'Yes and granted', to the drafted rule as written, joined runs with stand-ins allowed and labelled; proposed the same day by the coordinating session of the project where it was learned"
strength: assented
---
## Rule
**Anything built, modelled or tested in pieces keeps one parts list in its registry** ([registry-source-of-truth](registry-source-of-truth.md)): every part between input and output, each marked **real** (built and run, naming the run that shows it), **stand-in** (idealized, saying what it stands for) or **missing**.

1. **A run that leaves a part out, or uses an ideal one, updates that part's line in the same commit.** A caveat written only in the run's own note is lost.
2. **Every part records the basis it was built on**: the component library, the dataset, the model, the version. Figures from parts on different bases are not compared or added up until the parts are redone on one.
3. **A joined run prints the list's state with its result.** While any part in it is a stand-in, missing or on another basis, the result is a check of how the parts fit and is never reported as the whole thing's figure; the build refuses to label it as one.
4. **"What is left before X?" is answered by reading the list, never from memory.** If there is no list, writing it is the first task, before any estimate.

## Detail
The list is short: a line a part, in the file the build already reads. What makes it work is that it is the only place a gap is recorded as a gap. A run's note still says what the run left out, because the note is where a reader of that result looks; the list is where someone planning the next step looks.

**"Real" needs a run to point at.** A part that exists as a drawing, a function or a config, and has never been run against the neighbours it will sit between, is not yet real.

**A joined run with stand-ins can still be worth doing**, to find out that two parts disagree about an interface before either is finished. It is proposed as that, with the list's state beside it, and it gets a prediction like any other run. What it cannot do is answer "does the whole thing meet its mark".

**The basis is where the quiet failures are.** Two parts can each pass their own test and never have been two parts of one thing. Recording the basis on every line turns that from a discovery into a column anyone can read down.

## Why
Each run is honest about its own gaps, and the gaps add up in nobody's head. A dozen truthful caveats in a dozen notes read, from memory, as two or three.

## Story
2026-11-24, in a dependent repo that simulates a piece of hardware block by block, across many sessions and days. Every run's note said plainly what that run left out. Asked when the whole thing would be run, the coordinating session believed a few parts were missing and proposed a first joined run of the parts that existed. Asked for a plan, the worker that owned the design counted several times as many parts that were ideal stand-ins or did not exist, and found the two main blocks had been built on two different component libraries, so their figures had never described the same device. Redone on one library, one block's headline figure got much worse and missed its mark. The person the work was for asked why the gaps were only being discovered then.

## Install
Nothing to install. A repository that builds in pieces adds the list to the registry its build reads, and has the build print the list's state on any run that joins more than one part.
