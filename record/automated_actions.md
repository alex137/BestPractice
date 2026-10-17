---
title:         Automated actions and schedules
kind:          record
status:        closed
opened:        2026-10-17
closed:        2026-10-17
superseded_by: null
supersedes:    []
audience:      session
summary:       "Every automated action and schedule across the repos in force, and every path pass 4 looked at for deprecation, each with its verdict -- from the very deep check of 2026-10-17."
---

# Automated actions and schedules

Inventory from the very deep check of 2026-10-17, pass 4
([very-deep-check](../practices/very-deep-check.md)): every automated action
and schedule across the four repos in force (this one and the three sets it
declares), with a verdict each, and every path the pass looked at for
deprecation. It replaces the 2026-09-28 inventory, which said nothing fired
on a clock; **one workflow does now**, the daily run of the full suite here.
The next run reads this file first and re-examines only what changed.

## Workflows

Read from each repo's `origin/main` with `git ls-tree`. Last runs for the
scheduled trigger read once from GitHub's workflow-runs list for
`deep-check.yml`, filtered to `schedule`.

| Repo | Workflow | Triggers | Schedule | Last fired | Verdict |
|---|---|---|---|---|---|
| BestPractice | `.github/workflows/deep-check.yml` | `pull_request` into `main` (opened, reopened, ready for review, synchronize), `push` to `main`, `workflow_dispatch` | `17 7 * * *`, daily at 07:17 UTC, since 2026-10-12 | 2026-10-17 07:26 UTC, success; five scheduled runs (2026-10-13 to 10-17), all success, 11 to 15 minutes each | **Needed.** The one GitHub test on the way into `main`; the daily run checks the whole suite, which a change-scoped run cannot. Approved by Alex, 2026-10-12 ("yes on daily run"), pinned with its content in [precedent.json](../precedent.json)'s `github_ci_approved`. See the note below on where schedules are registered. |
| BestPractice | `.github/workflows/leak-gate.yml` | `push` to `main`, `workflow_dispatch` | none | not read | **Needed.** The structural leak gate for a merge made on GitHub, which never passes a session's own push gate. Approved by Morgan, 2026-10-11. |
| BestPractice | `.github/workflows/precedent-branch-cleanup.yml` | `workflow_dispatch` only | none | not read | **Needed, dispatch-only by design.** Started only by a person from the branch cleanup page (Morgan, 2026-10-16, decided: "NEVER run the cleanup automatically"). Not a half-finished decommissioning, which a dispatch-only workflow usually is. |
| the individual set and both shared sets | none | -- | -- | -- | Nothing to judge: no `.github/workflows/` on `main` in any of the three (`source-sets-run-no-ci`). The individual set's on-request `engine-refresh.yml`, judged in the 2026-09-28 inventory, is gone. |

**Where schedules are registered.** The individual set's
`crons-are-a-last-resort` asks for one list of every schedule in force in a
repo's instructions file or its map, updated in the commit that adds one.
Neither [AGENTS.md](../AGENTS.md) nor [MAP.md](../MAP.md) lists the daily
run; this file and the workflow's own header comment do. Raised with the
person rather than changed here: the rule is his, the repository is Alex's,
and the cron was Alex's approval.

## Session Routines

The account's session Routines and triggers are listed by the main session of
this run from the harness's own trigger list, not by this file's pass; no
repository holds them.

## Operating-system cron

`crontab` is not installed and no cron daemon runs (`pgrep cron` finds
nothing). The image still ships `/etc/cron.d/e2scrub_all` and
`/etc/cron.d/php`, and the container does not persist. **Not in force**; no
verdict owed.

## Paths looked at for deprecation

Method: every tracked `tools/*.py`, `tools/*.sh`, `tools/*.json` and
`tools/checks/*` file here, searched for its name in any other tracked file
outside the history directories (`todo/`, `gotchas/`, `record/`, `spec/`,
`decisions/`, and the generated [MAP.md](../MAP.md), [WHERE_THINGS_ARE.md](../WHERE_THINGS_ARE.md) and
[WHATS_NEW.md](../WHATS_NEW.md)). Only two came back with one reference or none. Each path
below was then read, and the doubtful ones run through
[tools/precedent_decommission.py](../tools/precedent_decommission.py) as an
audit; nothing was deleted.

| Repo | Path | Verdict |
|---|---|---|
| BestPractice | [`tools/move_paths.py`](../tools/move_paths.py) | **Deliberate.** A person-run tool (practice: rename-updates-links), named in [precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s engine file list, so every install carries it; nothing is meant to call it. |
| BestPractice | [`tools/routing_eval_synthetic.py`](../tools/routing_eval_synthetic.py) | **Deliberate.** The re-runnable scorer for `evals/routing_synthetic/`, whose [PREDICTION.md](../evals/routing_synthetic/PREDICTION.md) cites it. The audit is not clean (that file and MAP.md name it), which is correct for a live research harness. |
| BestPractice | [`tools/reach_key.py`](../tools/reach_key.py) | **Live now.** Imported by [doc_sync.py](../tools/doc_sync.py) and [fact_ledger.py](../tools/fact_ledger.py); the 2026-09-28 inventory had it as carried for a consumer and unused here. |
| BestPractice | `evals/routing`, `evals/routing_synthetic`, `evals/simulation` | **Live.** Each read by a tool in `tools/`. |
| the individual set | `bootstrap/session-start.sh` | **Live, ask.** Wired by nothing in that set's own settings and not declared as an adapter, but its `claude-web-bootstrap` check and that check's tests read it, so the audit is not clean. Whether consumers are still meant to copy it is the open question in [todo-2026-09-12-source-sets-declare-adapters](../todo/todo-2026-09-12-source-sets-declare-adapters.md). |
| the individual set | `bootstrap/freshness-guard.sh`, `bootstrap/commit-identity.sh` | **Resolved.** The 2026-09-28 inventory had the guard "live but frozen". Since 2026-10-07 both are the engine's 31-line stub, which runs the current `tools/` copy, so nothing is left to freeze. |
| the individual set | `page.md` | **Gone.** The accidental two-line file the 2026-09-28 inventory asked about is no longer in the tree. |
| a retired shared set | the whole repository | **Ask.** Retired 2026-10-06 and listed in [tools/deleted_sets.json](../tools/deleted_sets.json) as "being deleted", but on 2026-10-17 its repository still answers `git ls-remote`, with pull-request refs that its own open item says still reach a file naming private repositories. Deleting it is the person's call. |
