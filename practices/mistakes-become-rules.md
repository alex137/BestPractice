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
approved_by: "BestPractice (pre-fork). Extended 2026-09-12, Morgan F, relayed
  through a scheduled instruction to make \"prefer strengthening an existing rule\"
  operational -- the catalogue lookup in the proportionality guard. That extension
  was decided; the practice's original pre-fork approval stays unmarked,
  permanently, per decision-strength's no-backfill line."
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

**Before minting a rule at any level, search the universal catalogue for its
subject and say what the search returned.** "Prefer strengthening an existing
rule" assumes the existing rule is visible, and it often is not: a practice
source carries its own level's `practices/` only, so a set that resolves no
sources never sees universal text at all, and the rule you are about to
duplicate is invisible from inside the repository you are writing in. Search by
subject *and* by mechanism ([search-by-purpose](search-by-purpose.md)) — a clone
of the upstream catalogue on disk is enough, with nothing attached — and report
the result either way: **the slug you are extending, or that the search found
nothing.** Unsearchable is not the same as absent, and neither is silence.

**This is a lookup, not a meditation** — one search, one line. A session that
cannot reach a catalogue to search says that, in those words, and the rule it
writes is marked as written blind.

## Detail
**The lookup is aimed at one specific blindness, and it is structural rather
than careless.** The rungs above assume a session can see what the catalogue
already says. A repository that resolves no practice sources cannot: its own
`practices/` directory holds its own level and nothing else, so every universal
rule is absent from disk, absent from the loader's resident block, and absent
from the occasion index — and *nothing says so*. The session is not ignoring a
rule it read; it is writing into a gap it has no way to notice. **That is why
the guard has to be a required search with a stated result, not a preference.**
An unstated preference is discharged by feeling like you checked.

**What the search is for is the subject, not the wording.** The duplicate that
actually gets written never repeats an existing rule's phrasing — it arrives as
prose about the day's own problem, in the day's own vocabulary. So search by
what the rule is *about* and by the mechanism it names, and search the whole
catalogue rather than the neighbours you would expect
([search-by-purpose](search-by-purpose.md)).

**Verifying a rule is a different act from verifying a fact, and a session that
does the second will believe it did the first.** Checking every factual claim
against upstream is what a careful session does all day; it leaves the
catalogue's *rules* unread, because a rule is not a claim about the world that
some document will contradict. Nothing failed in the incident below except
that one step, and that session had been unusually careful.

**Where the rule finally goes is a separate question**, answered by
[layered-practice-packs](layered-practice-packs.md) — the lookup tells you
whether a rule already exists, not which level should hold the one you write.

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

**The lookup clause has a dated incident of its own: 2026-09-12.** A session
working in a private team practice source fixed a real defect, then wrote eight
operational rules about running a fleet of sessions into that set's own
instructions file and merged them. Most of the material was **already at universal**, which is
verifiable from here: [spawn-session](spawn-session.md) landed 2026-09-11 and
already required naming the repositories the work must read, write or push to
and comparing them against the ones the session holds — and its Detail already
cited `add_repo` refusing a cross-owner attach, which was one of the eight.

**The cause was not carelessness, and that is the whole reason this clause
exists.** That source declares no sources and materializes nothing into itself,
so universal practice text never reached it. Its own run of this engine's
mechanical checks is reported at **12 passed and 42 skipped, every skip the same
cause** — the repository carries no practice file of the slug each check is keyed
to — a figure recorded in
[very-deep-check](very-deep-check.md)'s Pass 2 as well. *(Reported, not
verified here: cross-owner attaches are refused, so that source cannot be read
from this repository at all.)* The session had a readable clone of the upstream
catalogue in its scratchpad the whole time and never grepped `practices/`
before writing rules. **It verified every factual claim it made against
upstream that day and never verified a rule against upstream's catalogue.**

By this practice's own rungs it stopped at (b) — a written rule, dated,
carrying its incident — and skipped (c), *if the lesson is generic, export it*.
That is the consumer-template-only shape one level up, landing on the same day
as [fix-the-original](fix-the-original.md), which exists to prevent exactly
that shape.

## Install
A habit plus a review question. The habit: end any session in
which a mistake was caught with an explicit root-cause note and its
prevention, in the same change-set as the fix. The review question, for the
owner: "does this guard's rung (audit / dated rule / export) match the
failure's checkability?" The habit has a second half since
2026-09-12: **the note names the catalogue search and its result** — the slug
being extended, or that the search found nothing — which is one `grep` over
`practices/` and one line of prose. Seed it retroactively: the next time an old mistake
class recurs, that is the origin incident for its rule.
