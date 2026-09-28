---
slug:        tier-branch
title:       "\"Tier branch\" names one rung of the pre-staging -> staging -> main ladder"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Tier branch\", or asks which branches are the tiers"
gates:       []
index_clause: "pre-staging, staging or main -- plus staging's old name and Promote's lock"
checked_by:  null
defines:     ["Tier branch", "Landing branch"]
command:     {"Tier branch": "One of the three branches work climbs through -- pre-staging, then staging, then main -- or one of the two that travel with them: staging's old name precedent-beta-v01 and Promote's lock branch precedent-promote-lock. Never offered for deletion."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "Morgan, 2026-09-28 -- after asking what \"a tier branch for deletion\" meant: 'Add \"Tier branch\" to the list of non-actionable vocabulary words.'"
strength:    decided
---
## Rule
**"Tier branch" is this project's word for one rung of the branch ladder**
([spec/BRANCH_TIERS_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/BRANCH_TIERS_PLAN.md)):
`pre-staging`, where work lands; `staging`, which a Promote moves it into;
and `main`, the top. Two more branches count as tier branches because they
exist only to serve the ladder: `precedent-beta-v01`, staging's name before
2026-09-25, kept so an install still pinned to it takes its updates; and
`precedent-promote-lock`, which a Promote holds so two sessions never
promote at once. `tier_branches()` and `LOCK_BRANCH` in
[tools/precedent_branches.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_branches.py)
are the list.

**Saying it does not itself trigger an action.** It is a word to look up,
like [primary-branch](primary-branch.md). What it carries is one standing
consequence stated elsewhere: a tier branch is never offered for deletion,
by any route ([branch-delete-links](branch-delete-links.md) rule 4, and
[very-deep-check](very-deep-check.md)'s branch sweep).

## Why
The word reached a person before it had a definition: a reply said the very
deep check "never offers a tier branch for deletion", and the next message
had to ask what that meant. Writing it down once, with a `command:` entry,
puts it in the [vocabulary](vocabulary.md) listing, so the next reply that
uses it points at an answer instead of a question.

## Story
Coined 2026-09-28. Fixing the very deep check for the branch tiers, a
session used "tier branch" as shorthand for the branches the sweep must
never offer to delete. Morgan asked what it meant, got the answer, and asked
for it to join "Primary branch" as a vocabulary word that defines rather
than acts.

## Install
No check on the answer, for the reason [vocabulary](vocabulary.md) gives:
this defines a word, it does not check that a session used it. The listing
is generated from the `command:` field (`python3 tools/precedent_vocabulary.py`),
and `python3 tools/build_views.py` regenerates the glossary row.
