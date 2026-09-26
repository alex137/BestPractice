---
slug:        base-branch-is-the-record
title:       "The base branch is the record; another session's summary is not"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "starting work another session may have done, or opening a PR"
gates:       ["push"]
index_clause: "read the base branch before starting and before the PR"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-12"
approved_by: "Morgan, 2026-09-13 -- \"yes, go merge, let's keep base branch is
  universal.\" Reached after he twice challenged the rule's NAME (\"if the branch is the
  record, when I delete merged branches, does that delete the record?\") and the answer
  was demonstrated rather than asserted -- a merged branch deleted in a throwaway repo,
  and one of this repo's own branches already auto-deleted on merge with its work still
  on the base branch. He chose the level in his own words after that, which is why this
  reads `decided` and not `assented`. Its ORIGINAL landing, 2026-09-12, rested on a
  scheduled instruction asserting his authorization that he does not recall giving
  (\"I don't remember if I did\"); the rule stands on the 2026-09-13 answer instead."
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
change, which is the common case. **Deleting a merged branch destroys nothing** --
merging copies its commits onto the base branch, and the feature branch is only a
pointer to them, so routine housekeeping that removes merged branches is safe and
is not what this rule is about. Search the base branch for the content:
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
moot"*, wrote the same change, ran the gates, pushed it, and opened a pull
request. Only then did it find the other session's merge, twenty minutes old.
The duplicate was closed unmerged. The summary was not wrong when it was
written; it was written before the merge it failed to mention.

**The merge was not even the summarising session's.** A third session, spawned
by one of the first two, had landed it — and a spawned session is invisible to
the sibling it was spawned beside, which cannot list it, message it, or read
what it did ([prompt-please](prompt-please.md)'s return path is the same fact
from the other end: a spawned session reports back through its repository or
not at all). So the summary was not merely stale. **It was written by a session
that had no way to know**, which is why the remedy cannot be a better summary
or a more careful reader of one, and has to be a read of the branch.

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
