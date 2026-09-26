---
slug:              todo-2026-09-06-retire-merge-target-practice
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "Morgan or Alex saying work moves to `main` (the practice's own expiry since 2026-09-14) -- no longer Alex's approval, which main stopped needing on 2026-09-26."
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-09-06
closed:            null
---
## What

- <a id="retire-merge-target-practice"></a>**Retire [local/practices/merge-target-is-beta-branch.md](../local/practices/merge-target-is-beta-branch.md)
    (and its check at
    [local/tools/checks/check_merge_target_is_beta_branch.py](../local/tools/checks/check_merge_target_is_beta_branch.py),
    and the pointer in [AGENTS.md](../AGENTS.md)'s opening paragraph) the
    moment Alex reviews and merges `precedent-beta-v01` into `main` for
    real.** Delete the practice file, delete the check script, and remove
    the [AGENTS.md](../AGENTS.md) pointer, all in that same PR. (The check
    moved out of [tools/precedent_check.py](../tools/precedent_check.py) on
    2026-09-06 — it is vendored into every consuming repo, and a check
    about THIS repo's own beta branch has no business running in
    somebody else's. Retiring it is now deleting two files, not editing
    the shared engine.) **Blocked on:** Alex's review
    and approval of `precedent-beta-v01` for the real phase-7 merge into
    `main` — not something to anticipate or do early.

    **That condition was met on 2026-09-14** — Alex merged
    [pull request #367](https://github.com/alex137/BestPractice/pull/367)
    ("Merge Precedent (precedent-beta-v01) into main"), tree-identical to
    this branch at `3386318`, and `main` has carried all of Precedent
    since. Found by the 2026-09-14 very deep check, whose `EXPIRING
    PRACTICES` section asked exactly this question. **What is now the
    decision, and it is not this item's to take:** this branch has moved
    64 commits past the merged point already, so retiring the practice
    means choosing where work lands next — switch to `main` now
    (`base_branch` in [precedent.json](../precedent.json) flips, the catalogue's
    ≈134 absolute links are rewritten by one `sed`, this practice and its
    check are deleted, the `TEMPORARY` paragraph leaves
    [AGENTS.md](../AGENTS.md), and the 64 commits go across as a second
    merge-back by the same recipe) or keep landing here until a named
    second fold-in. The session's recommendation is the first: every day on
    the branch after the merge is another fold-in to rehearse, and the
    recipe is proven. **Disposition:** ask (2026-09-14, the very deep check;
    the question is Alex's and Morgan's together, since it decides which
    branch adopters and check-ins target)

    **Answered 2026-09-14, and the answer is neither of the two above.**
    Morgan: *"work should still land to the precedent-beta-v01 branch; but I
    will regularly merge the precedent branch with main"* (`strength:
    decided`). So the branch stays the landing branch, `main` takes it by
    his regular merges (the histories are joined since the same day, so
    each is an ordinary merge), and this practice's expiry is reworded from
    "when the branch is merged into main" — which has now happened and will
    keep happening — to "when Morgan or Alex says work moves to main". The
    retirement steps stay as written. **Disposition:** wait (2026-09-14,
    Morgan's answer above)

    **What that merge will actually look like, rehearsed 2026-09-07 in a
    throwaway worktree and thrown away.** Two things worth not
    re-deriving under time pressure:

    - **Expect ≈125 conflicting files, and read them as divergence rather
      than damage.** `main` is still the pre-restructuring tree and lacks
      roughly 84,000 lines, so on nearly every one of them `precedent-beta-v01`
      is the correct side. The count is a snapshot and will drift — beta
      moved twice during the hour this was measured — but the shape will
      not. Newer work merges cleanly precisely because `main` has never
      seen it: of everything `philosophy/` and its repo-local practices
      added, only [tools/routing_scope.json](../tools/routing_scope.json)
      conflicted.
    - **The revert trap DOES fire. This bullet said the opposite until
      2026-09-07, because the rehearsal behind it sampled the one class of
      file that survives.** `main` merged PR #89 and then reverted it
      (`97ed078`); `precedent-beta-v01` merged *the same branch* as PR #91.
      Those commits are therefore ancestors of **both** branches, with
      `main` holding the later revert — the textbook setup for content
      silently failing to come back at merge time. The consequence is that
      `1ff6a7e` is the merge base, so a merge replays only what this branch
      did after 2026-09-03 and takes `main`'s deletion for everything
      older. **Two classes of file come out of that, and only one is
      visible.** A file this branch touched again since the merge base
      conflicts (`modify/delete`) and stops the merge — that is the ≈125
      above. A file it has *not* touched since presents no change from this
      side at all, so git has no disagreement to report and applies the
      deletion **silently**. Re-measured 2026-09-07 against `e8341e2`:
      **507 of this branch's 893 files are absent from the merge result
      with no conflict raised** — 496 under `evals/`, plus
      [templates/leak-blocklist.txt.template](../templates/leak-blocklist.txt.template),
      [templates/hooks/pre-push](../templates/hooks/pre-push),
      [tools/section_split.json](../tools/section_split.json),
      [tools/practice_metadata.json](../tools/practice_metadata.json),
      [decisions/README.md](../decisions/README.md),
      [decisions/2026-09-01-relax-private-repo-isolation.md](../decisions/2026-09-01-relax-private-repo-isolation.md),
      [.github/ISSUE_TEMPLATE/practice-candidate.md](../.github/ISSUE_TEMPLATE/practice-candidate.md)
      and the four files under
      [documentation/examples/practice-set/](../documentation/examples/practice-set/)
      (then at `examples/practice-set/`). **The miss is worth
      understanding, because the next rehearsal will be tempted to repeat
      it**: the earlier pass checked
      [tools/routing_audit.py](../tools/routing_audit.py) and
      [practices/routing-audit.md](../practices/routing-audit.md), which this
      branch touched 3 and 4 times since the merge base. They are in the
      surviving class by construction. Sampling files a rehearsal has
      recently worked on selects for exactly the files that cannot fail —
      the question is only answered by diffing the whole merge result
      against this branch's tree.
    - **The merge to run instead, measured the same day at zero
      conflicts.** Branch off `main`, revert the revert, then merge:
      `git checkout -b phase-7-merge main`, `git revert 97ed078`,
      `git merge precedent-beta-v01`. That came back **0 conflicts and a
      tree byte-identical to `e8341e2`** — an empty `git diff` against this
      branch.

      **That figure is no longer true, and the way it went stale is the
      point.** Re-rehearsed whole-tree 2026-09-11, the same three commands:
      **2 conflicts**, in [tools/doc_lint.py](../tools/doc_lint.py) and
      [tools/model_audit.py](../tools/model_audit.py). Both are real work on
      both sides of the same function, not noise — `main` carries an
      anchor-lint check (`check_anchors`) this branch does not have, this
      branch carries broken-link and heading-skip checks `main` does not,
      and the merge asks which list `main()` builds. Both must survive; the
      resolution is a union, not a pick. The cause is
      [`7d8f5a6`](https://github.com/alex137/BestPractice/commit/7d8f5a6)
      landing on `main` in the 2026-09-08 carry, which is also why the
      unmerged branch `claude/sync-practices-54-55-x2w4n3` is **not**
      unlanded work: its tip is that commit, already on `main`, and
      `git cherry` calls it unique only because it compares against this
      branch. Close that branch.

      **A measured number about two moving branches is true on the day it
      was measured and nothing re-runs it.** The 0-conflict figure was
      right on 2026-09-07 and wrong by 2026-09-08, and it sat here as fact
      for three days. Re-rehearse whenever
      [tools/precedent_upstream_check.py](../tools/precedent_upstream_check.py)
      reports `origin/main` has moved — that notice is already printed at
      every session start, and it is the trigger this measurement never
      had. Opening *that branch* as the pull request is what keeps the
      un-revert off `main` until Alex approves: both commits arrive
      together in one merge, so `main` flips from no-Precedent to
      all-of-Precedent exactly once, at the moment he says yes. A straight
      `git merge precedent-beta-v01` onto `main` is the move to avoid.
    - **The same trap points the other way, and that half is live now
      rather than at phase 7.** Merging `main` into `precedent-beta-v01` —
      an ordinary-looking "sync the branch with main", which any session
      might reach for — raises the same 125 conflicts and silently deletes
      the same 507 files *from this branch*. Measured 2026-09-07:
      `evals/` went from 623 files to 127, and
      [decisions/README.md](../decisions/README.md) vanished, with no conflict
      and no message for either. Nothing on this branch needs that merge
      before phase 7; `main`'s only three commits since the merge base are
      the bad merge, the revert, and the revert's own pull request merge,
      so there is nothing there to want.

## How It Closes

Not open until: Morgan or Alex says work moves to `main`. Alex's approval stopped being part of this on 2026-09-26 (Morgan: *"Alex said we no longer need his authorization to post to main so please remove that"*, strength: decided).

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.

2026-09-26: blocked_on, waiting_on and How It Closes moved off Alex's approval, which `main` no longer needs; the condition is the practice's own expiry, set 2026-09-14.
