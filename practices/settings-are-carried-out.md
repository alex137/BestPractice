---
slug:        settings-are-carried-out
title:       A setting the code does not carry out stops the run
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Loads with prediction-before-the-run (adds_to), which commits a run's settings before it starts; this is whether the code then honours them."
occasion:    "adding a setting, variant or option to code that produces results"
gates:       []
index_clause: "an unhonoured setting stops the run; one setting name, one meaning"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
adds_to:     prediction-before-the-run
added:       "2026-11-24"
approved_by: "Alex, 2026-11-24: 'Yes.', to merging the drafted lessons; first relayed the same day as 'Yes let's update. But first do a review and see if you see improvements on your ideas before sending'"
strength: assented
---
## Rule
**Code that is given a setting it does not carry out stops, and says which setting.** A variant that runs under its name while doing nothing, or doing part of what the name says, produces a result that is filed under a claim it never tested. **One setting name has one meaning everywhere it is read.**

## Detail
A crash costs a rerun. A silent no-op costs every conclusion drawn from the result until somebody notices, and nobody is looking, because the run succeeded.

**Check at the start, not in the report.** Each part of the code that receives the settings says which ones it acts on; anything it was handed and does not act on is an error before the first result is written.

**The same name in two places means the same thing.** Where two pieces of code read one setting name and do different things with it, a comparison between them is a comparison of two different experiments under one label.

## Why
The settings are the description of what was run. If the code can ignore one, the description and the run have come apart, and every figure downstream carries the wrong label.

## Story
2026-11-24, in a project with several interchangeable pieces of code behind one set of settings. Three cases were found in an hour where a named variant ran while doing nothing or only part of what its name said. They were caught before any figure was affected.

## Install
Nothing to install. Code that takes settings refuses the ones it does not implement.
