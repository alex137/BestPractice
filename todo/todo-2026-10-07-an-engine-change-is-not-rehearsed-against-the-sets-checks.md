---
slug:              todo-2026-10-07-an-engine-change-is-not-rehearsed-against-the-sets-checks
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-07
closed:            null
---
## What

Commit 1ef31386 turned the individual set's startup hook into a stub that
hands off to the engine's `tools/individual-source-bootstrap.sh`. The
individual set's own `claude-web-bootstrap` check recognized a consumer's
install by two literals in that hook's text, which the stub no longer
carries. Every consumer that took the update was reported as having no
install, and its next merge failed on a file it never touched (reported
2026-10-07 by a session in a consuming repository; the check was fixed in
the individual set the same night).

The commit was rehearsed on a copy of a consuming repository, and that
rehearsal looked at the hooks. Nothing ran the declared sets' checks there.
[precedent_consumer_shape.py](../tools/precedent_consumer_shape.py) covers the other direction, a set's own
check tests run in a consumer's layout when the set changes, and
`practice-change-propagates` covers a practice's citations. Neither reaches
an engine change that alters a file a set's check inspects in a consumer.

## Proposed

A rehearsal tool, not a prose rule: when a batch into staging touches
`templates/**` or a file Update Vendors writes into consumers, build a
scratch consumer, apply the batch's Update Vendors to it, resolve the
person's declared sets, and run `precedent_check.py --full-sweep` there
against the same consumer on `main`'s engine. A finding only the batch
produces refuses the Debut and names the set and check, so the fix ships
in the same round, in the set that owns the check. It runs locally, at
Debut, where the sets are on disk; GitHub's runner has no private sources.

Open questions: which sample consumer (the template project, or a recorded
shape of a real one), and how long it adds to a Debut.

## How It Closes

Planting 1ef31386's stub against the old check makes the Debut refuse,
naming `claude-web-bootstrap`.
