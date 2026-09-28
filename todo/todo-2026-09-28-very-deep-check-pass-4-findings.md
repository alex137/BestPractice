---
slug:              todo-2026-09-28-very-deep-check-pass-4-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-28
closed:            null
---
## What

What the 2026-09-28 very deep check's pass 4 found and the same day did not
act on. The branch counts it rests on were re-derived in full clones (the
tool's own counts were inflated by a fetch that made full clones shallow,
fixed that day).

- **Branches, for Morgan's click** (a session never deletes a remote
  branch): close `claude/chief-of-staff-uncommitted-review-ppt6v0` and
  `claude/harness-clone-count-1i9qoq` (BestPractice), every
  `claude/gracious-cannon-c0viqp` in the four sets, and the fully landed
  branches `record/stale_branches.md` lists. Keep
  `claude/graduate-synonym` and `claude/rename-covers-names` (PR #720). Ask
  Alex about `claude/file-sharing-service-spec-0m9c7p` (issue #394).
- **For Morgan:** cherry-pick `claude/cross-session-vocab-phrase-iu7hxa`
  ("Response Please", decided 2026-09-22) or let it go.
- **Backlog asks for Morgan:** propose close for
  `todo-2026-09-10-review-skill-level-permissions`,
  `todo-2026-09-15-check-default-cc-environment-staleness` and
  `todo-2026-09-17-weekly-very-deep-check-trigger-decision` (recommend
  "not pursued", per `crons-are-a-last-resort`); and ask about
  attach-private-sources, source-repo-consumes-no-catalogue,
  actions-as-enforcement-layer, github-issues-for-open-items,
  reply-check-rollout, all overtaken.
- The BLOCKED-ON-GONE scanner in `very_deep_check.py` resolves
  `process/upstream` and `tools/ENGINE_MANIFEST.json` against BestPractice's
  own tree, so both rows are false positives.
- The gotcha `github-actions-rejects-yaml-anchors-python-accepts` may be
  obsolete; one dispatch test would settle it.
- **No run has ever completed the full sequential catalogue judgment**
  (`full_practice_audit.py`: 216 active practices, 81 judgment-only).
