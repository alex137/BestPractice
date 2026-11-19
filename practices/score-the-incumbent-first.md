---
slug:        score-the-incumbent-first
title:       Before a pass mark judges your design, score the thing it competes with on it
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Loads with prediction-before-the-run (adds_to), whose one index line covers testing a design; Morgan, 2026-11-19, option 2, to bring the universal occasion share back under its cap."
occasion:    "setting a pass mark, margin or threshold that a design will be judged against"
gates:       []
index_clause: "score what you compete with on your own pass mark before judging yourself"
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
**A pass mark means nothing until the incumbent has been scored against it.** Before a margin, threshold or acceptance test is used to say a design passes or fails, run the thing the design competes with, or the thing in use today, through the same test under the same rules, and write its score beside the mark.

## Detail
A mark chosen from first principles ("no more than this much worse than exact") feels neutral and is not. It may be stricter than anything in the field meets, in which case every failure it reports is partly a failure of the mark; or looser, in which case its passes are worth less than they look.

**Same rules means the same handicaps.** If the design under test gets no tuning, no calibration and no retries, the incumbent is scored that way too, and then again the way it is normally run. Both scores go in the write-up, labeled. The gap between them is itself a finding: it says how much of the incumbent's standing comes from help the design has not yet been given.

**Do it early.** The incumbent's score is cheap next to the work the mark will go on to steer, and it recalibrates every result that came before it.

This is the test-side companion of [check-source-architecture](check-source-architecture.md), which checks that both options exist before they are costed.

## Why
A team holds its own design to a standard and reads each failure as the design's. If the competition would fail the same standard, the team has been solving a harder problem than the one it has, and does not know it.

## Story
2026-11-18 and 2026-11-19, in a dependent repo that models a piece of hardware and scores it by how much it degrades a set of published models. A margin was set on day one and every result for two days was read against it. On the second day the incumbent technology, in the reduced-precision formats it now ships in and with no tuning, was put through the same test for the first time. It sat on the margin in one configuration and outside it in the one actually shipped. The margin was as strict as the competition's untuned practice, and nobody had known.

## Install
Nothing to install. Where a repository keeps its pass marks in a registry, the incumbent's score is a row in it.
