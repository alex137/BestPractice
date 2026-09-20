---
slug:        example-starter-shared
title:       Replace me with your team's first practice
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "you are reading this because it is still here"
index_clause: "placeholder — delete this file once the team has written its own"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "{{APPROVER_NAME}}"
---
## Rule
This file exists to show the shape of a practice, not to be followed. Delete
it (or replace its content) once the team has written its first real one.

## Detail

## Why
A blank `practices/` directory gives a team nothing to copy from. This one
file — real frontmatter, real section headers, in the format Precedent
actually reads — is faster to edit into a first practice than reading the
spec cold. See
[`spec/PRACTICE_FORMAT.md`](https://github.com/alex137/BestPractice/blob/main/spec/PRACTICE_FORMAT.md)
in Precedent's own repo for what each field means and when a section can be
left empty.

## Story
**This file is its own first incident.** Until 2026-09-13 it shipped with an
empty `## Story`, and nothing minded: `catalogue-carries-stories` is a
universal practice, and the engine used to skip a universal check inside a
practice set because the set's `practices/` holds only its own files.
`binds_publishers` ended that skip, and the very next run of the checks in a
freshly bootstrapped set came back **`1 violated`** — pointing here. Every
new set would have opened its first pull request red.

So the section you are reading is the format demonstrating itself: an
**`active`** practice carries a real `## Story`, and a placeholder is not
exempt from the rule it is modelling. `## Detail` above is left empty on
purpose, because that section genuinely may be.

## Install
Nothing to install — a team practice is resolved live from this repo by
`tools/precedent_resolve.py`, once a consuming project declares this repo
as a `"level": "team"` source in its own `precedent.json`.
