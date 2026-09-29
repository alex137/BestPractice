---
slug:        plan-it
title:       "\"Plan it\" writes a plan in the session and hands it back as one paste-ready prompt"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Plan it\", or Consider picks a middle-sized plan"
gates:       []
index_clause: "a written plan in the session, as one paste-ready prompt for a second opinion"
checked_by:  null
defines:     ["Plan it"]
command:     {"Plan it": "Write a plan in the session -- numbered steps, the risks, what \"done\" looks like, and what is out of scope -- and hand it back as one prompt ready to paste into another session for its critique. Nothing is saved to the repository."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-29"
approved_by: "Morgan, 2026-09-27 -- \"maybe another option in the middle, a new word we can define, \\\"plan it\\\"\"; 2026-09-28 -- not saved, and \"it should be given in a prompt so that it is very easy to copy-paste that prompt to another session to get its feedback\""
strength:    decided
---
## Rule
**"Plan it" is the middle-sized plan** of [Consider](consider.md): more than
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
Between "think out loud" and "commit a report" there was nothing: real work
that needed its steps written down either got a document nobody would read
again or no plan at all. A plan written as a prompt also invites the review
it most needs -- another session reading it cold.

## Story
Named 2026-09-27 by Morgan as the middle option Consider can choose. On
2026-09-28 he agreed it should not be saved, and asked that it always come
as a prompt so a second session's feedback is one paste away.

## Install
Nothing to install. Whether a plan covered its four parts is a judgment.
