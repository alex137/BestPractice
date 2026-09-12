---
slug:        branch-is-the-record
title:       "The branch is the record; another session's summary is not"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "starting work another session may already have done, or opening a pull request"
gates:       ["push"]
index_clause: "read the base branch before starting and before the PR -- a summary lags"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-12"
approved_by: "Morgan, 2026-09-12, relayed through a scheduled instruction to land five
  fleet rules at universal -- \"facts about the platform and about running Claude
  sessions at all\", which \"do not vary by team or by person\". The placement is his;
  that this rule became its own practice rather than an extension was the session's
  judgment, named as a judgement call in that same instruction."
strength:    decided
source_practice_number: null
---
## Rule
**Fetch and read the base branch before starting work another session may
already have done — and read it again immediately before opening a pull
request.** Two reads, because the gap between them is exactly long enough for
somebody else's merge to land.

**Another session's status summary is not evidence of what landed.** It
records what that session *intended*, it is written before its last actions
finish, and nothing updates it afterwards. The repository is the only thing
that knows what actually happened
([repo-is-memory](repo-is-memory.md) is the same fact from the writing side:
that rule says commit it, this one says go read it).

**Look for the change, not for a branch.** A missing branch is not evidence
that the work never landed — a squash merge deletes the branch and keeps the
change, which is the common case. Search the base branch for the content:
a phrase from the text, the function name, the file. `git log --oneline
HEAD..origin/<base>` after a fetch answers "did anything land while I was
working", and grepping the file on `origin/<base>` answers "is my change
already there".

## Detail
**The second read is the one that gets skipped**, and it is the cheaper of
the two. The first read is remembered because it feels like orientation; by
the time the work is finished the question feels settled, and a fetch costs
one command against a claim that has had an hour to go stale.

**This is [verify-postcondition](verify-postcondition.md) turned around.**
That rule says check the state you wanted after acting, rather than trusting
what the command printed. This one says check the state you are assuming
before acting, rather than trusting what another session reported. Both fail
the same way — a confident answer read off something that was never the
authority.

**A summary is a worse authority than it looks**, because it is written in
the past tense about the future. "No branch, task moot" and "opened the PR"
are both written before the merge they describe either happens or does not,
and a reader cannot tell from the sentence which state it was written in.

**The cost is asymmetric, which is why the rule is a fetch and not a
judgement call.** Reading the branch costs one command. Not reading it costs
the whole piece of work, plus somebody else's attention to close the
duplicate — and the duplicate is discovered at the end, after the reasoning
and the writing are already spent.

## Why
Work that duplicates work is not merely wasted; it has to be *undone*. A
duplicate pull request cannot be silently dropped — someone has to read it,
establish that it is a duplicate, and close it, which spends a second
person's attention on top of the session's own.

The failure is not carelessness. A session that reads another session's
summary and believes it is doing the right thing: the summary is the most
recent information available and it is usually true. What makes it dangerous
is that it is *systematically* stale in one direction — it is written at the
moment a session stops, which is before its last push has been merged.

## Story
**Lived first-hand in this repository on 2026-09-12**, by the session that
wrote this practice. It cut a branch from what was then the tip of
`precedent-beta-v01`, worked for a while, and on re-fetching found the base
**seven commits ahead** — two merged pull requests, one of them recording the
same measurement, in the same source set, that the session's own previous
change had just been built on. Nothing had gone wrong, because the fetch
happened before anything was committed. The point is how ordinary it was: a
correct branch point, a normal amount of working time, and a base that had
moved twice underneath it.

**Reported from a team practice source the same day, and not verified
here** — that repository is private and this session could not reach it. A
session read another session's status summary saying *"no branch, task
moot"*, wrote the same change, pushed it, and opened a pull request. Only
then did it find the other session's merge, twenty minutes old. The
duplicate was closed unmerged. The summary was not wrong when it was
written; it was written before the merge it failed to mention.

## Install
Nothing to configure. The occasion index entry is generated, so every
session reads it whether or not any private source resolved.

No mechanical check, and this one was tried rather than waved past
([checkable-gets-checked](checkable-gets-checked.md)). What the rule governs
is a *read* — whether a session fetched and looked before it acted — and a
read leaves nothing in the tree. A session that checked and found nothing
leaves behind exactly what a session that never checked leaves behind: a
normal commit. The one downstream artifact, a duplicate pull request, exists
on the forge rather than in the repository, and by the time it exists the
rule has already been broken. The `push` gate is what carries it instead,
firing at the moment the second read is owed.
