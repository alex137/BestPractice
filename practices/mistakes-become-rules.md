---
slug:        mistakes-become-rules
title:       "Mistakes become rules: root-cause the miss, then encode the prevention"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a defect is fixed -- whether a review found it, the person reported it, or the session hit it itself"
gates:       ["review"]
index_clause: "root-cause the miss, then encode the prevention"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 20
---
## Rule
When a mistake is caught — by the owner, by an audit, by the person simply
reporting it, or by a later pass discovering an earlier session's error —
fixing the instance is half the job. **The trigger is the fix, not the
review**: most defects here are never reviewed, they are just mentioned and
repaired, and a rule that waits for a review never fires on them. Before the session ends, root-cause it *five-whys style*: ask why
iteratively, past the surface slip, until the answer is a **process
property** — a missing rule, a missing check, a judgment recorded at the
wrong granularity, a stale document trusted, a default that invites the
error — stopping at the level where a cheap guard exists. Then encode the
prevention at the strongest rung available: (a) an **audit or lint** if the
failure is mechanically checkable ([convention-to-audit](convention-to-audit.md) — conventions become audits);
(b) else a **written rule, dated, carrying its origin incident** ([cite-the-incident](cite-the-incident.md)
and [volatile-rules-carry-dates](volatile-rules-carry-dates.md) — the incident is both the justification and the test case); (c) if
the lesson is generic, **export it** ([practice-export-loop](practice-export-loop.md)). Discuss the choice with
the owner when it involves a judgment call — which rung, what scope, whether
the guard is worth its cost.

**Proportionality guard.** Not every slip earns a rule: the trigger is a
systemic cause (it would recur) or real cost (rework, a wrong external
statement, lost work). Prefer strengthening an existing rule or audit over
minting a new one — rule-bloat is itself a failure mode, and a silent rule
nobody agreed to is how it starts.

## Detail

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
No single dated incident is recorded, because the evidence for this rule is
the aggregate rather than one case: **the root-cause habit is what turned
one dependent repo's worst misses into its strongest machinery.** Every
audit that repo runs exists because of one specific, recorded incident.

That gives the rule its own falsifiable test, which is the part worth
keeping. The audit that would have caught the originating incident is how
you check whether the root cause was actually found -- a guard that would
not have caught its own origin incident is theater, however reasonable it
looks.

The alternative failure is specific too. A repo that only fixes instances
relives its mistakes with new surface details: the systemic cause stays free
to fire again, and each recurrence looks novel enough that nobody connects
it to the last one.

The origin incident is load-bearing twice over, which is why the rule
insists it be recorded rather than summarised away. It tells a future reader
what the rule protects against, so the rule can be re-judged when the world
changes, and it calibrates proportionality.

## Install
A habit plus a review question. The habit: end any session in
which a mistake was caught with an explicit root-cause note and its
prevention, in the same change-set as the fix. The review question, for the
owner: "does this guard's rung (audit / dated rule / export) match the
failure's checkability?" Seed it retroactively: the next time an old mistake
class recurs, that is the origin incident for its rule.
