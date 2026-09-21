---
slug:              todo-2026-09-21-structural-only-route-3-not-exercised
kind:              manual
domain:            testing
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

**`check_structural_only_actually_drops_the_private_half` covers two of
the three routes it names, and the third is guarded but never fires.**

[leak_gate.py](../tools/leak_gate.py)'s self-heal reloads the FULL
blocklist when a run has hits, which silently undid `--structural-only`.
It is now guarded by `not structural_only`. But in the harness fixture
`_try_refresh_private_blocklist_clone()` returns `False` — there is no git
clone to fast-forward — so the reload does not run **even with the guard
removed**. Confirmed by reverting the fix: the check fails on route 2 and
passes route 1; route 3 is silent either way.

## Why It Matters

A case that cannot fail is a case that proves nothing, and this one reads
like it covers the route it names. That is worse than an absent case:
somebody deleting the `not structural_only` guard would see the harness
go green.

It is also the exact shape this repo keeps relearning — a detector
verified only against a tree where the code path is unreachable is
indistinguishable from a broken one.

## What Would Close It

A fixture whose private blocklist is a real git clone, behind its origin
by one fast-forwardable commit, so `_try_refresh_private_blocklist_clone()`
returns `True`. Then assert that under `--structural-only` the reload does
not happen: the refreshed private pattern must not appear in the output.

Cheaper alternative if that proves fiddly: have the check import
`leak_gate` and assert the guard's presence structurally. **That is a
weaker test** — it checks the code says the right thing rather than does
it — and should be named as such if taken.
