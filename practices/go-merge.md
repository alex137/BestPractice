---
slug:        go-merge
title:       "\"Go merge\" authorizes sync, confirm branch, commit, push, PR, and merge"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message carries the standing merge-authorization phrase"
gates:       ["merge"]
index_clause: "\"Go merge\" anywhere in the message: sync, name branch, commit, push, PR, merge"
checked_by:  null
defines:     ["Go merge"]
status:      active
in_force_at: null
supersedes:  ["merge-authorization-keyword"]
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08 -- moved up from his individual set to
  universal; loosened 2026-09-12, Morgan, after sessions began refusing the
  phrase he had just typed"
strength:    decided
---
## Rule
If the message you are answering tells you to `Go merge` --
case-insensitive, **anywhere in the message**, as its own line, as a whole
sentence, or as a clause inside a longer one -- treat it as authorization,
right there, to: **sync your local branch with origin, say out loud which
branch you are merging into, commit the pending work, push the branch, open
a pull request (or confirm one is already open), and merge it** -- using the
repo's usual conventions, without asking again first.

**The default is to act on it.** Nothing about the phrase's position, the
punctuation around it, or what was said before it changes the answer, and
you do not have to have announced that you are ready to commit first. Said
before you have mentioned committing at all, it means get ready and go.

**Say the target branch before merging, every time.** It is spelled out
here rather than left inside "usual conventions" because that is the step
whose silent failure is expensive: a merge into the wrong branch looks
identical to a correct one until somebody goes looking.

## Detail
"That was perfect. Go merge", "Go merge.", a lone line reading `GO MERGE`,
"go merge it and tell me what broke", and "when the check passes, go merge"
all count. What does not is the words being used about something else --
"let's go merge those two lists", "go check the logs, then merge the
report" -- where `merge` has its own object and is plainly not an
instruction about the work in front of you.

**Ask about the object, never about the phrasing.** The one question worth
stopping for is *which* pending work is meant, and only when several
unrelated branches are genuinely in play. Asking whether the words were
meant as the command produces exactly the interruption the command exists to
remove: if you can tell what would be merged, merge it.

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

**A trigger that has to be recognized cannot be fussy about how it is
typed.** Every condition attached to the phrase -- a required position in
the message, a preceding statement of readiness, a standing invitation to
ask when it reads ambiguously -- is one more way for a session to answer an
authorization with a question, which is the one failure this practice
exists to prevent. The strictness buys nothing back: the expensive mistake
is merging into the wrong branch, and the spoken-branch step in the Rule is
what guards that, not the shape of the trigger.

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

**Loosened 2026-09-12, on Morgan's decision**, after a run of sessions
began treating the phrase as something to qualify for rather than something
to act on: *"In the last hour, you have become much much stricter in
accepting a go merge. I don't like that."* Nothing in the wording had
changed. The file had sat untouched since the 2026-09-08 move, no source
carried an edit near it, and the whole repository's last commit before the
complaint was about an unrelated practice -- so the strictness was not new
text but the conditions the text had always carried, read tightly. Three
came out: the message-final position, the requirement that the session have
already said it was ready to commit, and the invitation to ask when the
phrasing read ambiguously. The branch-naming step, which is the part
actually protecting anything, was left exactly as it was.

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
appear somewhere in the message" -- both leave the identical commit and
merge. The
only place the distinction exists is the conversation, which no repo-scoped
script can see, and even there it is a judgment call about intent rather
than a signature to pattern-match.

What IS checkable is downstream and already covered: the merge target
(wherever a repository declares one) and the closing link to the merged pull
request's page, where the one-click delete-branch button lives.
