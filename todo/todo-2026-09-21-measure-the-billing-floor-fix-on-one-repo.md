---
slug:              todo-2026-09-21-measure-the-billing-floor-fix-on-one-repo
kind:              manual
domain:            ci
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "the busiest consuming repo's vendor update finishing first — Morgan, 2026-09-21, sequencing"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

**A measured before/after on `precedent-individual`, as the controlled test
of the billing-floor theory.** Morgan, 2026-09-21: *"After [the busiest
repo] finishes, I want to do a test with precedent-individual that you
should write, because it's the second biggest offender."*

## Why This One, and Why A Test at All

**Five interventions before this all looked right and all missed.** Every
one attacked trigger frequency; the cost was per-job and structural. None
was measured afterward, which is why the miss took five rounds to notice
([spec/BILLING_FLOOR.md](../spec/BILLING_FLOOR.md)).

`precedent-individual` is the right subject: **468 billed minutes, 18.0% of
the whole account**, second only to the busiest consuming repo, and unlike
that one it is a practice set — so what is learned transfers to the other
three sets, which together add another 560.

It also has a clean intervention boundary. As of 2026-09-21 its
`precedent-check.yml` went from three jobs to one, and the remaining
`commit-identity.yml` (117 minutes; 118 runs, median 12 seconds against a
60-second floor) is proposed for folding into that job as a step.

## What the Test Has to Answer

**One question, stated before the data arrives so the answer cannot be
fitted to it:** did the per-job floor account for the spend, or did
something else?

The theory predicts, for the same pull-request volume:

- `precedent-check.yml` at 3 jobs → 1 job cuts that workflow by **about
  two thirds**, not by some smaller amount, and not by more.
- Folding `commit-identity.yml` in as a step takes its **117 minutes to
  approximately zero incremental** — a job already billed absorbs twelve
  more seconds free.
- Repo total **468 → roughly 76 a month**, once the already-deleted
  `views-drift.yml`'s historical 130 is excluded.

**Anything materially off those numbers falsifies something**, and the
falsification is the point. A result of "it went down a bit" is a failed
test, not a success: it would mean the floor is not the whole story and the
remaining cause is still unidentified.

## Design Constraints

- **Normalize by pull-request volume, not calendar days.** The prediction
  is per-trigger. A quiet fortnight looks like a successful fix and is not.
  Divide by runs, not by dates.
- **Record the baseline BEFORE the change lands**, from the usage export,
  per workflow, with the run count — not reconstructed afterward.
- **Name the confound:** the one-job merge and the fold land close
  together. Either measure between them, or predict and check the combined
  figure rather than attributing a share to each after the fact.
- **A shorter run than the baseline window is not comparable.** State the
  window length up front.

## What Would Close It

The write-up: prediction, method, baseline table, after table, and a plain
verdict on whether the numbers landed where the theory said. It goes in
[spec/BILLING_FLOOR.md](../spec/BILLING_FLOOR.md), which already carries the five failures — a sixth
entry saying "and this one was predicted, measured and confirmed" is what
turns that document from a post-mortem into something with a track record.

If it is NOT confirmed, that belongs there too, in the same words.
