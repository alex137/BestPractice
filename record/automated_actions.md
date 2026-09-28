---
title:         Automated actions and schedules
kind:          record
status:        closed
opened:        2026-09-28
closed:        2026-09-28
superseded_by: null
supersedes:    []
audience:      session
summary:       "Every automated action and schedule across the repos in force and the account's session Routines, and every path pass 4 looked at for deprecation, each with its verdict -- from the very deep check of 2026-09-28."
---

# Automated actions and schedules

Inventory from the very deep check of 2026-09-28, pass 4
([very-deep-check](../practices/very-deep-check.md)): every automated action
and schedule across the five repos in force and the account's session
Routines, with a verdict each, and every path the pass looked at for
deprecation. **Nothing here fires on a clock today.** The next run reads this
file first and re-examines only what changed.

## Workflows

| Repo | Workflow | Triggers | Schedule | Runs, last 14 days | Verdict |
|---|---|---|---|---|---|
| BestPractice | `.github/workflows/deep-check.yml` | `pull_request` into `main`, `push` to `main` | none | 947 runs x 4 jobs | **Needed** -- the one GitHub test on the way into `main` ([spec/BRANCH_TIERS_PLAN.md](../spec/BRANCH_TIERS_PLAN.md)). Its job count is a cost question for [spec/CI_MINUTES_PLAN.md](../spec/CI_MINUTES_PLAN.md), not a schedule question. |
| BestPractice | `.github/workflows/leak-gate.yml` | `push` (every branch), `workflow_dispatch` | none | 1400 runs x 1 job | **Needed** -- the server-side leak gate a `--no-verify` push cannot skip. |
| the individual set | `.github/workflows/engine-refresh.yml` | `workflow_dispatch` only | none (its weekly cron was removed 2026-09-14) | 1 | **Needed, with a question filed** -- an on-request refresh, cited by `practice-set-engine-refresh`; pass 2 asks whether to delete it or pin its base to the landing branch ([pass 2 findings](../todo/todo-2026-09-28-very-deep-check-pass-2-findings.md)). |
| the three shared sets | none | -- | -- | -- | Nothing to judge (`source-sets-run-no-ci`). |

## Session Routines (this account)

51 Routines on record; **none is enabled and none has a cron expression.**

| State | Count | Verdict |
|---|---|---|
| One-shot, already fired (`run_once_fired`), created 2026-09-05 to 2026-09-26 | 40 | **Delete** -- cannot fire again; kept only as history nobody reads. |
| Auto-disabled, environment deleted (`auto_disabled_env_deleted`), all 2026-09-14/15 relay and follow-up messages | 9 | **Delete** -- never fired; each carries an instruction nobody has re-read. |
| Auto-disabled, session gone (`auto_disabled_session_gone`) | 2 | **Delete** -- same reason. |

The weekly very-deep-check Routine proposed 2026-09-17
([todo-2026-09-17-weekly-very-deep-check-trigger-decision](../todo/todo-2026-09-17-weekly-very-deep-check-trigger-decision.md))
was never created.

## Operating-system cron

The container image ships `/etc/cron.d/e2scrub_all` and `/etc/cron.d/php`,
but no cron daemon runs (`pgrep cron` finds nothing) and the container does
not persist. **Not in force**; no verdict owed.

## Paths looked at for deprecation

| Repo | Path | Verdict |
|---|---|---|
| BestPractice | [`tools/reach_key.py`](../tools/reach_key.py) | **Deliberate** -- nothing here imports it; carried upstream 2026-09-27 (`f80024e0`) from a consumer so Update Vendors keeps it. |
| BestPractice | [`tools/precedent_beta_watermark_check.py`](../tools/precedent_beta_watermark_check.py) | **Live** -- run by `.claude/hooks/session-start.sh` and the reply gate. See the pass 4 finding about its `--depth=50` fetch. |
| BestPractice | `evals/routing`, `evals/routing_synthetic`, `evals/simulation` | **Live** -- each read by a tool in `tools/`. |
| the individual set | `page.md` | **Ask** -- a two-line file (`# Page` / `Decided (Morgan, 2026-09-08).`) committed by accident with a test-fixture change. `precedent_decommission.py page.md` is not clean, but all five blockers are left-side substring hits (`docs-page.md`, `a-page.md`) that the tool documents as deliberate false positives. |
| precedent-shared-repo-maintenance | `bootstrap/freshness-guard.sh`, `bootstrap/freshness.snippet.json` | **Deliberate, pending** -- `fresh-before-write` moved to universal 2026-09-28; its own Story says to decide at the deduplication step whether this copy and its check retire. |
| the individual set | `bootstrap/freshness-guard.sh` | **Live but frozen** -- wired in `.claude/settings.json`, not in `ENGINE_MANIFEST.json`'s `engine_paths`, so no refresh reaches it (729 lines against the engine's 886). Filed: [todo-2026-09-09-source-hook-drift](../todo/todo-2026-09-09-source-hook-drift.md). |
