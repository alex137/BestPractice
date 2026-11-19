---
slug:        cheap-test-earns-trust
title:       A faster test stands in for a slower one only after it has predicted results the slow one already gave
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Loads with prediction-before-the-run (adds_to), whose one index line covers testing a design; Morgan, 2026-11-19, option 2, to bring the universal occasion share back under its cap."
occasion:    "using a faster, smaller or partial test to stand in for a slower one"
gates:       []
index_clause: "a cheap test must reproduce known results of the slow one before it is trusted"
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
**A cheap test is checked against results you already have before it is used to choose anything.** Take the cases the slow test has already settled, run the cheap one on them, and see whether it puts them in the same order and on the same side of the pass mark. Use it for what it gets right, and say what it does not cover.

## Detail
A proxy is attractive because it is fast, and the speed makes it easy to adopt before anyone has asked whether it measures the same thing. The check costs little: the slow results exist, and the proxy is quick by definition.

**Ask three questions of it.** Does it order known cases the way the slow test does? Is there a value of it that separates known passes from known failures? And for which kinds of difference does it hold: a proxy that ranks one sort of change correctly can be blind to another.

**A proxy usually orders options within one case and does not compare cases.** Expect to need one slow run per case to place its pass line.

**Try more than one summary of the proxy.** The obvious figure may fail where another reading of the same data works, such as the worst part instead of the typical part, or an error measured against each value instead of against the average.

**Then use it to predict, and record the prediction** ([prediction-before-the-run](prediction-before-the-run.md)). Each slow run after that is a test of the proxy as well as of the design.

## Why
An unvalidated proxy steers confidently in a direction nobody has checked. A validated one turns hours into minutes for exactly the questions it has earned.

## Story
2026-11-18 and 2026-11-19, in a dependent repo that models a piece of hardware and scores it by how much it degrades a set of published models. A per-layer shortcut was used to rank configurations and later found to rank them wrongly on the large models: it rated as minor the one error that did nearly all the damage at full depth. A second shortcut, at the level of a single unit, was proposed by the person the work was for. Its obvious measure failed the same way. A different reading of the same data matched the order of thirty-eight results the slow test had already produced, almost exactly, and its first prediction about an untried design was confirmed in direction and rough size within the hour.

## Install
Nothing to install.
