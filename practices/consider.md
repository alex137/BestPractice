---
slug:        consider
title:       "\"Consider\" is stage 1: decide how much plan the work needs, then make that much"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A phrase in a MESSAGE (\"Consider\", \"Promote 1\") -- stage 1 of the five-stage ladder, like promote's entry; no file path reaches it. Reached through the occasion index; no gate, since the plan it asks for comes before any file moment. Decided: 2026-09-29, when the practice landed."
occasion:    "a person says \"Consider\" or \"Promote 1\", or asks to plan before building"
gates:       []
index_clause: "stage 1: pick the plan size -- one line, Brainstorm, Plan it, Write it up"
checked_by:  null
defines:     ["Consider", "One-line plan"]
command:     {"Consider": "Stage 1 (Promote 1): decide how much planning the work needs and do that much -- a one-line plan for a small change, a Brainstorm, a Plan it, or a full Write it up -- and say which.", "Plan": "The same as **Consider**."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-29"
approved_by: "Morgan, 2026-09-27/28 -- the five stages (spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md); \"You should choose, based on the context, the complexity, and also, I will sometimes give you verbal guidance\"; on the one-line plan: \"Very, very, very important.\""
strength:    decided
---
## Rule
**Consider is step 1 of the five-stage ladder ([promote](promote.md), [the plan](https://github.com/alex137/BestPractice/blob/staging/spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md)): before building, decide how much plan
the work deserves, then make exactly that much.** Four sizes, lightest
first:

| Size | What it produces | When |
|---|---|---|
| **One-line plan** | One sentence in the reply: what will change and where. Then straight to [Act](act.md). | Tiny changes -- a typo, a link, a one-line fix. Most work. |
| **Brainstorm** | Think it through in the session and write nothing ([brainstorm-holds-commits](brainstorm-holds-commits.md)). | The idea itself is still open. |
| **Plan it** | A written plan in the session, handed back as one paste-ready prompt ([plan-it](plan-it.md)). | Real work, clear enough to build in this session. |
| **Write it up** / **Spec it out** | A full report committed to the repository ([write-it-up](write-it-up.md)). | A detailed plan is needed: big or cross-session work, or anything someone else will pick up. |

**The session picks the size itself, without asking** -- from the context,
from how complex the work is, and from any guidance given in passing:
*"Consider this, it's a brainstorm"* settles it. The read-back names the
choice (*"Now Promote 1: Consider -- a one-line plan"*), so a wrong pick is
corrected in one word.

**The one-line plan is the usual answer.** A bigger plan than the work
needs is the failure this stage exists to avoid as much as no plan at all:
a document nobody needed is cost, not care.

## Why
Planning was optional and invisible: a session either started building or
wrote a report, with nothing in between and nothing said about which. One
named step with four sizes makes the choice deliberate and cheap -- and for
a person whose own set requires it, makes sure it happens at all.

## Story
Coined 2026-09-27 with the rest of the ladder. Morgan first framed it as
choosing between a brainstorm and a write-up, then added the middle ground
(Plan it) and, on the session's push, the one-line plan for tiny changes,
which he called "very, very, very important". On 2026-09-28 he settled that
the session chooses the size itself.

## Install
Nothing checks it: whether a plan fit the work is a judgment. A person's
individual set may require that Consider comes before any build.
