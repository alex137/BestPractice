---
slug:        timestamps-carry-offset
title:       Every timestamp carries its offset, and one module writes them all
tier:        on-demand
severity:    default
applies_to:  ["**/*.py", "**/*.sh", "precedent.json"]
occasion:    "writing code that stamps a date or a time into a file, a record or a document"
gates:       []
index_clause: "a stamp carries its offset; never a bare date.today()"
checked_by:  "tools/precedent_check.py"
defines:     ["declared fallback zone"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-09"
approved_by: "Morgan"
strength:    assented
---
## Rule
**A moment written into a file carries the offset it was written at, and
every emitter of one goes through a single module.** Never a bare
`datetime.date.today()`, `datetime.now()` with no zone, or an inline
`strftime` in a caller: each is a private copy of a policy, and each
silently resolves to whatever zone the machine happens to be on — which,
in a hosted container, is UTC.

The module resolves **whose** zone in a fixed ladder, most specific first,
and **its last rung is a real zone, never UTC-because-nobody-said**:

1. an explicit override in the environment;
2. the repository's own `identity.json`, when the repo *is* somebody's
   individual practice source;
3. that person's individual practice source's `identity.json`;
4. `TZ` in the environment;
5. the repository's **declared fallback zone** — `fallback_timezone` in
   `precedent.json`;
6. the engine's own last resort.

**The fallback is applied and never enforced**, and the two halves have
different reasons. Applied, because the alternative is not "no zone", it is
the container's UTC — so a person the project could not identify still
produces orderable records. Not enforced, because refusing somebody's
commit over a zone *they* never declared would block real work on a value
they never saw. Declaring a zone in your own `identity.json` is what turns
the applied default into a checked fact.

## Detail
**A date is a timestamp too, and it is the one people forget.**
`date.today()` looks zone-free and is not: it is computed in the machine's
zone, so for part of every day a container on UTC writes tomorrow's date
into a record somebody dated by hand as today. Route it through the module
like everything else.

**A field whose name already says UTC is not the failure this prevents.**
`generated_at_utc: 2026-09-09T16:53:36+00:00` is honest and orderable.
It still comes from the same module — one kind, one module
([one-formatter-per-quantity](one-formatter-per-quantity.md)) — but it does
not have to become local to be correct. What must never survive is a stamp
that *does not say* which of the two it is.

**Where each rung's value lives is a layering question, not a taste
question** ([layered-practice-packs](layered-practice-packs.md)). A
person's zone is person-level and belongs in their `identity.json`. The
fallback for a person the project could not identify is repo-level and
belongs in `precedent.json`, so an adopting repo sets its own without
editing vendored code ([registry-source-of-truth](registry-source-of-truth.md)).

## Why
**An unlabelled time is a lost fact, and no later reader can recover it.**
Two records say "Morgan 19:00" and "John 18:00" and nobody can order them
— not by looking harder, not by checking the file, not ever. Every other
formatting defect degrades a reader's experience; this one destroys
information at the moment of writing.

**The offset is what makes records from different people comparable at
all**, which is why the fallback is a real zone. UTC would also be
orderable if it were *chosen*; the state being replaced is UTC arrived at
by nobody configuring anything, which is indistinguishable from a genuine
UTC contributor and is wrong for whoever actually wrote the record.

**And this is a mechanism problem, not a care problem.** The wrong answer
is what a careful person gets by writing the obvious line, in every file,
forever. That is the shape of defect a module fixes and a reminder does
not ([durable-fix](durable-fix.md)).

## Story
**Origin.** 2026-09-09. Morgan, after the same wrong-offset problem had
surfaced repeatedly across sessions: *"I want to avoid timestamps that say
'Morgan 7pm' but then that's meaningless because there's another change
from 'John 6pm' and we don't know which was first because we don't know
their timezones"*, and — for the case where nobody's zone can be found —
*"if you can't find/get my timezone then use buenos aires timezone."*

**What the sweep found.** Fourteen call sites across `tools/` stamped
moments three different ways: `date.today()` (six sites, the container's
zone — UTC), `datetime.now(timezone.utc)` (five, honest but not the
person's), and one `utcfromtimestamp()`, which is both deprecated and
returns a naive datetime. Nothing in any output said which of the three it
was.

**Why it kept coming back.** The commit hook already resolved a person's
zone correctly, and deliberately refused to *apply* a zone it had merely
defaulted to — on the reasoning that changing a container's clock on a
guess is worse than a warning. That weighed the wrong pair: the
alternative to applying a default was never "leave the clock alone", it
was "leave it on UTC". Since the individual practice source is a private
repository a session is often refused access to, most sessions took that
branch, and every commit and every generated date came out `+0000`. The
same session that found this had already been bitten by the missing global
commit backstop, whose install gate is the identical
`declared`-versus-inferred distinction.

## Install
**Engine.** [tools/precedent_time.py](../tools/precedent_time.py) — the
ladder, plus `today()`, `now()`, `stamp()`, `stamp_iso()`, `compact()`,
`utc_iso()`, `from_unix()` and `date_from_unix()`. Run it directly
(`python3 tools/precedent_time.py`) and it prints the current moment **and
which rung answered**, because "declared in your identity.json" and
"nobody said, so the fallback" produce the same offset on a good day and
mean opposite things.

**The session half.** [.claude/hooks/commit-identity.sh](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/.claude/hooks/commit-identity.sh)
resolves the same ladder at session start, repoints the container's system
zone, and writes `TZ` into the harness `env` block — so `git`, `git merge`
and every tool that asks the clock get the right offset without anybody
retyping a `TZ=` prefix. Its `DEFAULT_TZ` and the engine's `FALLBACK_TZ`
are asserted equal by the check below; they cannot drift.

**Checked.** `tools/precedent_check.py --only timestamps-carry-offset`
fails on a bare `date.today()` / naive `datetime.now()` /
`utcnow()` / `utcfromtimestamp()` in any tracked `.py` outside the time
module itself, and on the three declared fallback values disagreeing.

**Related.** [one-formatter-per-quantity](one-formatter-per-quantity.md)
(this is that rule applied to the kind "a moment in time");
[volatile-rules-carry-dates](volatile-rules-carry-dates.md) (a date in a
document is the contributor's, not the agent's clock — this is the
mechanism that makes it so); [durable-fix](durable-fix.md).
