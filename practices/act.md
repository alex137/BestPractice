---
slug:        act
title:       "\"Act\" is stage 2: build the change on the session's feature branch"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Act\" or \"Promote 2\", or asks to start building after a plan"
gates:       []
index_clause: "stage 2: build it on the session's feature branch, pushed so it survives"
checked_by:  null
defines:     ["Act"]
command:     {"Act": "Stage 2 (Promote 2): build the change, on this session's own feature branch, pushed to GitHub so a lost session does not lose it -- not yet shared.", "Build": "The same as **Act**."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-29"
approved_by: "Morgan, 2026-09-27 -- Act lives on the session's temporary (feature) branch and \"booked is all about moving it from there to pre-staging so ... it won't get lost\""
strength:    decided
---
## Rule
**Act is step 2 of the five-stage ladder ([promote](promote.md)): make the
change.** The work lives on this session's own **feature branch** -- the
short-lived branch named like `claude/<topic>-<random>` -- and is **pushed
there**, so a reclaimed container loses nothing. It is not shared yet:
nothing reaches pre-staging until [Booked](go-update.md).

**Act comes after [Consider](consider.md)**, even if the plan is one line.
A request to build with no plan yet gets the one-line plan first, in the
same reply.

**A feature branch is easy to forget**, which is why Act never ends a
session on its own. Work that reached Act but not Booked is said plainly
at the end of the reply, with Booked recommended
([the-boildown](the-boildown.md)).

## Why
Building straight onto a shared branch skips the checks and the chance to
change course; building only in the container loses the work when the
session ends. The feature branch is the one place that is both private and
safe.

## Story
Named 2026-09-27. Morgan first wrote "local clone" for this stage, then
corrected it: he meant the session's feature branch on GitHub, and Booked
is the step that moves it somewhere it will not be forgotten.

## Install
Nothing to install. The reply gate already says when a feature branch holds
work that has not landed.
