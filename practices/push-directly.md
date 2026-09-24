---
slug:        push-directly
title:       "\"Push directly to [branch]\" -- skip go-merge's judgment call, push straight to that branch, no PR, for this one change"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message says \"Push directly\", naming a branch (\"push directly to main\") or not, or gives a specific instruction to skip the PR for this one change"
gates:       ["merge"]
index_clause: "\"Push directly [to BRANCH]\" -- no PR; unnamed defaults to the branch in play"
checked_by:  null
defines:     ["Push directly"]
command:     {"Push directly": "Save the work and push it straight to the branch right now -- no pull request, whatever go-merge's classification would otherwise call for. Name the branch (\"push directly to main\") to target it explicitly; say it bare and it targets whichever branch the work is already headed toward."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-20"
approved_by: "Morgan, 2026-09-20 -- coined in the same conversation that
  retired `Go merge` as a trigger of go-merge, asking what plain-English
  developers say to \"go make it live... but I don't want to merge it,\"
  then, once told the mechanism already existed as go-merge's own
  direct-instruction override, asking for a standing name for it: \"let's
  define a second and separate phrase... 'push directly' that does
  precisely just that.\" First used to authorize landing this file and
  go-merge's retirement of `Go merge` together: \"I will forget that
  phrase. Please push this one directly.\" Amended the same day,
  2026-09-20, to carry its target inline and default the rest: \"Let's
  update that to be clearer: 'push directly to [main]' in which '[main]'
  refers [to] the primary branch they are working towards... And let's
  update the definition so that IF they don't say 'to [main]', then you
  ASSUME it is the primary branch they are working towards.\" Invoked in
  the same message, in its amended form, to authorize landing the
  amendment itself: \"Push directly to precedent-beta-v01.\""
strength:    decided
---
## Rule
When the message you are answering says **"Push directly"** -- case-insensitive,
anywhere in the message, as its own line, a whole sentence, or a clause
inside a longer one, naming a branch or not -- treat it as
[go-merge](go-merge.md)'s own direct-instruction override, said in a few
words: **sync your local branch, commit the pending work, and push straight
to the target branch, right now, no pull request** -- whatever `Go
update`'s push-by-default/high-risk classification would otherwise call for
on this change.

**The phrase names its own target when the message says so.** "Push
directly to main", "push directly to precedent-beta-v01" -- whatever
follows "to" is the branch to push to, full stop, whatever branch a
session might otherwise have guessed.

**Said bare, with no branch named, the target defaults to the primary
branch the work is already headed toward** -- the branch this session's
own work has actually been developed and committed against, never a
repository's configured default branch chosen just because it is
configured that way. Where the repository declares that branch --
`base_branch` in its `precedent.json`, or a rule of its own -- the
declaration decides it ([primary-branch](primary-branch.md)); absent one,
it is whichever branch the change in front of you is already on.

**This is not a new kind of permission.** `Go update`'s Rule already lets a
direct, specific instruction about one change override its own
classification, high-risk included. `Push directly` is that instruction,
standing and reusable, so it does not need to be re-argued in a full
sentence every time it is meant.

**It authorizes this one change, not a standing exemption.** Said about a
different piece of work later, it authorizes that push, to whatever branch
that invocation names or defaults to; it does not turn off the high-risk
classification generally, and `Go update` still asks the question on the
next change that does not carry this phrase.

Same verification as [go-merge](go-merge.md): the light check still runs
before the commit and the deep check still runs before the push -- this
phrase skips the PR wrapper and the classification, never the checks. **And
the same landing**: the target is that branch on `origin`, confirmed by a
fetch before the reply reports it
([verify-postcondition](verify-postcondition.md)), never a commit left in
the local clone.

**Say the target branch before pushing, every time** -- same reason
[go-merge](go-merge.md) gives: the failure this catches is silent, not
loud, and looks identical to a correct push until somebody goes looking.
Say it whether the phrase named the branch or left it to the default --
naming it out loud in the reply is what makes the default checkable, not
just correct.

**A step you cannot perform hands off; it does not come back as a
question** -- run [prompt-please](prompt-please.md) on the spot, same as
[go-merge](go-merge.md).

## Why
`Go update`'s Rule already allows overriding its own high-risk/default
classification with a direct, specific instruction -- but writing that
instruction out in full, "skip the PR even though this touches a
governance practice," costs a sentence every time it is meant. `Push
directly` names the override once, so saying it costs two words, the same
saving `Go update` and `Approved` already make for the base case.

**Naming the branch inline, and defaulting the rest, closes the gap the
original two words left.** A bare "push directly" said nothing about
where, so the phrase that was supposed to save a sentence still cost one
in practice -- confirming a target that was usually never in doubt.
Letting the phrase carry its target when it matters ("to main" versus "to
precedent-beta-v01" are genuinely different instructions) and inherit it
from the work otherwise keeps the phrase to a handful of words in the
case that is actually routine: the target was the branch already being
worked on all along.

## Story
Coined 2026-09-20, Morgan, in the same conversation that retired `Go
merge` as a trigger of [go-merge](go-merge.md). He asked what plain-English
developers say for landing a small change live without a merge, was told
the general answer ("push directly," as opposed to opening a PR and
merging), and once he understood the real cost tradeoff go-merge's
push-by-default/high-risk split had just been built around, asked for two
things in the same breath: fold `Go merge` entirely into `Go update`, and
give him a plain, separate phrase for "skip the judgment, just push it"
that he would actually remember to say, rather than "I will forget that
phrase." He used it to authorize landing this file and `Go merge`'s
retirement together -- its first invocation, on a change
[go-merge](go-merge.md)'s own Rule would otherwise classify as high-risk,
since it edits a governance practice directly.

**Amended the same day.** Reading the freshly-coined phrase back, Morgan
asked for it to say its target the way a person actually would --
"push directly to `[main]`", with `[main]` standing for whichever branch
is really the primary one in play, not the literal word `main` -- and for
a bare "Push directly" with nothing named after it to default to that same
primary branch rather than leave a session to guess or stop and ask. He
invoked the amended phrase, in the same message that asked for the
amendment, to authorize landing the amendment itself: "Push directly to
precedent-beta-v01" -- naming this repo's actual routine branch, not
`main`, exactly the distinction [merge-target-is-beta-branch](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/local/practices/merge-target-is-beta-branch.md)
exists to keep a session from blurring.

## Install
Nothing mechanical checks that the phrase was honoured, same reason
[go-merge](go-merge.md) gives: this governs how a chat message is read, not
a property of the diff. What is checkable downstream is what
[go-merge](go-merge.md)'s own Install section names: the push lands on the
branch named in the reply, with no open pull request wrapping it.
