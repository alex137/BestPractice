---
slug:            gotcha-2026-09-26-the-carry-check-counted-upstream-s-own-deletions-as-lost
status:          live
noted:           2026-09-26
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

`checkin.py record` refuses an ordinary Update Vendors with a long list of
`LOST from <file>:` lines and "pending vendored additions are MISSING from
the landed upstream tree", while `checkin.py status` reads 0 files differing
against the clone. Every listed line turns out to be one upstream removed
itself.

## Story

**2026-09-26, a real consumer** on the tiered route (work lands on
pre-staging, the base branch `main` takes it by Promote). An update moved
the vendored tree from one upstream `main` commit to the next, and `record`
refused. Replayed afterwards on the consumer's real history, the check
flagged **301 lines, all of them upstream's own deletions** between the two
syncs -- for example the old wording of the Promote row in
[documentation/DAILY_HABITS.md](../documentation/DAILY_HABITS.md).

The carry check reads the vendored tree COMMITTED on the consumer's base
branch, and took "pending local additions" to be that tree minus the
upstream tree at the manifest's `upstream.commit`. That is only right when
the committed tree was mirrored from that same commit. On the tiered route
it usually was not: the base branch still held the previous sync, and the
manifest (hand-written, as the three updates before it had been) already
named the new one. Every line upstream changed in between looked local;
every line upstream deleted looked lost. The reverse gap -- base branch
ahead of a stale stamp -- produced 45 false lines on the same history.

The session could not confirm the lines one by one (its harness's auto-mode
check refused the ad-hoc script), so it handed the refusal to the person.
The three updates before it had stepped around the same guard by writing
`upstream.commit` by hand, which is how a guard stops guarding.

## Fix

In the tool ([tools/checkin.py](../tools/checkin.py), `_carry_check`), two mechanisms:

1. A line is pending only if it is absent from the upstream tree at EVERY
   commit the committed tree could have come from: the working manifest's
   `upstream.commit`, plus the `synced_from` and `commit` recorded in the
   manifest committed on the same ref.
2. A line still missing after that which an upstream commit between one of
   those and the clone's HEAD deleted is reported as upstream's own
   deletion, counted in one line, and not refused.

A line upstream never had is still refused and named. Pinned by
[tools/verify_harness.py](../tools/verify_harness.py)'s `check_carry_check_never_counts_upstream_deletions`,
which fails five of its six cases against the old code.
**A consumer gets the fix on its next Update Vendors**; until then a
refusal of this shape is almost certainly this bug, and running the new
tool from an up-to-date clone confirms it.
