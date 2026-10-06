---
slug:        no-duplication
title:       Don't duplicate a lower-precedence source
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A set rule is written in that set's own repository, which a consumer never edits, so no glob here can name it; the occasion index reaches it."
occasion:    "adding or reviewing a shared-set rule"
gates:       []
index_clause: "a rule that only restates universal gets dropped"
checked_by:  null
defines:     []
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan F, drafted 2026-10-05, moved from the shared set precedent-shared-repo-maintenance; merged in PR #880 on 2026-10-05"
strength: decided
---
## Rule
A shared or individual set exists to add to the universal catalogue or override it, not to restate it. A rule in one that only repeats something universal already establishes on its own -- same substance, no actual change in outcome -- gets dropped the next time it's touched: a restated rule is a second place for the same idea to drift out of sync with the first, for no benefit over leaving the universal text to stand alone.

## Detail


## Why
Precedence already lets a team rule override a universal one by slug; there is no separate need to also copy the universal rule's own text into the shared set just to have it nearby.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration. No incident was recorded for it, and none is invented here.

The argument is about drift rather than tidiness. A rule at this level that
only restates what universal already establishes -- same substance, no
change in outcome -- is not merely redundant; it is a second place for one
idea to be edited, and the two copies will not stay in step. Since there is
no benefit over letting the universal text stand alone, the duplicate is
pure downside, which is why the rule says to drop it the next time the file
is touched rather than to schedule a cleanup.

It bites at install time too: weaving a set's conventions into a target
repo's agent instructions means skipping any bullet whose substance that
repo's universal install already carries verbatim, rather than installing a
second copy of the same sentence.

## Install
No mechanical check: telling "only repeats something universal, same substance, no actual change in outcome" apart from a legitimate override or a genuinely additional rule requires comparing this set's rules against the universal catalogue's own semantics -- the universal catalogue lives in the public Precedent repo, not vendored here, and even with it in reach, substance-equivalence between two rules is a reading judgment, not a text match.

