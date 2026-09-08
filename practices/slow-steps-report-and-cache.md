---
slug:        slow-steps-report-and-cache
title:       A step that runs longer than a minute reports progress, and a heavy pure solve is memoized to disk
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing or running a gate, audit or solve that takes more than about a minute"
gates:       []
index_clause: "a long step prints elapsed and remaining; a heavy solve caches to disk"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Alex, 2026-09-08 — merged on main as catalogue entry 55, a check-in from dependent repo #1"
source_practice_number: null
---
## Rule
Two mechanics, one motive — a long wait must never be blind, and it must
never be repeated for nothing:

- **Progress with an estimate.** Any step expected to run for more than about
  a minute prints, on its error stream, a periodic line with items done,
  elapsed time, and an estimated time remaining computed from the rate so far
  — every N items, or on a timer — and a chained gate script echoes each
  step's elapsed seconds into its log so the next person can quote expected
  durations instead of rediscovering them. Record those durations where the
  run instructions live, dated.
- **Memoize the expensive pure function to disk.** When several gates (a
  self-check, a drift gate that spawns one subprocess per generated block, an
  audit) each re-derive the same expensive table, cache the solved result
  under a gitignored directory, keyed by the **content hash of the function's
  static, transitive in-repo import closure** — never a timestamp, never the
  calling process's import set (a caller-dependent key produces one entry per
  caller and never hits). Load the cache lazily at **every** entry point, not
  only the first one written, and keep an environment switch that forces a
  fresh solve: the cache is an accelerator, never a dependency.

## Detail
**Profile before declaring the remainder "the next lever."** A two-minute
profile removed the whole remainder twice in the originating case.

**Lazily, at every entry point** is the half that gets missed. A cache loaded
only where it was first needed leaves every other caller paying full price,
and the run looks exactly as slow as it did before — which reads as the cache
not working rather than as the cache not being consulted.

## Why
A gate that takes twenty minutes gets skipped, run concurrently with its
siblings (halving both), or trusted from memory. And a wait with nothing on
the screen is indistinguishable from a hang, so the operator either kills a
healthy run or waits on a dead one.

## Story
The originating case ran an eleven-fold re-solve per gate pass — one per
subprocess, nothing persisted between them. The first cache keyed on the
process's imports and never hit. The self-check then still ran nine minutes,
because a serial block executed *before* the cache load. And the owner's
question — *"do you have an estimate of how long we should expect to
wait?"* — had no answer, because nothing had ever measured it.

## Install
Memoize the solve under a source-content key with a bypass switch; add a
progress line with an estimate to anything over a minute; run heavy gates
sequentially; record measured durations, dated, in the run instructions;
export the pattern to any other heavy model the moment it appears.
