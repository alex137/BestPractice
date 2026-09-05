---
slug:        cross-source-rollout
title:       A change with cross-source implications rolls out now, or queues with why
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a change here has implications for how an attached team, individual, or repo-local source should work"
gates:       ["merge"]
index_clause: "roll it out to attached sources now; else a blocked-on TODO"
checked_by:  null
defines:     ["cross-source rollout"]
status:      active
supersedes:  []
overrides:   null
added:       2026-09-05
approved_by: "Morgan F"
---
## Rule
A change to how this repo's own checks, conventions, or engine work — a
new mechanical gate, a changed merge or push convention, a tool whose
behavior a private source relies on — is not finished at this repo's own
commit if the change has implications for how a team, individual, or
repo-local source should work. If that source is attached to this same
session, roll the change out to it in this session, before the thread
ends — the same "do it now, not later" reasoning
[todo-is-a-handoff](todo-is-a-handoff.md) already applies to any
agent-doable item. If it is not attached, the rollout is genuinely blocked
on a session that has it: queue it in `TODO.md` with `blocked-on: <source
name> not attached this session`, naming the specific change and what the
other source needs to do about it — never a bare "check the other repos"
reminder.

## Detail
This is `todo-is-a-handoff` applied to one recurring boundary: the
four-way split between universal, team, individual, and repo-local
practices means a change made in one of them routinely has a sibling
implication in another, and "the other repo isn't open right now" is a
real, nameable `blocked-on` reason — distinct from the convenience
deferral `todo-is-a-handoff` already rules out.

It is also distinct from [parallel-artifact-ledger](parallel-artifact-ledger.md): that practice's family
members are independent implementations of *one design* (three harness
adapters, same architecture). These four sources are not parallel copies
of each other at all — individual, team, and repo-local practices are
novel content their own owners write, most of which has nothing to do
with universal. What transfers here is narrower and specific: a change to
the *mechanism* a source relies on (an engine tool's behavior, a
merge/push/deep-check convention, a resolver rule) — not every change to
this repo's own prose.

[very-deep-check](very-deep-check.md) is this same gap seen from the other side, on-demand rather
than at every merge: run against the checkout plus every attached
team/individual source, it should read whether a check, tool, or
convention this repo changed has left an attached source assuming the old
behavior, and fix or flag it in the same pass. This practice is what
should have made that drift impossible to accumulate in the first place;
`very-deep-check`'s own cross-source-staleness bullet is the backstop for
whatever a session's rollout at merge time still misses.

## Why
A four-source split with no standing rule for propagating mechanism
changes across it degrades exactly like any other split-ownership system:
each source drifts from what the others now assume, silently, because no
single commit's diff shows the gap — the change lands cleanly in the repo
that made it, and the repos that should have followed simply don't, with
nothing at merge time asking whether they needed to.

## Story
Raised directly, in the same conversation that added `very-deep-check`'s
own source-presence and stale-branch-sweep additions — the request that
closed those two gaps immediately generalized to: whenever this repo
changes something an attached sibling source should also reflect, that
rollout needs the same standing rule `todo-is-a-handoff` already gives
every other agent-doable item, not a one-off fix each time it happens to
get noticed.

## Install
No mechanical check, and not for lack of trying: "does this change have
implications for another source" is a judgment call about the *meaning*
of a diff, the same class `checkable-gets-checked` already lets
`todo-is-a-handoff` leave unchecked for the identical reason. One
narrower thing could plausibly be checked later — that every `blocked-on:
<source> not attached` item this practice creates actually gets picked up
once that source is attached, rather than sitting in `TODO.md`
indefinitely — left `checked_by: null` here rather than wired in without
running it, per `checkable-gets-checked`.
