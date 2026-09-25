---
slug:        install-declares-its-scope
title:       This repo's install-path documents declare what an install defers and what it never defers
tier:        on-demand
severity:    default
applies_to:  ["INSTALL.md", "SETUP.md"]
occasion:    null
gates:       []
index_clause: "the install path says what it defers and what it never defers"
checked_by:  "tools/checks/check_install_declares_its_scope.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "Morgan, 2026-09-14, choosing a check over a universal practice"
---
## Rule
[INSTALL.md](https://github.com/alex137/BestPractice/blob/staging/INSTALL.md)
and [SETUP.md](https://github.com/alex137/BestPractice/blob/staging/SETUP.md)
— the two documents an install, upgrade or migration is driven from — each
carry a section declaring that **an install does the essentials and stops**,
and that section names **both halves**: what is deferred, and what is never
deferred as "polish".

And **every mention of `local/practices/project-voice.md` or
`local/practices/project-visual-identity.md` in either document sits beside
a deferral marker** — optional, out of scope, ships as a skeleton, or a
plain "do not". A mention with no marker is an install being told to fill
them in.

**This practice has no `occasion` on purpose.** It is reached by its
`applies_to` when somebody edits either document, and by its check on every
run. An occasion-index line would cost every session in every adopting repo
about 31 tokens to reach a rule that fires only during an install — and an
installing session is already reading these documents, because they are the
procedure it is following.

## Detail
The check asserts three things per file, and none of them grades prose:

1. A heading whose text contains **essentials** — the scope declaration
   exists at all.
2. Somewhere in the file, a phrase naming the **counterpart**: what is never
   deferred. Without it the rule is an excuse rather than a scope.
3. Every paragraph naming `local/practices/project-voice.md` or
   `local/practices/project-visual-identity.md` also carries one of the
   deferral markers.

Assertion 3 is written as a **positive** requirement for a reason. The
obvious form — grep for "walk them through" — fires on SETUP.md's own
correct text, which says *do not walk them through the sections*. A check
that cannot tell an instruction from its negation is worse than none.

## Why
The rule this guards is generic, and it is deliberately **not** a universal
practice: the universal catalogue reaches a session through the occasion
index, which costs tokens in every session everywhere, and an installing
session is the one population that is already reading INSTALL.md. Prose in
the runbook is the cheaper channel and the equally forceful one.

What prose cannot do is stop a later session quietly putting the walkthrough
back. That is what this check is for — the specific regression, at the
specific two files, for no context cost at all.

## Story
2026-09-14. Morgan read the guided install and found it walked every
administrator through `VOICE.md`'s sections and asked whether a brand
guideline existed — on the day they knew least about Precedent, before the
essentials had landed. The fix was to cut both from the install path and
state the scope rule once in INSTALL.md.

The rule was first raised as a universal candidate, [issue
#318](https://github.com/alex137/BestPractice/issues/318). Morgan pushed
back twice: once that a rule used in one place is a poor fit for a
catalogue, and once asking whether anything had more force than a TODO item.
Both pushes were right, and the second reframed it — the session had been
weighing reach and load cost and never force.

The measurement that settled it: the occasion index is 3,283 tokens across
103 lines, so a practice costs about 31 tokens in every session, forever,
while AGENTS.md sat at 11,545 against a 12,000 ceiling that three reduction
passes had ratcheted *down*. A check costs nothing until it fails, and
`tools/build_views.py` skips any practice with no `occasion` from the index
entirely — which is what makes this shape free.

**Amended 2026-09-17**, when `VOICE.md` itself stopped being a root document:
its rule-shaped content (voice target, audiences, project vocabulary,
departures) became the repo-local practice
`local/practices/project-voice.md`, reached through the occasion index
rather than sitting at the root until someone opened it — see
`templates/local-practices/project-voice.md.template`'s own header. The
essentials-only deferral this practice guards did not change; only the
file's name did, so the check and its fixtures were updated to scan for
the new one.

**Amended 2026-09-22**, when `STYLEGUIDE.md` followed the same path: its
content stayed data (colors, fonts, logo paths), never a rule, but a
repo-local practice is the better home for project data too — reached
through the same occasion-index channel rather than a bare root file
nobody happens to open. It is now
`local/practices/project-visual-identity.md`, instantiated from
`templates/local-practices/project-visual-identity.md.template`. The check
and its fixtures were updated the same way the 2026-09-17 amendment updated
them for `VOICE.md`.
