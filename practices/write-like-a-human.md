---
slug:        write-like-a-human
title:       Nothing you ship may sound like it came from an AI
tier:        resident
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing anything a person will read -- a document, a reply, a commit message"
gates:       ["reply"]
index_clause: "say the thing in your own words; unrewritten model output is output nobody thought about"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       2026-09-07
approved_by: "Morgan, 2026-09-07 -- merging that repository's `no-ai-voice` (the argument) and `write-like-a-human` (the rule) into one universal practice, deliberately as a short guiding point rather than a vendored ruleset"
---
## Rule
**Nothing you ship may sound like it came from an AI** — a document, a
chat reply, a commit message, a pull-request body. The tells: the
throat-clearing opener that circles before it lands, the "not just X,
it's Y" contrast, the summary nobody asked for, the even-handed survey
that takes no position, the caveat stack. **Say the thing, in your own
words, at the length it earns.**

Unrewritten model output is output nobody thought about — style is the
cheapest evidence a reader has that somebody did.

## Detail
This is a short guiding point on purpose, not a banned-word list. A word
that is the right word is the right word: "robust" about an estimator,
"delve" in a piece about mining. Contorting a sentence to dodge a term is
a worse tell than the term.

Register adapts; the rule does not. A contract, a filing, or an academic
paper is formal and still must not read as machine-generated — formality
is a dial, the tells are not on it.

The one place this bites hardest is the place easiest to forget: **the
reply**. A session that carefully rewrites a document and then answers in
default assistant register has shipped the thing this rule exists to
stop, which is why `gates: ["reply"]` puts the Rule in front of the turn
that writes it.

## Why
These were two rules saying one thing. `no-ai-voice` argued *why* — it
reads as nobody home, it erodes trust, and what you sound like is the one
claim a reader can check for free. `write-like-a-human` was the
operational half. Splitting an argument from its rule leaves the argument
un-actionable and the rule un-explained, and the two drift.

It is universal by the test `layered-practice-packs` sets: it holds in
any repository, about any writing, with no reference to a subject matter.
Nothing about it is specific to one team or one person.

## Story
2026-09-07, and the history is the argument for the shape this landed in.

the project's own prior notes repository held both halves. `no-ai-voice` sat in its essay on
building a company around AI as rule 11; `write-like-a-human` sat in its
"rules now testing" list as rule 5, and it did not state a rule at all —
it pointed at a long writing-style ruleset **vendored from a private
repository**, kept current by its own manifest, a weekly sync workflow
and a session-start freshness check.

That entire apparatus was removed the same day, on Morgan's instruction
that a private repository should not be vendored into a public-facing
project. The rule it left behind pointed at nothing, so the session
marked it *Withdrawn* — accurate, and wrong as a resting state. Morgan's
correction: these are the same point, it is still a best practice, it
should be in force **always**, and it wants "a simple, short point to
guide it, not my whole long repo on that."

So the dependency on that ruleset is what got retired, not the rule. What
is written above is short enough to sit in the resident block and be
loaded every session, which is what "always" has to mean mechanically —
an on-demand practice about how to write reaches a session only if the
session first thinks to ask.

**The check was attempted and refused, with evidence.** A tell-scanning
regex is the obvious mechanical check, so it was written and run against
this repository's whole tree before being rejected. It produced three
findings, and **all three were legitimate prose**: "the direction is not
an artifact of the key, but the exact gap could be"
([PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)), "A universal
candidate is not private, but the gate bans…"
([spec/SOURCES.md](../spec/SOURCES.md)), and "worth noting that the
failure mode here was *inventing* work, not missing it"
([spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md)). Three for three
false positives. `checkable-gets-checked` calls a check that fires on
correct work worse than no check, because it teaches the next session to
ignore the gate — and this one would have fired on nothing else.

## Install
No mechanical check, for the reason measured above rather than assumed:
the distinguishing property is whether a sentence was *thought about*,
and every proxy for that tested here flagged prose that had been. Being
`tier: resident` is what makes this bind without one — the Rule is in
every session's context from the start, and `gates: ["reply"]` puts it in
front of the turn most likely to forget it.

A repository this genuinely does not bind — one whose output is entirely
code or generated data, with no prose audience — exempts it in
`precedent.json`'s `not_binding` with a stated reason.
