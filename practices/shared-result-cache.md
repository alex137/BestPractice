---
slug:        shared-result-cache
title:       A heavy result keyed by a hash of its code is shared through git, so no session solves it twice
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A property of a memoized solve, which lives wherever a repository keeps its models; no common path. Reached through the occasion index, beside slow-steps-report-and-cache. Decided: 2026-09-27, when the practice landed."
occasion:    "memoizing a heavy solve, or finding a fresh session re-running one another session already ran"
gates:       []
index_clause: "share code-keyed memos on a cache branch; a peer waits on a leased solve"
checked_by:  null
defines:     ["result cache"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-27"
approved_by: "Alex, 2026-09-27 — asked for it to be built into BestPractice and applied in dependent repo #1, and for it to survive that repo's coming split into several repositories"
strength:    decided
---
## Rule
A heavy result memoized under **a key that is the content hash of the code
that produced it** (practice
[slow-steps-report-and-cache](slow-steps-report-and-cache.md)) is correct for
**any** session running that code — so it is **shared, not recomputed**. Before
a cold solve, a session **pulls the entry from the result cache**; after
one, it **publishes** it. A cold solve **takes a lease** (practice
[lease-in-flight-work](lease-in-flight-work.md)) on its entry, and a session
that misses while that lease is held **waits for the result** instead of
running the same solve beside it. The cache is **an accelerator, never a
dependency**: any failure falls back to the local memo alone.

## Detail
**Stored as one snapshot commit on one branch.** A hosted session can push
only to `refs/heads/` and can never delete a branch, so neither a ref nor a
branch per entry is possible. The cache branch holds a single root commit —
the entries plus an `index.json` — and every publish **replaces it**, pushed
with `--force-with-lease` against the tip it read. That is a
compare-and-swap: a concurrent publisher is refused, re-reads and retries,
and nobody's entry is lost. Old blobs fall out of reach instead of growing
history, so a clone that fetches every branch pays only for the current
snapshot.

**Bounded three ways.** Each family (the entry's name with its key stripped)
keeps its few newest entries, so two sessions on different code do not evict
each other; the whole snapshot stays under a total cap, oldest first; an
entry over a per-file limit is not shared. Measure before choosing the caps:
in the originating repository a three-minute solve produced a memo of a few
mebibytes.

**The key already survives a repository split.** A hash of the code does not
change when files move between repositories; at worst a move is a miss.
Each repository caches its own models' results in its own cache branch.

**Waiting is bounded and visible.** A waiting session prints what it waits
for, who holds the lease, and how long before it gives up and solves itself;
it stops at once if the lease disappears without a result, and ignores a
lease old enough to be abandoned. An environment switch skips the shared
cache entirely.

**A memo filled one entry at a time, on demand and without the lock,
is re-solved by every process that misses at once.** When the processes
that read such a table need all of it -- a gate that emits many blocks
from one model does -- solve the whole table once under the lock and let
the others wait. Measured in the originating repository: an engine sweep
filled per class, re-keyed by one edit, was sized by every batch emit
process at the same moment, and a three-minute solve took nine.

**The git mechanics are one shared engine.** The cache keeps its policy
— families, the per-family and total budgets, the index — and hands
[tools/branch_store.py](https://github.com/alex137/BestPractice/blob/staging/tools/branch_store.py)
each publish as a whole snapshot: a new root commit pushed with a lease
on the tip it read, so the branch never grows past what it holds.

**A solve killed by a signal keeps its claim.** Release at exit runs
only when the process exits normally; a process-group kill skips it,
and the claim stays on the board. Peers stop waiting on it once it is
older than the stale limit, but it is still wrong: after killing a
solve, release its claims by hand with the reason.

## Why
A memo on a container's disk dies with the container, so every fresh session
pays every cold solve again — and the gates that need those results get
skipped or deferred "to a container that has them". Two sessions landing on
the same stale memo at once pay it twice, in parallel, on the same answer.

## Story
In the originating repository, the heavy model gates re-solved on every fresh
container; some result families took hours, and a document's generated
tables were left to a drift gate "on a container that has the memos". The
memos were already keyed by a hash of their code, which is exactly the
property that makes sharing them safe. A probe showed the session's git proxy
refusing a push to a custom ref namespace and accepting a forced replacement
of a branch under a lease, which set the storage design.

## Install
Vendor [tools/result_cache.py](https://github.com/alex137/BestPractice/blob/staging/tools/result_cache.py) with
[tools/lease_board.py](https://github.com/alex137/BestPractice/blob/staging/tools/lease_board.py) and
[tools/branch_store.py](https://github.com/alex137/BestPractice/blob/staging/tools/branch_store.py). Each memo site gets **two
calls**: `ready(path)` in place of its existence check — a False answer
means this session solves, and the solve lease is already taken — and
`publish(path)` after writing the memo. A memo that accumulates across calls
passes `claim=False`. The file name must carry the key. A host shim sets
`REMOTE` and `BRANCH`, and configures the lease board the cache imports; a
claim left by a solve that fails, or by a smoke run that writes no memo, is
released at exit; one killed by a signal is not (Detail).
