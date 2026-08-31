---
slug:        mistakes-become-rules
title:       Mistakes become rules: root-cause the miss, then encode the prevention
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a review finds a defect"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 20
---
## Rule
When a mistake is caught — by the owner, by an audit, or by a later
pass discovering an earlier session's error — fixing the instance is half the
job. Before the session ends, root-cause it *five-whys style*: ask why
iteratively, past the surface slip, until the answer is a **process
property** — a missing rule, a missing check, a judgment recorded at the
wrong granularity, a stale document trusted, a default that invites the
error — stopping at the level where a cheap guard exists. Then encode the
prevention at the strongest rung available: (a) an **audit or lint** if the
failure is mechanically checkable (practice 6 — conventions become audits);
(b) else a **written rule, dated, carrying its origin incident** (practices
5 and 16 — the incident is both the justification and the test case); (c) if
the lesson is generic, **export it** (practice 14). Discuss the choice with
the owner when it involves a judgment call — which rung, what scope, whether
the guard is worth its cost.

**Proportionality guard.** Not every slip earns a rule: the trigger is a
systemic cause (it would recur) or real cost (rework, a wrong external
statement, lost work). Prefer strengthening an existing rule or audit over
minting a new one — rule-bloat is itself a failure mode, and a silent rule
nobody agreed to is how it starts.

## Why
Repos that only fix instances relive their mistakes with new
surface details; the systemic cause remains free to fire again. The
root-cause habit is what turned one dependent repo's worst misses into its
strongest machinery — every audit it runs exists because of one specific,
recorded incident, and the audit that would have caught the incident is the
test of whether the root cause was actually found. The origin incident in
the rule text is load-bearing twice over: it tells a future reader what the
rule is protecting against (so the rule can be re-judged when the world
changes), and it calibrates proportionality (a guard that would not have
caught its own origin incident is theater).

## Story

## Install
A habit plus a review question. The habit: end any session in
which a mistake was caught with an explicit root-cause note and its
prevention, in the same change-set as the fix. The review question, for the
owner: "does this guard's rung (audit / dated rule / export) match the
failure's checkability?" Seed it retroactively: the next time an old mistake
class recurs, that is the origin incident for its rule.
