---
slug:              todo-2026-09-14-branch-merge-or-close-verdicts
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "Morgan, for three branch deletions, and nothing else. A session cannot make them: `git push origin --delete` is refused by the permission classifier as `[Git Destructive]` before it reaches GitHub — a different wall from the 403 [record/GOTCHAS.md](../record/GOTCHAS.md#g39) describes, and one no retry "
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-09-14
closed:            null
---
## What

- <a id="branch-merge-or-close-verdicts"></a>**The unmerged-branch verdicts are acted on; three branch deletions are
  the only part left, and no session can do them.** Morgan delegated the
  four, 2026-09-14. This item replaces an earlier version that named
  `claude/pre-launch-audit-fixes-7wumzx` in two private sets — that
  description was already stale against
  [spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md)'s own pass 4, which is
  the record, and reading the item instead of the record is what kept it
  stale.

  - `alex137/BestPractice: philosophy-bidirectional-slugs` — **merged**
    2026-09-11, zero commits ahead. No verdict was ever owed on its content;
    only the branch remains.
  - `alex137/BestPractice: claude/sync-practices-54-55-x2w4n3` — **CLOSE**
    stands, and it is now checked rather than assumed: its tip `7d8f5a6` is
    an ancestor of `origin/main`, so nothing is discarded with it.
  - `alex137/BestPractice: claude/file-sharing-service-spec-0m9c7p` —
    **raised with Alex as [issue #394](https://github.com/alex137/BestPractice/issues/394)**,
    2026-09-14, with the three answers laid out. That closes the drift two
    runs recorded (recommending the ask, never making it). Its 41 commits
    exist on no other branch, so it is the one branch here whose closure
    would really discard something.
  - `themorgan/precedent-individual: precedent/engine-refresh-c6c885033a9f` —
    **CLOSE** as decided 2026-09-08; it pins an engine commit since
    superseded, so merging it would refresh that set backwards.

  **Blocked on:** Morgan, for three branch deletions, and nothing else. A
  session cannot make them: `git push origin --delete` is refused by the
  permission classifier as `[Git Destructive]` before it reaches GitHub —
  a different wall from the 403 [record/GOTCHAS.md](../record/GOTCHAS.md#g39)
  describes, and one no retry or alternate tool gets around. Links were
  handed to him 2026-09-14.

## How It Closes

Not open until: Morgan, for three branch deletions, and nothing else. A session cannot make them: `git push origin --delete` is refused by the permission classifier as `[Git Destructive]` before it reaches GitHub — a different wall from the 403 [record/GOTCHAS.md](../record/GOTCHAS.md#g39) describes, and one no retry 

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
