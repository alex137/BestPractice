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
    runs recorded (recommending the ask, never making it). Its 3 commits
    (corrected 2026-09-19: recorded as 41 by two shallow-clone reads;
    see the issue's own correcting comment) exist on no other branch, so
    it is the one branch here whose closure would really discard something.
  - `themorgan/precedent-individual: precedent/engine-refresh-c6c885033a9f` —
    **CLOSE** as decided 2026-09-08; it pins an engine commit since
    superseded, so merging it would refresh that set backwards.
  - `alex137/BestPractice: claude/team-sets-carry-code-x2w4n3` — **CLOSE**,
    added 2026-09-19: its proposal, `spec/PRACTICE_SETS_CARRY_CODE.md`, was
    dispositioned in [PR #444](https://github.com/alex137/BestPractice/pull/444)
    ("Superseded by #455, which implements the general form … Closing."),
    and [PR #455](https://github.com/alex137/BestPractice/pull/455) is
    merged and its content is on `precedent-beta-v01`
    (`tools/checkin.py --source`, per-row defaults in
    `spec/INSTALL_QUESTIONS.md`, `precedent-source.json`). Nothing is
    discarded by deleting it.

  **Blocked on:** Morgan, for four branch deletions now (one added
  2026-09-19), and nothing else. A session cannot make them: `git push
  origin --delete` is refused by the permission classifier as `[Git
  Destructive]` before it reaches GitHub — a different wall from the 403
  [record/GOTCHAS.md](../record/GOTCHAS.md#g39) describes, and one no
  retry or alternate tool gets around. Links were handed to him
  2026-09-14; the fourth link is in this run's own
  [spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md).

  **Also found 2026-09-19, pass 4:** `agents-cross-tier-and-git-author-gotchas`,
  `claude/a-spawned-session-can-answer`, `claude/apply-writes-neither-half`
  and `claude/bestpractice-migration-cleanup-i5s118` — reported by earlier
  runs as carrying 210-485 unlanded commits each — are plain, fully-landed
  ancestors of both `precedent-beta-v01` and `main`, and are **already
  deleted from the remote**. The false counts came from two compounding
  bugs in `tools/very_deep_check.py`, fixed the same day: `_fetch_all_heads`
  never pruned stale local remote-tracking refs for branches already
  deleted upstream, and `_unmerged_row` computed its `ahead` count before
  confirming the merge-base actually resolved in this clone rather than at
  a shallow boundary. No deletion needed for these four; they are already
  gone. `record/stale_branches.md` needs a regeneration with the fixed
  tool before it is read again.

## How It Closes

Not open until: Morgan, for three branch deletions, and nothing else. A session cannot make them: `git push origin --delete` is refused by the permission classifier as `[Git Destructive]` before it reaches GitHub — a different wall from the 403 [record/GOTCHAS.md](../record/GOTCHAS.md#g39) describes, and one no retry 

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

2026-09-19: pass 4 of a very deep check re-read every branch in this
checkout carrying reported unlanded work, on a fully-unshallowed clone.
Found and corrected the stale "41 commits" figure on issue #394 (real: 3),
found and added `claude/team-sets-carry-code-x2w4n3` as a fourth CLOSE
(superseded by merged PR #455), and found the four huge-looking counts
(210-485) on other branches were a shallow-clone artifact against
already-deleted branches -- fixed at the source in
`tools/very_deep_check.py`, no deletion needed for those four. Two other
branches from this session's own read got a real MERGE recommendation
rather than a verdict acted on here --
`claude/bootstrap-drift-pycache-exclusion-kgtw57` (a real, traced bug fix
PR #427 deferred, half already landed independently) and
`claude/harness-clone-count-1i9qoq` (a self-contained drafted proposal,
`spec/VERIFY_HARNESS_SCOPING_PLAN.md`) -- left for a human decision since
merging someone else's un-reviewed branch is bigger than what this pass
does on its own.
