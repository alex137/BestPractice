---
slug:        prompt-please
title:       "\"Prompt Please\" hands back a recommendation, or work this session cannot reach, as one paste-ready prompt for a new session"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "handing the person work to do, starting work that may touch a repository this session cannot reach, or the person wants to act on a recommendation already given by opening a fresh session"
gates:       ["reply"]
index_clause: "\"Prompt Please\" -- recommendation or unreachable work, one paste-ready prompt"
checked_by:  null
defines:     ["Prompt Please"]
command:     {"Prompt Please": "Write up the situation, the problem, your recommended action and why, and hand it back as one prompt ready to paste straight into a new session -- naming which repository to root it in and which others to attach."}
status:      active
in_force_at: null
supersedes:  ["session-text"]
overrides:   null
added:       "2026-09-20"
approved_by: "Morgan, 2026-09-20 -- described the two cases and the phrase
  himself: a smaller, paste-ready sibling to Write it up, used once a
  recommendation is already on the table and he just wants a clean prompt
  for a new session to run with it -- distinct from My options, which he
  reaches for earlier, to see the choices before mostly following whichever
  one gets recommended. Named it himself: \"Maybe we could call the new one
  'Prompt Please'.\" Folded Session Text into it in the same message: \"this
  new one deprecates session-text, it's basically a better version of it, I
  never use that anyway.\" Authorized in full: \"Go update.\" Tightened
  2026-09-20, same day, Morgan, after checking whether this and My options
  actually deliver the copy-in-one-click block both promise and finding the
  answer was often no: \"You often don't do that and I want to enforce
  it.\" The Rule now names the mechanism -- a fenced code block -- rather
  than just the outcome."
strength:    decided
source_practice_number: null
---
## Rule
**"Prompt Please" is the clean form, not the only one** -- "give me a prompt
for a new session on this", "write that up as something I can paste
elsewhere" and anything else that plainly asks for the same shape of answer
get the same treatment, recognized by what is being asked for rather than by
matching the phrase.

**Two occasions produce the same deliverable, and both get it:**

1. **A recommendation already exists and the person wants to act on it in a
   fresh session.** This is the common case: you have already said what you
   think should happen, and rather than think through alternatives, the
   person wants a clean, standalone prompt to carry that recommendation into
   a new window. **This is where it differs from
   [My options](my-options.md).** That command is for *before* a
   recommendation is settled -- laying out every real choice, its cost and
   its benefit, so the person can weigh them, even though they will often
   end up taking the pick anyway. `Prompt Please` is for *after* that point:
   the recommendation is already the plan, and what's wanted is the clean
   handoff text, not another comparison.
2. **The work itself belongs in a different session** -- because this
   session cannot reach a repository the work needs. **Before starting work
   you were just asked for, check whether it belongs in a different session,
   and check the repositories first.** Name the repositories the work has to
   read, write or push to, and compare that list against the ones this
   session actually holds. This check is unconditional: it runs whenever
   another repository might be involved, whether or not the person says
   anything, and `Prompt Please` is the explicit command for the times it
   did not fire on its own.

Whichever occasion triggered it, produce one prompt with all of the
following, every time:

- **The situation.** What is going on and the context that led to it,
  written for a reader with none of this conversation.
- **The problem or bug**, stated plainly, if the work is about fixing
  something rather than building something new.
- **This session's own id and title, with a link, and that a session wrote
  it rather than a person** --
  [seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md)'s
  header, required of any prompt one session hands to another.
- **The recommended action, and why.** Not a survey -- the thing to do,
  named plainly, with the reasoning behind it.
- **Which repository has to be the primary seed root** -- the one the new
  session needs opened or rooted in before any of this is actionable.
- **Which other repositories, if any, need to be attached alongside it.**
  Say "none" explicitly rather than leaving the reader to guess whether the
  question was even considered.

**Delivered as one fenced markdown code block (triple backticks), not a
paragraph of prose** -- the fence is what makes the client render a
one-click copy button; a block described in words but not actually fenced
has not delivered this. [The
three-things-always shape](handoff-is-pasteable.md) any reply that sends
someone elsewhere already owes: repository, exact paste text, a way back.
Nothing split into the surrounding prose, nothing left for the reader to
assemble.

**Never call a session-creating or session-messaging tool for this, and
never wake a live session either.** Produce the prompt and tell the person
to open a new window and paste it in themselves -- the same standing
instruction `session-text` held before this absorbed it, for the same two reasons:
reliability (sessions this session created, or woke, have come back rejected
often enough that the mechanism is retired outright) and portability (a
paste block needs nothing from any one provider's tool surface).

**The prompt carries a merge authorization only when the person gave one for
this handoff**, exactly as `session-text` drew this line before this
absorbed it. Absent that, the default text says so directly:

> **DO NOT MERGE — STOP AT THE PULL REQUEST. Wait for the word "Go merge" in
> this session before merging.**

When the person says `Prompt Please` together with `Go merge` (or
`Approved`) -- or anything that plainly gives both in the same breath -- the
authorization travels with the prompt, bounded exactly as
[go-merge](go-merge.md) already bound it (and `session-text` bound it
before this absorbed it): the handed-off work only, the branch that
repository's own rules say
routine work lands on, and conditional on that repository's own checks
passing. Whether the receiving session may act on it is
[relayed-authorization](relayed-authorization.md)'s question, not this
practice's.

## Detail
**Where this differs from [Write it up](write-it-up.md).** That command's
deliverable is a file, committed to the repo and reached later by a link --
built for the durable record, and bigger: the full context, sequence of
events and proposed fix, written to last. This command's deliverable is the
prompt itself, meant to be pasted directly into a new window with nothing to
click through and nothing to memorialize. Use `Write it up` when the issue
needs a record that outlives this conversation; use `Prompt Please` when all
that's needed is to hand the next step to a session that can act on it now.
Nothing stops using both on the same issue -- write it up for the record,
then `Prompt Please` for the actual handoff -- but this practice does not
depend on a commit existing first, and does not make one.

**The cross-repository check is the same check `session-text` ran, carried
forward rather than dropped.**
Compare OWNERS, not just repository names: a session already holding one
owner's repositories is refused another owner's outright, and `add_repo`'s
own refusal names both sides -- *"cross-tier adds are not supported in v1:
requested `<other>/<repo>` but session already has repos from owner(s)
[`<this>`]"*. Plan for that refusal; do not plan on it. Settle who merges at
the same moment you name the repositories, since a session that cannot
attach across owners cannot gain push access there either.

**A repository wall is not a permission refusal, and only one of the two
stops you relaying an authorization already given.** A session that cannot
reach another owner's repository has hit a capability boundary, and the
person authorized the work already -- relay it. A permission refusal is the
person declining, or the tool governing this session blocking the action
itself, and there the answer is to go back to the person, never to route
around it with a fresh session.

## Why
The four demands behind `My options` exist because the shape of a decision
answer used to drift toward an even-handed survey with no pick in it. This
command exists because the shape *after* the decision was made had the same
problem from the other direction: asked for a clean handoff, a reply would
describe what the new session should do in prose, leaving the person to
retype it, or would re-run the comparison `My options` already settled
instead of just producing the prompt. Naming the two occasions -- an
existing recommendation, and work this session cannot reach -- as one
command, with one deliverable, is cheaper than two commands that produce the
same shape of answer for different reasons.

## Story
Coined by Morgan, 2026-09-20. He named the gap directly: something like
[My options](my-options.md), for a copy-pasteable prompt into a new session,
but for the case where a recommendation already exists and he just wants to
move ahead on it -- distinguishing it from `My options`, which he uses to
see the choices first and will usually follow the recommendation anyway once
he has. He drew the second contrast himself, against [Write it
up](write-it-up.md): that command is bigger and formally committed to
GitHub; this one is smaller, and just a prompt. Asked to help name it, the
session proposed "Prompt Please"; he took it.

**Session Text folded in the same message.** He named it as a better version
of `session-text` and said he never used that phrase himself -- the cross-repository check it ran, and the paste-block mechanism
it produced, survive here rather than under a separate command he was not
reaching for. The check itself stays unconditional, exactly as it was: this
practice is the explicit trigger for the times it did not fire on its own,
the same role `Session Text` played before it.

**Tightened the same day**, after Morgan checked whether this practice and
[My options](my-options.md) both actually deliver the copy-in-one-click
block they promise and said the answer was often no: *"You often don't do
that and I want to enforce it."* "Ready to copy in one click" was true but
not mechanical -- nothing said the block had to be an actual fenced code
block rather than a paragraph that merely reads as paste-ready. Both
practices now name the mechanism directly. Strength: decided.

## Install
Nothing for an adopter to set up. The occasion index entry is generated
from this file, so the phrase reaches every session regardless of whether
any private source resolved.

No mechanical check, matching [my-options](my-options.md) and
[write-it-up](write-it-up.md): the artifact is a chat reply, not a file the
tree holds, so whether a given reply recognized
the request and assembled the required pieces is a judgment call on the
conversation, not a property a script watching a diff could read off.
