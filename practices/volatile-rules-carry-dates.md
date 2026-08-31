---
slug:        volatile-rules-carry-dates
title:       Volatile rules carry their dates
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing a rule that depends on the outside world"
gates:       []
index_clause: "a rule about the outside world carries its date, inline"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 16
---
## Rule
A rule whose truth depends on the outside world — the behavior of
an external platform, an algorithm someone else changes, a tool quirk, a
price — carries an inline date: *as of `<date>`* when adopted, updated to
*verified `<date>`* whenever a session reaffirms it still holds. Optionally
add a review-by cadence for rules in domains known to shift. Stable internal
conventions don't need this; their origin story (practice 5) is enough.

## Detail
Three corollaries. **The date is the contributor's, not the session's:**
an agent stamping a date uses the human contributor's local calendar date
— the date they experienced when the fact was true or the decision was
made — not the agent session's system clock. The two disagree by a full
day near midnight in most timezones, and an agent's clock is often UTC or
otherwise unaware of where the contributor sits; ask when it isn't already
clear from context rather than defaulting to the session's own date.
**Durable rules earn a record, not just a date:** for a
rule whose age is its authority, capture the tenure and the exception
history inline — *in effect since `<date>`; N exceptions in that time, each
under `<circumstances>`* — because that survival record is institutional
memory that otherwise lives only in people's heads, and it is exactly what
tells a reader how seriously to take the rule. **Rules about model behavior
are the most volatile class of all:** a rule that encodes "the agent's
model handles X this way — route/decide/format accordingly" breaks
silently when the model is upgraded under you, so it carries not just a
date but the model it was verified against — *verified `<date>` on
`<model>`* — and a model change is itself a re-verify trigger, not a wait
for symptoms.

## Why
Age means opposite things in different domains. A convention that
has survived years of internal use is battle-tested; a rule about an
external platform that has sat untouched for a year may describe a world
that no longer exists — teams whose whole craft is tracking a
constantly-retuned external algorithm learn this the hard way, and their
hardest-won rules decay the fastest. The date is what lets a reader apply
the right lens. And it must be **inline**: version control does timestamp
every line, but sessions read file *content*, not commit metadata — in a
repo-is-the-memory system, a date that isn't in the text effectively
doesn't exist for the session reading the rule.

## Story

## Install
A writing habit with a natural audit extension (practice 6):
tag rules with a review-by date or a volatility marker and a small script
can flag overdue ones — the drift check's shape, applied to time instead of
content. The environment-gotchas section (practice 4) is the most
decay-prone rule set most repos have; date its entries first.
