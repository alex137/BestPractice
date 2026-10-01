---
slug:        consider
title:       "\"Consider\" is stage 1: decide how much plan the work needs, then make that much"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A phrase in a MESSAGE (\"Consider\", \"Promote 1\") -- stage 1 of the five-stage ladder, like promote's entry; no file path reaches it. Reached through the occasion index; no gate, since the plan it asks for comes before any file moment. Decided: 2026-09-29, when the practice landed."
occasion:    "a person says \"Promote\", \"Promote N\" or a stage word (\"Consider\", \"Act\", \"Debut\", \"Produce\", \"Make live\"), or asks to plan, build or move work up a tier"
gates:       []
index_clause: "stage 1: pick the plan size -- one line, Brainstorm, Plan it, Write it up"
checked_by:  null
defines:     ["Consider", "One-line plan", "Plan it"]
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
| **Plan it** | A written plan in the session, handed back as one paste-ready prompt (Detail, below). | Real work, clear enough to build in this session. |
| **Write it up** / **Spec it out** | A full report committed to the repository ([write-it-up](write-it-up.md)). | A detailed plan is needed: big or cross-session work, or anything someone else will pick up. |

**The session picks the size itself, without asking** -- from the context,
from how complex the work is, and from any guidance given in passing:
*"Consider this, it's a brainstorm"* settles it. The read-back names the
choice (*"Now Promote 1: Consider -- a one-line plan"*), so a wrong pick is
corrected in one word.

**The one-line plan is the usual answer.** A bigger plan than the work
needs is the failure this stage exists to avoid as much as no plan at all:
a document nobody needed is cost, not care.

## Detail
**Plan it, in full** (folded in from plan-it, 2026-09-30: it is this stage's middle size, and Morgan asked that it be recognized as one of Consider's sizes rather than kept as its own trigger).

**"Plan it" is the middle-sized plan** of Consider: more than
a [Brainstorm](brainstorm-holds-commits.md), far less than a
[Write it up](write-it-up.md). It is written in the session, never saved to
the repository -- work that spans sessions is Write it up's job -- and it
always contains:

1. **The steps**, numbered, in the order they will be done.
2. **The risks**: what could go wrong, and what each step could break.
3. **What "done" looks like**, concretely enough to check.
4. **What is out of scope**, so nobody builds it by accident.

**It is handed back as one paste-ready prompt**, so getting a second
session's opinion is one copy and one paste. The block follows
[fence-block-for-paste](fence-block-for-paste.md): it says where to paste
it -- a new session, the repository to root it in, what to attach -- opens
by naming the session that wrote it
([seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md)), and
asks the receiving session to critique the plan, not to carry it out.

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
