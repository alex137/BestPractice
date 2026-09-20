---
slug:        push-directly
title:       "\"Push directly\" -- skip go-merge's judgment call, push straight to the branch, no PR, for this one change"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message says \"Push directly\", or gives a specific instruction to skip the PR for this one change"
gates:       ["merge"]
index_clause: "\"Push directly\" -- skip the judgment, push straight to the branch, no PR"
checked_by:  null
defines:     ["Push directly"]
command:     {"Push directly": "Save the work and push it straight to the branch right now -- no pull request, whatever go-merge's classification would otherwise call for."}
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
  phrase. Please push this one directly.\""
strength:    decided
---
## Rule
When the message you are answering says **"Push directly"** -- case-insensitive,
anywhere in the message, as its own line, a whole sentence, or a clause
inside a longer one -- treat it as [go-merge](go-merge.md)'s own
direct-instruction override, said in two words: **sync your local branch,
say out loud which branch you are pushing to, commit the pending work, and
push straight to that branch, right now, no pull request** -- whatever
`Go update`'s push-by-default/huge classification would otherwise call for
on this change.

**This is not a new kind of permission.** `Go update`'s Rule already lets a
direct, specific instruction about one change override its own
classification, huge included. `Push directly` is that instruction,
standing and reusable, so it does not need to be re-argued in a full
sentence every time it is meant.

**It authorizes this one change, not a standing exemption.** Said about a
different piece of work later, it authorizes that push; it does not turn
off the huge classification generally, and `Go update` still asks the
question on the next change that does not carry this phrase.

Same verification as [go-merge](go-merge.md): the light check still runs
before the commit and the deep check still runs before the push -- this
phrase skips the PR wrapper and the classification, never the checks.

**Say the target branch before pushing, every time** -- same reason
[go-merge](go-merge.md) gives: the failure this catches is silent, not
loud, and looks identical to a correct push until somebody goes looking.

**A step you cannot perform hands off; it does not come back as a
question** -- run [prompt-please](prompt-please.md) on the spot, same as
[go-merge](go-merge.md).

## Why
`Go update`'s Rule already allows overriding its own huge/default
classification with a direct, specific instruction -- but writing that
instruction out in full, "skip the PR even though this touches a
governance practice," costs a sentence every time it is meant. `Push
directly` names the override once, so saying it costs two words, the same
saving `Go update` and `Approved` already make for the base case.

## Story
Coined 2026-09-20, Morgan, in the same conversation that retired `Go
merge` as a trigger of [go-merge](go-merge.md). He asked what plain-English
developers say for landing a small change live without a merge, was told
the general answer ("push directly," as opposed to opening a PR and
merging), and once he understood the real cost tradeoff go-merge's
push-by-default/huge split had just been built around, asked for two
things in the same breath: fold `Go merge` entirely into `Go update`, and
give him a plain, separate phrase for "skip the judgment, just push it"
that he would actually remember to say, rather than "I will forget that
phrase." He used it to authorize landing this file and `Go merge`'s
retirement together -- its first invocation, on a change
[go-merge](go-merge.md)'s own Rule would otherwise classify as huge, since
it edits a governance practice directly.

## Install
Nothing mechanical checks that the phrase was honoured, same reason
[go-merge](go-merge.md) gives: this governs how a chat message is read, not
a property of the diff. What is checkable downstream is what
[go-merge](go-merge.md)'s own Install section names: the push lands on the
branch named in the reply, with no open pull request wrapping it.
