---
slug:              todo-2026-09-29-pre-staging-tier-skips-doc-sync
kind:              analysis
domain:            mechanism
severity:          medium
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "out of scope for the session that found it (local edits to received files); filed at the proposing session's request rather than folded into that work"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-29
closed:            null
---
## What

**A new practice can land on pre-staging with stale generated counts, and
only the Debut notices.** 2026-09-29: `stage-word-carries-its-step` landed
on pre-staging without `python3 tools/doc_sync.py --write`. Three generated
blocks went stale (the catalogue count in [spec/LOADER.md](../spec/LOADER.md),
[spec/ENFORCEMENT.md](../spec/ENFORCEMENT.md)'s enforced count, and the routing table in
[spec/ROUTING_REASONS.md](../spec/ROUTING_REASONS.md)). Every push to pre-staging passed, because the
basic tier and the changed-files step do not run doc_sync. The Debut's deep
check refused on it, and it was fixed in pull request #751. The drift is
fixed; the reason it could land is not.

## Measured

`python3 tools/doc_sync.py` on pre-staging at c1dd37f5, three runs in a
hosted container: 0.55 s, 0.55 s, 0.45 s. Cheap enough to run on every push
that could move a count.

## Proposal

The changed-files step of a push into pre-staging runs doc_sync (the drift
gate, not `--write`) when the push adds a practice file or changes a
practice file's front matter, the two changes that move the generated
counts. Running it on every pre-staging push would also be affordable at
half a second; the narrower trigger keeps the tier's promise of checking
only what the push changes.

Closes when a push into pre-staging that adds a practice without
regenerating the blocks is refused at that push, with a test that shows it.
