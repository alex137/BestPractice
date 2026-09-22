---
slug:              todo-2026-09-22-precedent-individual-dedup-points-at-itself
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-22
closed:            null
---
## What

- <a id="precedent-individual-dedup-points-at-itself"></a>**precedent-individual's
    `practices/deliverables-carry-no-process.md` carries `status: deduplicated`
    with `in_force_at: deliverables-carry-no-process` -- pointing at its own
    slug, not at whatever practice it was actually deduplicated into.**
    Surfaced by `tools/verify_harness.py --as-ci` here (this repo, run
    against the real four-source pipeline): "deliverables-carry-no-process
    (precedent-individual): status: deduplicated names in_force_at:
    'deliverables-carry-no-process', but that slug does not resolve IN
    FORCE against the declared sources. A surviving copy that is itself
    dropped, shadowed or unreachable is not a surviving copy."

    Predates this session (`git log` on the file: PR #168, "Move the dedup
    ledger proposal to BestPractice, now that it's built") -- not caused by
    anything landed today. Not fixed today either: the file lives in
    precedent-individual, a private repo, and the actual correction (which
    slug this practice really survives as) needs someone who knows that
    history to answer rather than a guess from this repo.

## How It Closes

precedent-individual's `deliverables-carry-no-process.md` either names a
real, in-force `in_force_at` slug, or drops the `deduplicated` status if
nothing actually superseded it. `verify_harness.py --as-ci`'s
cross-source-consumer check stops naming it.

## Notes

2026-09-22: filed from BestPractice after `verify_harness.py --as-ci`
surfaced it mid-session, while pushing unrelated changes here and to
precedent-individual. Not raised in precedent-individual itself since this
repo cannot write there beyond what this session already pushed.
