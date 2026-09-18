---
slug:        go-merge
title:       "\"Go update\", \"Approved\", and \"Go merge\" -- authorize sync, confirm branch, commit, push, PR, and merge (or a direct push, when it's trivial)"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message carries the merge phrase, or plainly authorizes a merge"
gates:       ["merge"]
index_clause: "\"Go update\"/\"Approved\"/\"Go merge\": trivial -> push; else sync, branch, PR, merge"
checked_by:  null
defines:     ["Go update", "Approved", "Go merge"]
command:     {"Go update": "Save the work, publish it, and tell you where it went — without asking anything further.", "Approved": "The same as **Go update**: save the work, publish it, and tell you where it went.", "Go merge": "The same as **Go update**: save the work, publish it, and tell you where it went."}
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
  go merge\"; trivial/substantial split added 2026-09-15, Morgan -- \"Sold.
  Let's do it. Go merge\", choosing it over a rename to a new command; third
  phrase added later the same day, Morgan, reconsidering the rename he had
  just set aside -- \"I think the solution is to allow BOTH words to be used\";
  extended 2026-09-16, Morgan, on Alex's intent-over-keyword point -- \"apply
  the same to the ones that are a serious decision such as Go Merge, Weak Yes,
  etc -- and just note that (if the exact phrase isn't used), then use your
  judgment and ASK the person if you have doubt\"; reversed 2026-09-18, Morgan --
  \"let's reverse it so that Go update is the primary one, that you recommend
  and use\" and \"it's not about the merge because many times it's not a merge
  but a direct edit,\" declining a rename again for the same reason as
  2026-09-15"
strength:    decided
---
## Rule
If the message you are answering tells you to `Go update` --
case-insensitive, **anywhere in the message**, as its own line, as a whole
sentence, or as a clause inside a longer one -- treat it as authorization,
right there, to: **sync your local branch with origin, say out loud which
branch you are merging into, commit the pending work, push the branch, open
a pull request (or confirm one is already open), and merge it** -- using the
repo's usual conventions, without asking again first.

**The phrase is not scoped to the git sequence itself — it authorizes doing
whatever finishing the thing in front of it actually requires.** Where
landing the change really is sync/commit/push/PR/merge, do exactly that.
Where the request needs something else, do that instead of forcing the git
sequence onto work it doesn't fit. And where it turns out nothing needs
doing at all — the change already exists, or the request has no repository
action to take — **say so plainly instead of manufacturing a commit or a
merge just to satisfy the phrase.** The authorization is for finishing the
work, not for performing the ritual regardless of whether the work calls
for it.

**The default is to act on it.** Nothing about the phrase's position, the
punctuation around it, or what was said before it changes the answer, and
you do not have to have announced that you are ready to commit first. Said
before you have mentioned committing at all, it means get ready and go.

**Classify the pending change before running that chain.** Two kinds of
work answer to `Go update`, and they are not treated the same:

- **Trivial** — wording, a typo, a dead link, formatting, or any other edit
  that does not change what a document requires or what code does, *and* it
  is already the kind of content this repo allows a direct edit to
  ([its own rule](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md#working-in-this-repo)
  — README, practice wording, engine code, never an abstracted lesson
  arriving as a check-in from elsewhere). For this: commit and push straight
  to the branch. No pull request. The light check still runs before the
  commit and the deep check still runs before the push — verification does
  not get skipped, only the PR wrapper does.
- **Substantial** — everything else: a new practice, a rule's meaning
  changing, real logic in code, anything touching more than one system, or
  anything you are not confident is trivial. Run the chain above, unchanged.

**Default to substantial when you are not sure.** A pull request here costs
nothing extra — this is the branch that merges without anyone's sign-off —
while a bad direct push is a silent edit sitting on the branch every session
reads from. A close call goes through the PR.

**Say which path you took and why, in one clause, in the reply.** Not
"pushed the fix" — *"pushed directly (wording only, no behavior change)"* or
*"opened a PR (touches engine logic)"*. A path taken without its reason is
exactly as unreviewable as no reason at all.

**`Approved` means the same thing.** Said of the work in front of you --
as its own line, as a whole sentence, or as a clause accepting what you just
proposed or showed -- it carries the identical authorization, the identical
chain, and the identical branch-naming step. There is no weaker reading of
it: it is not "noted", it is not "go ahead and I will merge it later", and it
does not become a question about whether he meant the command.

**`Go merge` means the same thing too, permanently, alongside `Go update`
rather than instead of it.** `Go update` is the one to reach for first:
"update" names what actually happens whether or not a merge ends up in the
picture -- a trivial fix can go straight to the branch with no merge in
sight at all -- where "merge" reads as a promise the phrase might not
keep. `Go merge` stays exactly as good a way to say it, especially when a
real merge is literally what is happening; neither phrase retires the
other, and using one over the other still carries no different meaning or
weaker authorization -- only which one gets said first changed.

**None of the three phrases is required for the authorization to exist —
they are the unambiguous case, not the only case.** A message can plainly
authorize a merge without any of them in it: "sold, ship it", "yes, let's
do this", "that's exactly what I wanted, put it up" all read as this
command to a reasonable person, and treating them as anything less is
answering a clear yes with a question. **The phrases stay valuable because
they remove the one thing intent-reading cannot: doubt.** Say one of them
and the chain runs, full stop, no matter how the sentence around it reads.

**Where the phrase is absent and the sentence leaves genuine doubt, say
your reading out loud and get it confirmed before running the push, the
pull request, or the merge — never guess silently in either direction.**
"I'm reading that as authorization to go merge this — say so if that's not
what you meant" costs one line and is cheap; a merge nobody actually asked
for, or work left sitting because a real go-ahead was read as small talk,
both cost more than that line. This is *not* license to ask about
phrasing that already reads as a clear yes — asking there is the exact
interruption this practice exists to remove — it is for the sentence that
could honestly go either way. Committing locally is never blocked on
this: do that regardless, and hold only the steps that touch the shared
branch until the reading is confirmed.

**Say the target branch before merging, every time.** It is spelled out
here rather than left inside "usual conventions" because that is the step
whose silent failure is expensive: a merge into the wrong branch looks
identical to a correct one until somebody goes looking.

**A step you cannot perform hands off; it does not come back as a
question.** If the push, the pull request or the merge is refused because
this session cannot reach the repository -- a cross-owner `add_repo`
refusal, no push access, a repository nobody attached -- **the
authorization is still good and it travels with the work.** Run
[spawn-session](session-text.md) on the spot: wake a live session that
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
"That was perfect. Go update", "Go update.", a lone line reading
`GO UPDATE`, "go update it and tell me what broke", and "when the check
passes, go update" all count. What does not is the word being used about
something else -- "go update the branch, then look at the diff", "can you
update TODO.md first", "go update your local clone before you start" --
where `update` has its own object and is plainly not an instruction about
the work in front of you.

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

**`Go merge` collides with ordinary language the same way, because
"merge" names a routine action of its own elsewhere -- two lists, two
branches, two reports.** "let's go merge those two lists", "go check the
logs, then merge the report" are not the command -- there `merge` has an
object of its own, exactly like `update` above. "Go merge it", "go merge,
no PR needed for this one", and a lone line reading `GO MERGE` do count.
Same test: if you can tell what would be updated and the word is being
said about it, do it.

**"Blocked" means a call came back refused, not that you expect one to.**
`Go merge` is not an invitation to go looking for reasons the merge might
not be allowed; try the step, and hand off on what the tool actually said,
quoting it. A restriction the repository itself declares on a branch is a
different thing and is handed off nowhere -- the phrase authorizes a merge,
it does not lift a branch rule, so a merge that waits for review goes on
waiting for review.

**Trivial reads narrowly, not generously.** "Fixed a typo in
[README.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/README.md)",
"corrected a dead link", "reworded a confusing sentence without changing
what it asks for" are trivial. "Fixed a bug in
[tools/precedent_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_check.py)",
"changed what a check enforces", "added or edited a practice" are not — even at one line,
even when the fix is obviously correct, because what changed is behavior or
meaning, not words. **The test is never the size of the diff; it is whether
the meaning changed.**

**Once one of the three phrases is there, ask about the object, never about
the phrasing.** The one question worth stopping for is *which* pending work
is meant, and only when several unrelated branches are genuinely in play.
Asking whether the words were meant as the command produces exactly the
interruption the command exists to remove: if you can tell what would be
merged, merge it. This is a different case from the phrase being absent
altogether — there, the confirmation above is about whether the message
authorizes anything at all, not about which branch it means.

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
was read, and [spawn-session](session-text.md) -- written about work that
has not started yet -- did not obviously govern a chain that stopped
halfway. So the session that hit it reported the refusal and stopped, which
is what he was looking at when he asked.

**Moved to universal 2026-09-08, on Morgan's decision**, from his private
individual set. The move is also what makes the phrase readable at all by a
session that has not attached a private source -- which had already happened
once: a session followed an instruction to go ask what "Go merge" meant,
generating the precise interruption the phrase exists to prevent, while the
definition sat in a repository nobody had fetched.

**The trivial/substantial split added 2026-09-15, on Morgan's decision**,
raised after he noticed two things sitting side by side. A session had
pushed two engine bug fixes straight to `precedent-beta-v01` with no pull
request -- real, verified fixes, landed on nothing but the same session's
own report that its deep check passed. Separately, he had been typing
`Go merge` for one-line typo fixes and paying the full PR round-trip every
time, for work that carried none of the first case's risk. Two shapes were
proposed and discussed in the open before either was written: banning
direct edits outright, and renaming the command itself (to `Go update`) so
a new phrase would front-load the judgment call. Both were set aside --
a ban would have made every typo fix cost a PR again, and a rename breaks a
phrase already propagated to every source that vendors this file, for a
problem that was never about the name. What was missing was the
classification step itself, so it went into the existing chain rather than
a new one. *"Sold. Let's do it. Go merge."*

**A third phrase, `Go update`, added later the same day, on Morgan's
decision, after he reconsidered the rename he had just set aside.** He came
back to it directly: *"I thought about it, and I'd like to do it anyway
despite your reasoning... I think the solution is to allow BOTH words to be
used! If we treat Go Merge and Go Update as the same, then it's easier to
justify to people like Alex... it's a secondary synonym in case people say
the wrong thing, but it really is a 'go update it', not necessarily
merge."* This is not the rename that was set aside hours earlier -- that
would have broken a phrase already propagated to every source vendoring
this file, for a problem that was never about the name. A synonym breaks
nothing: `Go merge` keeps meaning exactly what it always meant, and `Go
update` now means the same thing beside it. Same shape as `Approved`'s
addition two days earlier -- one command, now three triggers, maintained
once.

**Revised 2026-09-15, on Morgan's decision, to state the scope explicitly
rather than leave it implied by the worked examples.** He put it this way:
*"'Go merge' doesn't mean just merge but 'Do what you need to, to make it
happen -- and if there is nothing to do, then just TELL ME!'"* The git
sequence was always the common case, not the definition; this makes that
explicit before a session reads the Rule too literally and either forces a
merge onto a task that doesn't need one, or stays silent when the honest
answer is that nothing was left to do.

**Revised 2026-09-16, on Alex's design point and Morgan's decision, to
recognize the intent rather than only the three phrases.** Alex's framing,
relayed by Morgan: a session should ask itself whether a message reads as
this authorization, not scan it for the trigger words. Morgan agreed and
set the boundary for how far that goes on an action this size: *"apply the
same to the ones that are a serious decision such as Go Merge, Weak Yes,
etc -- and just note that (if the exact phrase isn't used), then use your
judgment and ASK the person if you have doubt."* This is why the confirm
step above holds only the shared-branch steps, and only when the reading is
genuinely in doubt -- not a general license to question a clear yes, which
is the interruption this practice has always existed to remove.

**Reversed 2026-09-18, on Morgan's decision, to make `Go update` the
phrase the assistant leads with, recommends, and reaches for first --
`Go merge` stays exactly as valid, just second.** He named the seam his
own 2026-09-15 words had already found: *"it's not about the merge because
many times it's not a merge but a direct edit."* Asked directly for the
ordering to flip, not for a rename -- a rename was declined again, for the
same reason it was declined on 2026-09-15, propagation to every source
that vendors this file for a problem that was never about the name. Both
phrases keep meaning exactly the same thing, with the identical
authorization and the identical chain; only which one comes first, in the
frontmatter and in the assistant's own mouth, changed.

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

**The trivial/substantial split is the same shape of judgment call, and just
as uncheckable from the diff alone.** A one-line fix to
[tools/precedent_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_check.py)
and a one-line fix to
[README.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/README.md)
are the same shape in a `git log`; only the second is trivial by this rule,
and telling them apart means reading what changed, not measuring it. One
slice of it is mechanical and is not built:
whether a push straight to a branch, with no open pull request, touches
only the content a repository's own convention already allows a direct edit
to. For this repo that convention is already written down -- named in the
Rule above -- and a check could fail a direct push that lands outside it.
Recorded rather than left silent; not built here.
