---
slug:              todo-2026-10-07-one-sets-update-moves-another-sets-working-branch
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-07
closed:            null
---
## What

Update Vendors in one practice set can switch another set's checkout off
the branch a session is working on. On 2026-10-07 a session updating three
sets one after another made a working branch in each, then ran
`precedent_update.py` in the individual set first. Its brought-sets step
refreshes the sets the individual brings, the ladder set among them, and
found the ladder clone clean on that working branch. Because the clone was
made by the bootstrap (it carries the clone marker), `_sync_once` checked
out `main` there and pulled. The ladder set's own update then ran on
`main`, and its commit landed on local `main`. Nothing reached the remote:
the push of the working branch said "Everything up-to-date", and opening
its pull request failed with "No commits between", which is how it was
noticed. Repaired by hand: the commit was cherry-picked onto the branch and
local `main` reset to `origin/main`.

The self-skip added earlier the same day (`sources_from_brings(skip=)`)
covers only the repository being updated, and `_session_working_trees()`
knows only the project directory, which in a session rooted above its
repositories is none of them.

## Proposed

Two ways, not yet chosen:

1. **A marked clone off its pinned branch is reported, never switched**,
   the way an unmarked one already is. A tool-made clone left on another
   branch then needs a person to move it back, and says so.
2. **`precedent_update.py` refuses to start on a tier branch** (`main`,
   `staging`, `pre-staging`): an update lands through a working branch.
   Catches the symptom wherever it comes from, and leaves the switch
   itself in place.

## How It Closes

Updating two sets in a row, each on its own working branch, leaves both on
those branches, shown by a harness case that does exactly that.
