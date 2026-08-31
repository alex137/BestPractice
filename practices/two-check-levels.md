---
slug:        two-check-levels
title:       Two named check levels: a fast one for every commit, a full one before merge
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "naming what \"run the checks\" means in a repo"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 44
---
## Rule
A repo of any size ends up wanting two different things when it
says "check this": a fast, cheap sanity pass a session runs constantly
without thinking about it, and a slower, complete audit that gates a merge.
Give the two levels fixed, distinct names in the repo's own
[GLOSSARY.md](templates/GLOSSARY.md.template) — a plain pair like *light
check* and *deep check* reads well, but any repo-chosen pair is fine — so a
person or a session can ask for one or the other unambiguously ("run the
light check before you commit that" vs. "this needs a deep check before we
merge") instead of re-describing what "check" means every time.

## Why
Without named levels, "run the checks" is ambiguous between two
very different costs, and the drift goes one of two ways: sessions run the
expensive audit so often that it gets skipped when time is short, or they
run only the cheap pass and the expensive one quietly stops happening
before merges. Naming the two levels separately keeps both cadences
legible: the fast one stays cheap enough to run on every commit path with
no friction, the full one stays a deliberate, named gate that is obviously
missing if it's skipped.

## Story

## Install
This repo's own [tools/doc_lint.py](tools/doc_lint.py) is
already the fast pass — it scans only the markdown a session touched — and
[tools/practice_audit.py](tools/practice_audit.py) is already the full one
— the public-safe scrub, baseline-hash checks, and everything else that
needs the whole repo. Naming them is the only step this practice adds: pick
the repo's own pair of names, add both to `GLOSSARY.md` with what each one
actually runs, and reference the names (not just the script paths) in the
merge runbook (practice 9) and in any CI wiring (practice 6). A repo that
adds its own extra fast checks (secret-shaped strings, conflict markers,
JSON/YAML syntax) folds them into the "light" name rather than inventing a
third level — two named levels is the right number for almost every repo.
