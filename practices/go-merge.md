---
slug:        go-merge
title:       "\"Go merge\" authorizes sync, confirm branch, commit, push, PR, and merge"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message ends on the standing merge-authorization phrase"
gates:       ["merge"]
index_clause: "\"Go merge\" alone at the end: sync, name the branch, commit, push, PR, merge"
checked_by:  null
defines:     ["Go merge"]
status:      active
in_force_at: null
supersedes:  ["merge-authorization-keyword"]
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08 -- moved up from his individual set to universal"
---
## Rule
If the message you are answering, at a point where you have said you are
ready to commit (or ready to commit and merge), ends with `Go merge`
standing alone as its own sentence -- case-insensitive, whether that is the
whole message on one line or the last sentence of a longer one, set off by
ordinary sentence-ending punctuation -- treat it as authorization, right
there, to: **sync your local branch with origin, say out loud which branch
you are merging into, commit the pending work, push the branch, open a pull
request (or confirm one is already open), and merge it** -- using the repo's
usual conventions, without asking again first.

**Say the target branch before merging, every time.** It is spelled out
here rather than left inside "usual conventions" because that is the step
whose silent failure is expensive: a merge into the wrong branch looks
identical to a correct one until somebody goes looking.

## Detail
"That was perfect. Go merge", "Go merge.", and a lone line reading
`GO MERGE` all count. "Let's go merge those two lists" and "go check the
logs, then merge the report" do not -- there the words are part of a longer
sentence rather than standing alone as the last one.

**Where it is ambiguous, ask.** If the trailing phrase might be ordinary
sentence meaning rather than the keyword, or if several pending items leave
it unclear what "merge" would even apply to, do not assume.

**This is shorthand for an authorization, never a new kind of permission.**
It says the person has approved *this* merge; it does not widen what may be
merged, and it does not survive into the next one. Where a repository
restricts a particular branch -- a release branch, a pinned integration
branch, a `main` behind review -- that restriction still holds, and
`Go merge` with no branch named means the branch the repository's own rules
say routine work lands on.

## Why
A standing phrase costs the person two words instead of a re-explanation in
every session, and it survives the session that heard it. The alternative is
being asked the same question across sessions forever, which is the exact
annoyance it exists to remove.

**Universal rather than per-person, and that reverses a 2026-09-07
decision.** The rule this supersedes told every adopting repository to go
adopt a merge keyword of its own, which is a preference dressed as a
practice, and it was retired for that. Naming ONE phrase and shipping it
with the engine is a different thing: Morgan, 2026-09-08 -- *"we should have
our own commands we use for people who live in our universe."* An adopter
gets a working vocabulary out of the box instead of a homework assignment,
and a session moving between repositories reads the same word everywhere.

## Story
It began as one person's shorthand, from typing `go` / `merge` /
`PR & merge` session after session. Revised 2026-09-04 after two confusions
surfaced in one conversation: a session's local branch was badly stale
against origin, and -- separately, already on record -- a pull request had
once merged silently into the wrong branch. Neither was caused by the
keyword, and both came down to the same gap: a Rule that says "using the
repo's usual conventions" trusts the sync-and-correct-branch check
invisibly. The three triggers collapsed into one phrase (`go` and `merge`
are too common as ordinary words to trust alone), and the sync/branch
confirmation became an explicit, spoken step.

Revised again 2026-09-05 to spell out push and pull request as their own
steps rather than leaving them inside "usual conventions" -- so the full
chain is visible, not just its two ends.

**Moved to universal 2026-09-08, on Morgan's decision**, from his private
individual set. The move is also what makes the phrase readable at all by a
session that has not attached a private source -- which had already happened
once: a session followed an instruction to go ask what "Go merge" meant,
generating the precise interruption the phrase exists to prevent, while the
definition sat in a repository nobody had fetched.

## Install
No mechanical check, and not for lack of trying: this governs how a chat
message is *read*, not any property of a diff, a commit, or the tree.
Nothing left behind afterwards distinguishes "recognized the authorization
and merged" from "merged on its own initiative while those words happened to
be the last ones typed" -- both leave the identical commit and merge. The
only place the distinction exists is the conversation, which no repo-scoped
script can see, and even there it is a judgment call about intent rather
than a signature to pattern-match.

What IS checkable is downstream and already covered: the merge target
(wherever a repository declares one) and the closing link to the merged pull
request's page, where the one-click delete-branch button lives.
