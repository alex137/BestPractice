---
slug:        lease-in-flight-work
title:       Work in flight is leased on a coordination branch, so a second session cannot start it again
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus. The work a lease guards is whatever a repository finds costly to start twice -- a submission, a migration, a solve -- and it shares no path. Reached through the occasion index. Decided: 2026-09-27, when the practice landed."
occasion:    "starting slow, costly or external work another session could also start"
gates:       []
index_clause: "lease work in flight on a branch; the starting tool checks the board first"
checked_by:  null
defines:     ["lease board"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-27"
approved_by: "Alex, 2026-09-27 — asked for it to be built into BestPractice and applied in the shared set and dependent repo #1, and for it to survive that repo's coming split into several repositories"
strength:    decided
---
## Rule
**Trunk shows what has landed, never what another session has started and
not yet landed.** So when a session starts work that is slow, costly or
external — and that a second session, reading the same trunk, would start
again — it **takes a lease on the items that work covers**, on the **lease
board**: a coordination branch of a shared remote holding **one small JSON
file per lease**. The tool that starts the work **checks the board first and
refuses** on an overlapping lease held by someone else; the tool that
records the result **marks or releases** the lease. **Nothing expires a
lease on its own.**

## Detail
**Why a branch of JSON files, not a database.** Sessions run in separate
containers with no shared disk, so a database's locking would lock nothing.
Git already gives every session one atomic operation: **a push that is
refused when the branch moved**. The board is written with plumbing (a
private index, `commit-tree`, a push of the new commit), so the working tree,
the index and the current branch are never touched; a refused push re-reads
the board and re-runs the overlap check against the board it is about to
replace. **One file per lease** means two sessions taking different leases
touch different paths, so their retries always succeed and the only conflict
left is the one that is wanted. Every take, update and release is a commit,
so the branch's log is the full history of who held what.

**Only branches, and never a deletion.** A hosted session's git proxy
refuses pushes outside `refs/heads/` and cannot delete a branch (practice
[never-delete-a-remote-branch](never-delete-a-remote-branch.md)), so the
board is one long-lived branch and a release is a commit that removes a
file.

**The board lives with the work it guards, named by URL.** A host sets
where its board is — a remote name or a repository URL — rather than
assuming its own origin. When one project is split across several
repositories, every one of them names the same board, and the guard
survives the split. A holder is recorded as `repo:branch`.

**What the practice supplies and what each repository supplies.** The rule
and the engine ([tools/lease_board.py](https://github.com/alex137/BestPractice/blob/staging/tools/lease_board.py)) are the
same everywhere. Each repository supplies only its **call sites**: what an
item is (a record, a result, a migration) and which of its commands starts
the work and which records the outcome. Writing those few lines is adopting
the practice.

**A lease that goes stale is shown, not removed.** `list` prints each
lease's age; a session that finds an abandoned one releases it with the
reason (practice [repair-cannot-discard-work](repair-cannot-discard-work.md)).
A tool that only *waits* on a lease may stop waiting on an old one without
releasing it. An unreachable board warns loudly and lets harmless work go
ahead; the warning names the command that takes the lease by hand.

**The judgment half is [dont-race-another-window](dont-race-another-window.md).**
A board catches the collisions somebody wired a call site for; a request
for work another of the person's windows already has in flight arrives in
conversation, usually before any tool runs. There the session declines and
sends the person back to the window that has it, and an overlapping lease
is one of the signals that tells it so.

**A single-slot lock is the special case.** A lock that lets one session at a
time run an operation is a lease board with one item; the same push-as-lock
mechanics apply.

## Why
The costliest duplicate is the one nobody can see coming: each session's
reasoning is sound against the trunk it read, so no review of either
session's work finds the mistake. A rule to land results immediately
narrows the window but cannot close it, because the window opens when the
work *starts*, often days before its result can be recorded.

## Story
In a dependent repository, two concurrent sessions each produced and made
the same paid, irreversible external submission. The first had submitted
and not yet landed the record on trunk; the second built from trunk, saw the
work still pending, and did it again. The repository's first fix, landing
the record immediately after the submission, left the days between starting
the work and recording its result uncovered. Asked whether a store outside
the repository would help, the answer was narrow: not a database for
knowledge, which belongs in git, but a board of leases on work in flight,
as JSON files on a branch rather than a database file git cannot merge.

## Install
Vendor [tools/lease_board.py](https://github.com/alex137/BestPractice/blob/staging/tools/lease_board.py) and write a host shim
that sets `REMOTE` (the repository whose work it guards, by URL once work
spans repositories), `BRANCH` and `DIR`. Wire the call sites: the command
that starts the work calls `conflicts()` and refuses on a hit, then
`take()`; the command that records the result calls `update()` or
`release()`. Test the race with two clones of a scratch remote before
relying on it.
