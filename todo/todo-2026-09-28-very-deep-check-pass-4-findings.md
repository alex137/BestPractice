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

What the 2026-09-28 very deep check's pass 4 (catalogue, backlog, branches)
found and did **not** act on in the same run.

- **Branch verdicts** (full clones; the tool's own counts were inflated by a
  depth-limited fetch that turned full clones shallow, fixed in this run):
  close `claude/chief-of-staff-uncommitted-review-ppt6v0` (2 real commits,
  superseded) and `claude/harness-clone-count-1i9qoq` (1, overtaken); keep
  `claude/graduate-synonym` and `claude/rename-covers-names` (PR #720);
  ask Alex about `claude/file-sharing-service-spec-0m9c7p` (issue #394);
  confirm with Morgan whether `claude/cross-session-vocab-phrase-iu7hxa`
  ("Response Please", decided 2026-09-22) should be cherry-picked. In the
  practice sets, every `claude/gracious-cannon-c0viqp` (a stale engine and
  a path that does not exist) and the fully landed branches can be closed.
- The individual set's `claude/moved-practice-mentions` (`e82312d`) is
  unblocked: staging now carries the practices it points at.
- **Backlog asks:** propose close for `todo-2026-09-10-review-skill-level-
  permissions`, `todo-2026-09-15-check-default-cc-environment-staleness`
  (met in substance, no written condition), and `todo-2026-09-17-weekly-very-
  deep-check-trigger-decision` (recommend "not pursued", per
  `crons-are-a-last-resort`); overtaken and worth asking about:
  attach-private-sources, source-repo-consumes-no-catalogue,
  actions-as-enforcement-layer, github-issues-for-open-items,
  reply-check-rollout.
- The BLOCKED-ON-GONE scanner resolves `process/upstream` and
  `tools/ENGINE_MANIFEST.json` against BestPractice's own tree; both rows are
  false positives. A branch whose commits cancel out still reads as carrying
  unlanded work (filed 2026-09-21).
- `record/automated-actions.md`, which pass 4 asks for, exists in no repo; a
  draft was written in this run's scratch space.
- The gotcha `github-actions-rejects-yaml-anchors-python-accepts` may be
  obsolete; one dispatch test would settle it.
- **No run has ever completed the full sequential catalogue judgment.**
  `full_practice_audit.py` lists 216 active practices across six sources, 81
  judgment-only; this run did not judge them one by one.
