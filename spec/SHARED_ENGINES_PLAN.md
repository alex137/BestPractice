---
title:         Two shared engines -- a branch store and a content-hash record
kind:          proposal
status:        drafted
opened:        2026-09-29
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The first run of practice judgment-check-or-tool: two mechanisms that each exist more than once across the catalogue and its private sets, what each copy does, what a merged engine keeps, and how each caller moves over. A plan for the owner to decide on; no engine is written yet."
---

# Two shared engines -- a branch store and a content-hash record

This is the first application of
[judgment-check-or-tool](../practices/judgment-check-or-tool.md). Two
mechanisms each exist more than once. **Nothing here is built yet**; the
merge is the owner's call.

## 1. The branch store

**What it is:** small records kept on a dedicated branch of the shared
remote, written with git plumbing so the working tree is never touched,
with `git push` as the lock.

**The copies today:**

| Tool | Branch | Records | Own plumbing |
|---|---|---|---|
| [tools/lease_board.py](../tools/lease_board.py) | `coord` | one JSON file per lease | `_git`, `_fetch`, `_read`, `_commit` (private index file, `commit-tree`), `_push`, `_transact` (retry on a rejected push) |
| [tools/result_cache.py](../tools/result_cache.py) | `result-cache` | memo files plus an `index.json`, pruned to a size budget | its own `_git`, `_fetch`, `_index`, `_pull`, and an inline private-index commit and push in `publish()` |

The result cache already uses the lease board for its **locking** (a
cold solve takes a lease so a second session waits). What is duplicated
is the **storage**: two copies of fetch, read-a-file-at-the-tip,
write-files-through-a-private-index, commit, push, retry. Both retry the
same way (re-fetch, rebuild, push again). They differ in one real
decision: the lease board commits on top of the tip, so the branch keeps
its history (who held what, and why it was released, is in its log); the
result cache writes a commit with no parent and pushes it with
`--force-with-lease` on the tip it read, so the branch never grows past
its size budget.

**The engine:** `tools/branch_store.py`, one class:

```
not for pasting -- the proposed interface
store = BranchStore(remote="origin", branch="coord", repo=None, retries=5,
                    history=True)
store.tip()                       # fetch; the tip commit, or None if no branch
store.list(dir)                   # names under dir at the tip
store.read(path, binary=False)    # a file at the tip, or None
store.transact(mutate, message)   # mutate(tip_reader) -> (writes, deletes);
                                  # commit through a private index, push,
                                  # on rejection re-fetch and re-run mutate
```

`writes` maps a path to bytes or to a local file (the result cache's
memos are large and are hashed in with `hash-object -w PATH`, never read
into memory). Both tools keep their own policy — lease semantics, holder
identity, the cache's size budget and pruning — and call the store for
everything that touches git.

**What the merge keeps from each copy:** both history modes, as a
constructor switch (`history=True` commits on the tip; `history=False`
writes a parentless commit and pushes with a lease on the tip it read);
the lease board's `mutate` callback, so a check runs against the tip it
is about to replace; the result cache's file-path writes. The cache's
`KEEP` and size pruning stay in the cache.

**The local lock stays out.** The result cache's pid lock file (a second
process on the same machine waits for the first) is a same-machine
mechanism, not a branch one. It could become a small helper of its own
if a second user appears; today it has one.

## 2. The content-hash record

**What it is:** hash a set of inputs, store the hashes beside a name,
and later answer *does this record still hold?* — and if not, which
input moved.

**The copies today:**

| Tool | What it records | Hashing |
|---|---|---|
| [tools/fact_ledger.py](../tools/fact_ledger.py) | per unit of a gate: code fingerprint, every file, listing, existence test and environment variable the run read, the result's hash, the hook version | at read time, inside the working process |
| a drift check in a private practice set | per released document: its content hash at release, compared on every audit | at audit time, after normalizing the text |
| build manifests in the same private set | per built package: each input file's hash and the hash of every embedded figure, rolled into a short build code | at build time, after the same normalization |

The three disagree on details that matter. Only the ledger records the
version of the tool that recorded it, so a change to what it watches
invalidates old records. Only the private two normalize text before
hashing, so a line-ending change does not register as a change. The
ledger's records merge by union and verify themselves; the manifests are
immutable once written; the drift baseline is rewritten in place on
purpose.

**The engine:** `tools/content_record.py`, below the fact ledger rather
than replacing it:

```
not for pasting -- the proposed interface
rec = Record.of(root, inputs, normalize=None, extra={})   # hash now
rec.digest()                        # one short code over all inputs
rec.holds(root) -> (bool, [moved])  # re-hash; which inputs changed
rec.to_json() / Record.from_json()  # stored form, carries engine version
```

`normalize` is a per-input function the host supplies (the private set's
text normalization stays in its shim). Every stored record carries the
engine's version, taken from the ledger. The fact ledger keeps its
reads hook and its unit bookkeeping and stores its reads as a `Record`;
the drift check and the manifests become `Record`s with the host's
normalizer.

**What does not merge:** where records live and whether they may change.
Ledger lines merge by union; manifests are immutable; a baseline is
rewritten deliberately. Those stay with each caller.

## 3. How each caller moves over

One caller at a time, each with a check that it gives the same answer
on the same input before and after:

1. **Branch store, lease board first.** Its plumbing is the cleaner copy.
   Check: take, update, release and a forced push race on a scratch
   remote, before and after.
2. **Result cache onto the store.** Check: publish, pull and prune on a
   scratch remote; a memo round-trips byte for byte.
3. **Content record under the fact ledger.** Check: every committed
   ledger line in a consuming repository still holds after the move
   (the gate re-runs nothing on an unchanged tree).
4. **The private drift check and manifests** move in the private set,
   through its own review. Check: every stored manifest reproduces its
   build code, and the drift audit reports the same set before and
   after.

## 4. The practices that change

Once the engines exist, these practices shrink to how and when to use
them: [lease-in-flight-work](../practices/lease-in-flight-work.md),
[shared-result-cache](../practices/shared-result-cache.md),
[gate-ledger](../practices/gate-ledger.md),
[slow-steps-report-and-cache](../practices/slow-steps-report-and-cache.md)
(its memo-key half), and three or four in the private set.

## 5. What is not proposed

One runner for every gate (the fail-fast behavior now lives separately
in each gate) is a third candidate. It is left out: the gates differ
more in what they run than in how, and the copies have not drifted yet.
