---
slug:              todo-2026-10-05-very-deep-check-pass-4-findings
kind:              analysis
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
noted:             2026-10-05
closed:            null
---
## What

What the 2026-10-05 very deep check's pass 4 (catalogue, backlog, branches)
found and did not fix. Covered: every non-long-lived branch in all six
repositories, from full clones; 46 overlapping practice pairs, each judged;
the frontmatter of all 152 open items, with about 25 blockers or closing
conditions actually tested; every `retires_when`; the scope of all 157
active on-demand universal practices.

Fixed the same day: six open items closed on their own conditions, and
`item-closes-on-its-condition` now routes from `todo/todo-*.md`.

- **For Morgan: the folded repo-maintenance set's `default-branch` still
  wins wherever the set is declared.** A shared copy beats universal's by
  slug, and the set's copy still says to set the default branch to `main`,
  while universal's says the trunk may have any name (2026-10-05). That is
  BestPractice itself today. Deduplicating that one copy now, ahead of the
  other ten, fixes it; see
  [the fold item](todo-2026-10-05-move-repo-maintenance-into-universal.md).
- **For Morgan: retire both folded sets together.** Two repo-maintenance
  stubs resolve only through working-style's stubs, so dropping one set
  without the other leaves them pointing nowhere. The sets are still
  declared by BestPractice, the individual set, the writing set and each
  other.
- **For Morgan: three branches need a call.**
  `claude/upstream-bug-fix-review-ltbiy8` adds an approved `upstream-review`
  practice and tool, nothing equivalent exists, and it is 520 commits
  behind: cherry-pick it, or say "Root issues" replaced it.
  `claude/file-sharing-service-spec-0m9c7p` carries the only copy of a
  `share/` spec for an open issue: ask Alex. The ladder set's
  `merge-takes-vendor-update` branch is unblocked and merges cleanly; merge
  it after the ladder's deep check.
- **50 files under `todo/` still say `precedent-team-*`**, nine of them in
  `blocked_on`. Several are blocked only on read access to a private set,
  which a session now normally has; repoint the names and re-triage those
  as doable.
- **`todo-2026-09-21-pass-4-branch-verdicts-and-catalogue` has no closing
  condition**, and every branch it names but one is gone. Close it as
  superseded or give it one. `todo-2026-09-14-branch-merge-or-close-verdicts`
  can narrow to the issue #394 question.
- **No ruleset protects `main`, `staging` or `pre-staging`**, so the "a pull
  request from staging deletes staging" gotcha is still live.

## How It Closes

Each decision is made and recorded, and each other bullet is fixed or
recorded here as declined.
