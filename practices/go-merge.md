---
slug:        go-merge
title:       "\"Go merge\" -- and \"Approved\" -- authorize sync, confirm branch, commit, push, PR, and merge"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message carries a standing merge-authorization phrase"
gates:       ["merge"]
index_clause: "\"Go merge\"/\"Approved\": sync, branch, commit, push, PR, merge; blocked hands off"
checked_by:  null
defines:     ["Go merge", "Approved"]
command:     {"Go merge": "Save the work, publish it, and tell you where it went — without asking anything further.", "Approved": "The same as **Go merge**: save the work, publish it, and tell you where it went."}
status:      active
in_force_at: null
supersedes:  ["merge-authorization-keyword"]
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08 -- moved up from his individual set to
  universal; loosened 2026-09-12, Morgan, after sessions began refusing the
  phrase he had just typed; extended 2026-09-13, Morgan, who raised the
  blocked-step handoff himself out of a refusal he had just hit; second phrase
  added 2026-09-13, Morgan -- \"if I say 'approved', that also means the same as
  go merge\""
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

**`Approved` means the same thing.** Said of the work in front of you --
as its own line, as a whole sentence, or as a clause accepting what you just
proposed or showed -- it carries the identical authorization, the identical
chain, and the identical branch-naming step. There is no weaker reading of
it: it is not "noted", it is not "go ahead and I will merge it later", and it
does not become a question about whether he meant the command.

**Say the target branch before merging, every time.** It is spelled out
here rather than left inside "usual conventions" because that is the step
whose silent failure is expensive: a merge into the wrong branch looks
identical to a correct one until somebody goes looking.

**A step you cannot perform hands off; it does not come back as a
question.** If the push, the pull request or the merge is refused because
this session cannot reach the repository -- a cross-owner `add_repo`
refusal, no push access, a repository nobody attached -- **the
authorization is still good and it travels with the work.** Run
[spawn-session](spawn-session.md) on the spot: wake a live session that
already holds that repository, or, where none does, create one seeded with
the steps that are left, and put the link in the reply. **Finish everything
this session can do first** -- sync, commit, push where the push works --
so only the residue moves. Reporting the refusal and stopping there is the
one wrong answer.

**What the receiving session may then DO with the relayed phrase is
[relayed-authorization](relayed-authorization.md)'s**: it merges only where
the person's own `identity.json` says they accept relays, and otherwise stops
at the pull request. So a handoff can end with the work finished and the
merge still waiting on one word said in the other window -- that is the
declaration's absence, not a failed relay, and the reply says which word and
where.

## Detail
"That was perfect. Go merge", "Go merge.", a lone line reading `GO MERGE`,
"go merge it and tell me what broke", and "when the check passes, go merge"
all count. What does not is the words being used about something else --
"let's go merge those two lists", "go check the logs, then merge the
report" -- where `merge` has its own object and is plainly not an
instruction about the work in front of you.

**`Approved` has the same shape and one more way to be about something
else, because it is an ordinary adjective as well as a verb.** "Approved.",
"Approved -- ship it", "that's approved, go" all count. What does not is the
word modifying a noun that is not the work in front of you -- "the approved
plan of record", "Alex has not approved that yet", "an approved practice
source" -- or a question about approval rather than a grant of it, "has this
been approved?". **The test is the same one the rest of this file uses: if
you can tell what would be merged and the word is being said about it,
merge it.** A message that says `approved` about work you have not yet shown
him, where nothing is pending, is the one case worth a question -- and the
question is *which* work, never whether the word meant what it said.

**"Blocked" means a call came back refused, not that you expect one to.**
`Go merge` is not an invitation to go looking for reasons the merge might
not be allowed; try the step, and hand off on what the tool actually said,
quoting it. A restriction the repository itself declares on a branch is a
different thing and is handed off nowhere -- the phrase authorizes a merge,
it does not lift a branch rule, so a merge that waits for review goes on
waiting for review.

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

**A refusal that ends the turn spends the authorization and delivers
nothing.** The person said two words to avoid being asked a question, and
"I could not, permissions" hands them back the whole job plus a new one:
working out which session could have done it. The session that hit the wall
is holding the branch, the diff and the reason it stopped -- it is better
placed than anyone to write that handoff, and writing it costs one call.

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

**A second phrase, `Approved`, added 2026-09-13 on Morgan's instruction:**
*"To the 'go merge' command, also add: if I say 'approved', that also means
the same as gold merge."* It is one command with two triggers rather than two
practices, because everything after the trigger -- the chain, the spoken
branch, the blocked-step handoff, the fact that it authorizes this merge and
not the next one -- is identical, and a second file would be the same rule
maintained twice. The word is riskier than `Go merge` in exactly one way:
`merge` needs an object to be about something else, where `approved` is
already an adjective this repository uses about plans and sources in ordinary
prose, so the Detail above names that case explicitly.

**Extended 2026-09-13, on Morgan raising it**, out of a `Go merge` he had
just run that came back as a repository-permissions problem: *"if you don't
have permission to do the go merge (or a part of it) because of cross repo
issues, then you can spawn a new session to do so."* The chain in the Rule
had always assumed every step of it was reachable from wherever the phrase
was read, and [spawn-session](spawn-session.md) -- written about work that
has not started yet -- did not obviously govern a chain that stopped
halfway. So the session that hit it reported the refusal and stopped, which
is what he was looking at when he asked.

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
