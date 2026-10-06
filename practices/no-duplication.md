---
slug:        no-duplication
title:       "A rule lives in one place: another source adds to it, never repeats it"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A set rule is written in that set's own repository, which a consumer never edits, so no glob here can name it; the occasion index reaches it."
occasion:    "adding or reviewing a set's rule, or one that another source already has"
gates:       []
index_clause: "never repeat another source's rule; add to it in a practice of your own"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan F, drafted 2026-10-05, moved from the shared set precedent-shared-repo-maintenance; merged in PR #880 on 2026-10-05. Tightened 2026-10-06, Morgan (strength: decided): \"rules should not be repeated, but supporting repos can have additions for them\""
strength: decided
---
## Rule
**A rule lives in exactly one place.** A shared or individual set never carries a copy of a rule another source already has -- not to restate it, and not to change a few of its lines. **What a set wants to add goes in a practice of its own that holds only the addition**, names the rule it adds to, and says plainly any one point it changes. A copy that exists today is cut down to that addition and marked `deduplicated` the next time it is touched.

## Detail
**What an addition looks like.** Its own slug, named for the rule and the set (`prompt-please-on-the-ladder`); the same occasion as the rule it adds to, so the two load together; and a first line that says so -- *"Adds to `prompt-please`, for people who bring the ladder:"* -- followed only by what the set adds. Where it changes a point of the rule rather than adding one, it quotes the point it replaces and gives its own; everything else is left to the rule, which it never restates.

**Why not override.** Precedence lets a set's practice replace a universal one by slug, and that is how the copies came about: a set wanting a few different lines copied the whole rule to get them. A whole copy goes on overriding the rule it copied after the rule changes, so every later edit has to be made twice, and the copy that was not edited quietly wins for everyone who brings the set.

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

**2026-10-06: no copies at all.** Four practices -- prompt-please, the-boildown, vendor-update-runbook and very-deep-check -- lived as full copies in both universal and the ladder set, the ladder's overriding universal's to change a handful of ladder sentences. Every edit had to be made twice, and in one day three of the four were missed on the first pass; a check added on 2026-10-05 only named the copies, in universal, after the change. Morgan, asked why one was repeated: *"Shouldn't all Ladder type commands be only in Ladders?"*, and then the rule: *"rules should not be repeated, but supporting repos can have additions for them."* The rule now forbids the copy outright, says what an addition looks like, and the `no-duplication` check refuses a set's active copy of a practice its universal source has active. The four were split the same week: universal keeps each rule, the ladder keeps only its additions.

## Install
Checked mechanically by [tools/precedent_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py)'s `no-duplication`, in every practice set: an active practice whose slug is also active in the set's declared universal source is refused, with the way out named. It cannot see a rule restated under a different slug, or one set copying another set's rule -- telling a restatement from a genuine addition is a reading judgment, which stays this rule's to make. A set that says it is retired is passed over, since its copies leave with it.
