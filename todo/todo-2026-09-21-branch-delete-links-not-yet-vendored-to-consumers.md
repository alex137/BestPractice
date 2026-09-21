---
slug:              todo-2026-09-21-branch-delete-links-not-yet-vendored-to-consumers
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "an \"Update Vendors\" run per consuming repo -- this session is scoped to BestPractice alone and cannot reach them"
noted:             2026-09-21
closed:            null
---
## What

**The branch-delete-link work landed in BestPractice's originals only. Every
consuming repo still carries the pre-change copies**, and will until an
"Update Vendors" run reaches it
([vendor-update-runbook](../practices/vendor-update-runbook.md)).

What has to travel, and by which route:

| Thing | Where it lands in a consumer |
|---|---|
| [practices/branch-delete-links.md](../practices/branch-delete-links.md) (new) | `process/upstream/practices/` |
| [practices/chief-of-staff.md](../practices/chief-of-staff.md) (fleet sweep added) | `process/upstream/practices/` |
| [practices/very-deep-check.md](../practices/very-deep-check.md) (scope bounded, mechanism cited) | `process/upstream/practices/` |
| [tools/very_deep_check.py](../tools/very_deep_check.py) (substring check, success note) | `tools/`, tracked in that repo's `tools/ENGINE_MANIFEST.json` |

**Do not hand-edit a vendored copy to get there.** That produces exactly the
drift the manifest exists to catch, and `practice-export-loop` will report the
copy as diverged from its baseline rather than as updated.

## Why It Is Filed Rather Than Done

The session that landed the change had GitHub access scoped to
`alex137/BestPractice` and could not reach a consuming repo to run the
sequence in it. The runbook's own first step is making the SOURCE clone
current, which is where any consumer's run starts anyway — so nothing here
is half-done, it is just not started.

## Closing Condition

Every consuming repo's `process/upstream/practices/` holds the three practice
files at their current content, and its `tools/ENGINE_MANIFEST.json` records
[very_deep_check.py](../tools/very_deep_check.py) as synced rather than
diverged.
