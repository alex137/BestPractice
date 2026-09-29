---
slug:        gates-fail-fast
title:       A gate runs its cheap checks first and stops at the first failure
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing or running a gate that chains several checks or runs work concurrently"
gates:       []
index_clause: "cheap checks first; a failure skips the slow ones and stops the work beside it"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "Alex, 2026-09-28 -- \"Let's do the fixes\" (the cheap-first ordering and the stop at the first crash were two of them)"
strength:    decided
source_practice_number: null
---
## Rule
**Order a gate's checks by cost: the fast ones first, the slow ones last.**
Once a fast check has failed, **do not start a slow one** — the push or
merge is refused either way, and the fix will be checked again. When a
gate runs units **concurrently**, the **first failure stops the others**
and the gate exits at once, naming what failed. A switch runs everything
regardless, for the session that wants every failure in one pass.

## Detail
**A pool hides a crash behind its slowest member.** A thread or process
pool used as a context manager waits for every running task before it
lets an exception out, so a unit that crashed in its first second is
reported when the slowest unit beside it finishes. Run each unit in its
own process group and kill the groups on the first failure; a killed
process's children (a solve's own worker pool) go with its group.

**Reordering does not change what a pass means.** The same checks run
on a clean tree; only a failing tree is cut short. A recorded pass keyed
on the list of checks stays valid, because the list is the same.

**Kill by group, never by pattern.** A pattern can match the shell that
issued the kill; a unit started in its own session has a group of its
own to kill.

This practice has no repository-level check (`checked_by: null`): it is a
property of the gate runners, and the harness tests them — with a fast
failure the slow checks do not run, the override runs them, and a gate
with one unit that sleeps a minute and one that fails exits in seconds.

**The same order holds outside a gate.** Before starting any expensive
run — a cold solve, a regeneration, a long suite — run the cheap check
that could invalidate it: scan the cache keys the run will use, run the
one-case smoke version, lint the input. Minutes spent afterwards finding
that the run was wasted are the same waste as a slow check run first.

## Why
A slow check exists to catch the rare deep problem. When it runs first,
every shallow problem — a stale generated file, a lint slip — costs its
full duration before anyone hears about it, and a person who has waited
ten minutes for a one-second finding learns to stop running the gate.

## Story
In one session the same gate cost twenty minutes over a one-second
finding. A merge check ran a four-minute harness suite first and
refused, after ten minutes, over generated views that a one-second check
reports; the fixed push then waited another ten. The same day a document
gate that emitted blocks in a thread pool reported two crashes — each in
its emitter's first second — fourteen minutes later apiece, when the
slowest solve beside them finished.

## Install
Sort the gate's checks into a cheap list and a slow list; run the cheap
list first and skip the slow one after a failure, behind an override
that runs everything. Start each concurrent unit in its own process
group, and on the first failure kill every other group and exit naming
the failure.
