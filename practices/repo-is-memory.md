---
slug:        repo-is-memory
title:       The repo is the memory; sessions are ephemeral
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "starting any session cold"
gates:       ["reply"]
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 1
---
## Rule
Everything a future session needs — orientation, open items,
decisions, lessons — lives in committed files. A session's chat thread is
disposable; if knowledge exists only in a thread, it is already lost.

## Detail

## Why
Agent sessions (and humans returning after a month) start cold.
Repos that kept context in threads paid a re-derivation tax every session —
re-finding files, re-learning environment quirks, re-making settled decisions.

## Story
No single dated incident was recorded, because the failure this prevents is
continuous rather than punctual: **repos that kept context in threads paid a
re-derivation tax every session.**

The tax is concrete and itemisable -- re-finding files, re-learning
environment quirks, re-making decisions that were already settled once. Each
individual instance looks like ordinary startup work rather than like loss,
which is exactly why it can run indefinitely without anyone costing it.

The rule's sharpest clause is the one that makes it actionable: **if
knowledge exists only in a thread, it is already lost.** Not "at risk of
being lost" -- already, because nothing about a thread's contents is
reachable by the next session, and the moment of loss has therefore already
passed by the time anyone would think to look.

Agent sessions start cold every time, and a human returning after a month is
in the same position. That symmetry is why this is not an agent-specific
accommodation.

## Install
The three living documents below (MAP, TODO, GLOSSARY) plus a
project instructions file (`AGENTS.md`, plus a per-harness pointer file —
see [session-bootstrap](session-bootstrap.md)). Everything else in this
catalog is a refinement of this rule.
