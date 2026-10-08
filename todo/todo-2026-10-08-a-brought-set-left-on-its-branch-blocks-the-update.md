---
slug:              todo-2026-10-08-a-brought-set-left-on-its-branch-blocks-the-update
kind:              manual
domain:            mechanism
severity:          null
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-08
closed:            2026-10-08
---
## What

Since 2026-10-07 a source clone on another branch is left where it is
rather than switched ([the branch-switch item](todo-2026-10-07-one-sets-update-moves-another-sets-working-branch.md)).
The first vendor round after that fix, run across three practice sets in
one session, showed the next rough edge: the individual and writing sets'
updates each stopped with "brought set precedent-shared-ladder: could not
be fetched ... so its rules are not in force for this sync", because the
ladder set's clone was on that session's own update branch. The clone was
on disk with its practices, so the resolver does read it; the message is
wrong on that point, and the stop is stronger than the situation needs.
Worked around by landing the ladder set's update first and putting its
clone back on `main`.

## Proposed

`brought_sets_step` treats a clone left on its branch the way
`ensure_source` already does (`_left_as_it_stands`): in force as it stands,
reported as a note naming the branch it was read from, never a call left
for the person. Only a brought set missing from disk stays a stop.

## How It Closes

Two sets updated in a row, the second bringing the first, each on its own
working branch: both updates end DONE, and the second's report names the
branch it read the first from.

## Notes

**Fixed 2026-10-08, as proposed** (Morgan: "LETS FIX"). A brought set that
`_sync_once` leaves on another branch, on disk with its practices, is
reported by `sources_from_brings` as in force, naming the branch it was
read from (`READ_ON_ITS_BRANCH`). Update Vendors lists it as its own step,
"brought sets on a working branch", and leaves nothing for the person. A
brought set missing from disk, or one that fails to fetch, is still a stop.
`check_update_never_fetches_the_repo_it_updates` builds the shape that held
the two updates, a real clone with practices on a branch named
`session-update`, and asserts: read as it stands with the branch named,
left on that branch, and reported as a step with nothing left. Planting the
old behavior fails the first of those.
