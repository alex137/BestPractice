---
slug:        cite-the-incident
title:       Conventions cite the incident that created them
tier:        on-demand
severity:    default
applies_to:  ["practices/**", "PRACTICES.md"]
occasion:    "writing a new convention or rule"
gates:       ["review"]
index_clause: "record the failure a rule prevents, inline with the rule"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 5
---
## Rule
When you write a rule, record what failure it prevents, inline.

## Detail

## Why
"Do X" invites relitigation and misapplication; "do X — we once lost
Y because Z" sticks, and lets a reader judge whether the rule applies to their
case. Rules without origin stories decay into cargo cult or get dropped.

## Story
**This practice had an empty Story until 2026-09-07, which is its own
best illustration.** The rule that exists to make every other rule carry
the failure it prevents did not carry one, and nothing flagged that for
weeks -- because the check that enforces it fires on authorship of a
*changed* Rule, and a section that was empty from the start is never a
change.

No single originating incident was recorded, and this Story does not invent
one; the reasoning is what was recorded. "Do X" invites relitigation and
misapplication, where "do X -- we once lost Y because Z" sticks, and lets a
reader judge whether the rule applies to their case at all. A rule without
its origin story decays in one of two directions: it becomes cargo cult, or
it gets dropped by somebody who cannot see what it was protecting.

The empty-Story episode adds one thing the reasoning did not have. A rule
about recording incidents needs a standing check over the whole catalogue,
not only a gate at the moment of writing, because the gap this rule guards
is most often created by a bulk landing that no later edit ever touches
again.

## Install
A writing habit, not a file. Enforced socially by example: every
rule in the instructions file carries its story.
