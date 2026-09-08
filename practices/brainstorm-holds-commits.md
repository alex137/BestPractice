---
slug:        brainstorm-holds-commits
title:       A brainstorm holds every commit until the person says otherwise
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "a conversation is exploratory, or a person calls it a brainstorm"
gates:       ["push", "merge"]
index_clause: "in a brainstorm, write nothing to the repo and commit nothing until he says so"
checked_by:  null
defines:     ["Brainstorm"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08 -- after a session committed and pushed twice, unasked, inside an exploratory thread"
---
## Rule
When a conversation is a **Brainstorm** -- the person says the word, or the
thread is plainly exploratory ("I'm wondering", "what are my options", "do
you have ideas", "maybe this is a terrible idea") -- **write nothing to the
repository and commit nothing until they say to.** Research freely, read
whatever you need, argue the case, propose the design. Do not create, edit,
commit, push, open a pull request, or merge.

**The edit is the thing to hold, not just the commit.** A session that
writes files and then asks whether to commit has already made the decision,
because a working tree it left dirty is one a Stop hook or a later turn will
push to finish. Say what you would write and where; wait to be told.

A brainstorm ends only when the person authorizes the work -- `Go merge`,
"do it", "write it up", or anything else unambiguous. **Their answering a
question inside the brainstorm is not authorization**, and neither is their
enthusiasm for the idea.

## Detail
**When in doubt, it is a brainstorm.** The cost is asymmetric and not
close: holding costs one question at the end of a reply, and guessing wrong
puts commits in someone's history that they did not want, on a branch they
now have to read before they can trust it.

**A directive inside an exploratory thread is still a directive.** "Make
this a practice" is an instruction to build, even if the three messages
before it were speculation. What the state changes is the default, not the
person's ability to ask for something.

**This does not reach the person's own house-keeping.** A brainstorm still
ends its turn honestly: if a repository's tooling has already left the tree
dirty, say so plainly rather than committing to tidy it away.

## Why
Exploratory conversation is where a person is deciding what they think, and
a commit made in the middle of it is a decision recorded before they made
one. The repository is memory, which is exactly the problem: a speculative
edit committed on their behalf is indistinguishable, a month later, from
something they chose.

There is a second cost that is easy to miss. Once a session has written a
proposal into the tree, its next reply is arguing for something it already
built, and the person is now reviewing a fait accompli rather than weighing
an idea. Holding the edit keeps the conversation about the idea.

## Story
2026-09-08. A thread that began *"I'm wondering if there's a better way"*
and ran through *"maybe this is a terrible idea. What do you think?"*
produced two commits, both pushed, neither asked for. The work itself was
not wrong -- open items recorded, no deliverable touched -- and that is what
makes the incident worth writing down rather than shrugging at: nothing
failed loudly, and the session's own reasoning at each step was that
capturing an open item is cheap and reversible. It filed each one under
"repo is memory" and pushed. Morgan, the same day: *"Multiple times today
you committed to github on your own without my telling you, and I didn't
want you to."*

The reasoning was not wrong about capture; it was wrong about who decides
when. `repo-is-memory` says a decision must not live only in a thread. It
does not say a session may decide, on the person's behalf, that something
has become a decision.

## Install
**No mechanical check, and the reason is the same one
[go-merge](go-merge.md) records:**
the trigger lives in the conversation, and nothing left behind afterwards
distinguishes a commit made under authorization from one made on a
session's own initiative. Both leave the identical commit.

**The environment actively pulls the other way, and an adopting repo should
know it.** A `Stop` hook that refuses to end a turn while the working tree
is dirty -- Precedent ships one at
`templates/harness/claude-code/hooks/stop-git-check.sh` and instantiates it
for its own repository -- will block a session that correctly declined
to commit, and the obvious way out of that block is to commit. That is why
this practice holds the *edit* rather than the commit: a brainstorm that
writes nothing never reaches the hook, so the two mechanisms stop fighting.
Do not weaken the Stop hook to make room for this one; it is load-bearing
for the ordinary case, where uncommitted work is work about to be lost.
