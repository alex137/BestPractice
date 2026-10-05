---
slug:        revert-needs-no-trailer
title:       A revert needs no Session trailer
tier:        on-demand
severity:    advisory
applies_to:  ["**"]
applies_to_why: "Committing a revert is a moment, not a file; the occasion index reaches it, and so does the session-trailer check that would otherwise flag the commit."
occasion:    "committing a revert, or a trailer check flags one"
gates:       ["push"]
gates_why:   "The push check's trailer check already exempts a revert while this practice is in force, so a session that never sees this rule loses nothing: it adds a trailer, which the Rule calls welcome. The push gate prints it where a trailer is at issue. index_required: false records that judgment: Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: assented -- one yes over a batch; corrected 2026-10-05)."
index_clause: "a revert commit may leave out the Session: trailer"
index_required: false
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "pending PR review -- drafted 2026-10-05 by Morgan F, moved from the shared set precedent-shared-working-style"
strength: decided
source_practice_number: null
---
## Rule
**A revert commit may leave out the `Session:` trailer** that
`session-trailer` (universal) asks for on every other commit. A revert is
`Revert "<subject>"` with `This reverts commit <sha>.` in its body -- what
`git revert` and GitHub's revert button write. Adding the trailer is still
welcome; it is simply not required.

## Detail
The exemption covers reverts only. A commit that undoes something by hand,
with its own message, is new work and still carries the trailer.

The trailer check in the repository-maintenance set honours this practice
only where it resolves in force: it asks the engine's own resolver, so a
repository whose declared sets do not include this one keeps requiring the
trailer on reverts.

## Why
A revert's reason is the commit it names, and the trailer on that commit
already leads back to the session that made the change being undone. Asking
for a second link on the undo adds friction at the moment someone is
backing out of a mistake quickly.

## Story
2026-09-29, Morgan, while approving the change that made the trailer check
judge only what a push carries: *"I think we should update the 'Session'
trailer rule to say that it is okay if reverts don't have it ... And I think
this should be in the working-style repo, maybe Alex or others don't want to
include that."* So the exemption lives in this set, which a team declares
by choice, rather than in the universal rule everyone gets.

**Push gate, and off the occasion index, from 2026-10-01.** The reduction pass for precedent-individual's session-start file counted this among the lines a mechanical check already covers at push: `check_session_trailer.py` skips reverts while this practice is in force, so the line in every session's index bought nothing. Morgan (strength: decided): *"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)"*

## Install
No check of its own: the trailer check reads whether this practice is in
force and skips reverts when it is.
