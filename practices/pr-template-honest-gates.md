---
slug:        pr-template-honest-gates
title:       A default PR template captures the living-doc gates — honestly, not mechanically
tier:        on-demand
severity:    default
applies_to:  [".github/pull_request_template.md"]
occasion:    "writing or filling out a pull-request description"
gates:       []
index_clause: "write the body from the diff; an unchecked box is fine"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 39
---
## Rule
Every dependent repo installs a default pull-request template
covering what changed, why, files touched, and the practices' own
living-document gates (scrub, MAP, TODO, GLOSSARY) as a checklist. The body
is written from the actual diff; a gate is checked only when it is actually
true for this change. An unchecked box, or a "not applicable" note, is a
normal and expected outcome — never a defect to paper over.

## Detail

## Why
A template with a fixed checklist is worth nothing the moment
filling it in becomes reflex: "N/A" typed into every box looks exactly like
verification happened and means nothing did. The template earns its place
only paired with an explicit instruction that unchecked boxes are fine — the
alternative trains exactly the behavior the checklist exists to catch.

## Story
No dated incident was recorded, and the rule is unusual in that it is
mostly a warning about its own mechanism.

**A template with a fixed checklist is worth nothing the moment filling it
in becomes reflex.** "N/A" typed into every box looks exactly like
verification happened and means nothing did -- and it looks that way to
reviewers too, which is what makes it worse than an absent template rather
than merely equal to one.

So the explicit permission is not politeness; it is the load-bearing half.
The template earns its place only paired with a stated instruction that an
unchecked box, or a "not applicable" note, is a normal and expected outcome.
Without that, the form trains exactly the behavior the checklist exists to
catch, because a reader who believes every box must be ticked will tick
every box.

The other half -- write the body from the actual diff -- exists for the same
reason one level up: a template is a layout to populate from what happened,
never a set of prompts to answer plausibly.

## Install
[templates/pull_request_template.md.template](../templates/pull_request_template.md.template)
→ `.github/pull_request_template.md` — installed the same way as `AGENTS.md`
(§1), propagated to existing installs the same way (§2). The "write from the
diff, unchecked is fine" instruction lives in
[templates/AGENTS.md.template](../templates/AGENTS.md.template) so every
session opening a PR sees it, not just the template itself.
