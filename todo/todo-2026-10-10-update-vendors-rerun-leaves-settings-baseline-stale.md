---
slug:              todo-2026-10-10-update-vendors-rerun-leaves-settings-baseline-stale
kind:              analysis
domain:            engine
severity:          minor
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        Morgan, whether to fix it now
noted:             2026-10-10
closed:            null
---
## What

When Update Vendors stops with LEFT FOR YOU and the person fixes what it
left, the rerun finishes, and then the public-safe scrub gate
([practice_audit.py](../tools/practice_audit.py)) refuses the repository: `.claude/settings.json`
changed during the first run, and its baseline in `process/manifest.json`
still holds the old hash. The rerun never re-records it.

Found on 2026-10-10 doing Update Vendors on two voice-pack repositories
that were still on `pre-staging`; both needed
`python3 tools/practice_audit.py --update-baseline --entry .claude/settings.json`
by hand before the second pass would go through.

## Fix wanted

The step in [tools/precedent_update.py](../tools/precedent_update.py) that
rewrites `.claude/settings.json` re-records that entry's baseline itself,
on the first run and on every rerun, with a harness test that stops a run
at LEFT FOR YOU, reruns it, and expects the scrub gate to pass.

## Notes

Not fixed in the session that found it because nobody asked for it there;
offered to Morgan.
