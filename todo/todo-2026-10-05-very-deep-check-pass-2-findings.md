---
slug:              todo-2026-10-05-very-deep-check-pass-2-findings
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
noted:             2026-10-05
closed:            null
---
## What

What the 2026-10-05 very deep check's pass 2 (mechanisms) found and did not
fix. Covered: the seven items the automated run raised, reproduced on
`main`, plus the fold seam and question 3 on four tools. Questions 1, 4-12,
16-19, 22 and 23 were not worked one by one (time-box; 16, 19 and 22 need
GitHub reads that were not budgeted).

Fixed the same day: BOOTSTRAP DRIFT refused to run on any branch main lacks
and the harness's process-wide allowance hid it; the fix sweep's copy of a
repo lost the repo's neighbours, so the ladder-words check reported the
individual set in violation of a rule it is exempt from; and the ORPHANS
section judged a check script by filename alone.

- **Bot-authored commits reach `main` because no gate sees a pull
  request's commits.** [check_commit_author.py](../tools/checks/check_commit_author.py) reads only commits on no
  remote, and stands down where no identity is declared, which is the CI
  state. Five commits by `noreply@anthropic.com` at +0000 landed in
  BestPractice on 2026-10-02 through a pull request merged on GitHub. Root
  fix: a bot-author half that refuses the harness's bot addresses even when
  the check stands down, scoped in CI to the pull request's range, run in
  the deep-check workflow's pull-request job, with a planted case.

  **Fixed 2026-10-06, except the workflow step:** the check now has a
  bot-author half that refuses a commit authored as one of
  [precedent_session_check.py](../tools/precedent_session_check.py)'s
  `BOT_EMAILS` (imported, not copied) whether or not a person is declared,
  takes a range (`--range A..B` or `PRECEDENT_CHECK_RANGE`), and runs alone
  with `--bot-authors-only`. Planted case:
  `check_bot_authored_commits_are_refused_where_no_person_is_declared`
  (fails on the old script: every case came back SKIPPED). The bot commits
  already on `main` stay as they are.

  **Waiting for Morgan's approval: one step in
  [deep-check.yml](../.github/workflows/deep-check.yml).** Without it,
  nothing runs the new half on a pull request. The step goes in the
  existing `precedent-check-and-sync` job, right after "Set up Python". It
  adds no job, trigger or run, only a few seconds inside a job that already
  runs, and the repository is public. Editing a workflow file is his call
  under [ci-workflow-approved](../practices/ci-workflow-approved.md), so it
  was not made:

  ```yaml
        - name: Refuse commits authored by the harness's bot
          if: github.event_name == 'pull_request'
          run: python3 tools/checks/check_commit_author.py --bot-authors-only --range "origin/$GITHUB_BASE_REF..HEAD"
  ```
- **The "harness check in a linked worktree turns the main clone bare"
  trap has no prevention.** Its gotcha says the leaking call was never
  traced, and it is still live: this run had to forbid worktrees. Trace it,
  and make [verify_harness.py](../tools/verify_harness.py) refuse to start from a linked worktree, with
  a planted case.

  **Fixed 2026-10-06, at the cause rather than by refusing worktrees:** the
  leak is `GIT_DIR`, which `git bisect run` exports. Every fixture inherited
  it, so a fixture's `git init --bare` re-initialised the worktree's git
  directory as bare, in the config the main clone shares. The harness now
  drops git's repository variables at start. Planted case:
  `check_harness_drops_inherited_git_repository_variables` (fails on the
  old harness; its control reproduces the trap without the harness). It
  does not refuse a linked worktree: Promote and the merge check run the
  full push check, harness included, in one. The
  [gotcha](../gotchas/gotcha-2026-10-01-a-harness-check-run-in-a-linked-worktree-turns-the-main-clone-bare.md)
  carries the trace.
- **GENERATED FILES reports six false candidates, and will every run.** It
  matches a basename written under any directory and the bare word
  "generated". Match writes rooted at the repo and a real claim ("generated
  by", "do not hand-edit"), and give
  [tools/generated_files.json](../tools/generated_files.json) a
  `not_generated` list with reasons.
- **INCIDENT COVERAGE greps only for the slug.** Nine of the twelve
  uncited gotchas name their own planted case in their Fix section, and
  each case exists. The section should read those names and confirm them.
  Two have no written answer yet: auto mode refusing a bare promote (a
  person's managed setting) and stale shallow entries (a manual recovery);
  each needs "nothing, and deliberately so" written down.
- **`approved_by: "pending PR review"` outlives the merge.**
  [tools/precedent_move.py](../tools/precedent_move.py) writes it and
  nothing rewrites it; 18 practices carried it until this run fixed the
  text by hand. A merge-gate check that refuses it on the base branch, or a
  rewrite at landing, is the root fix.
- **The writing and ladder sets differ from what the generator writes
  today in eight files each** (AGENTS.md, MAP.md, GLOSSARY.md, CODEOWNERS,
  precedent.json, precedent-source.json, `tools/generated_files.json`, the
  individual-source hook), now that BOOTSTRAP DRIFT runs. Not judged file
  by file in this run.

## How It Closes

Each bullet is fixed or recorded here as declined, with the reason.
