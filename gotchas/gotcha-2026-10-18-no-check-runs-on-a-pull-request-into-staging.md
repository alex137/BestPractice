---
slug:            gotcha-2026-10-18-no-check-runs-on-a-pull-request-into-staging
status:          retired
noted:           2026-10-18
severity:        notable
retired:         2026-10-31
retires_when:    "a workflow here runs on pull requests into staging, or the landing guard's own refusal says when no check is coming"
---
## Symptom

A landing on `staging` is refused with "This one takes a pull request ... merge it
once its checks pass". The pull request into `staging` shows no checks at
all, and the session sits waiting for a CI event that never arrives.

## Story

**2026-10-18.** A landing changed [`tools/precedent_check.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py) and
[`tools/verify_harness.py`](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py), so the ladder set's landing guard sent it through
a pull request. The session opened #1203 into `staging`, subscribed to its
activity, set a check-in for 50 minutes later, and stopped. In
[deep-check.yml](https://github.com/alex137/BestPractice/blob/staging/.github/workflows/deep-check.yml), `pull_request` runs
only for `branches: [main]`, so no check ever started and no event came.
Morgan asked whether anything was running in the background. Nothing was:
the session was waiting on a check that did not exist.

## Fix

[`precedent_branches.py --land`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_branches.py) now follows
a refusal that names the pull-request route with a line read from the
workflows themselves (`pull_request_route_note`). With no workflow on pull
requests into that branch, it says to open the pull request and merge it
straight away, since the quick checks that landing ran already passed. By
hand: open the pull request, look at its checks once, and if none is listed,
none is coming. Never wait on a check nothing has started. The refusal's
own wording lives in the ladder set's [`landing_pr_guard.py`](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/landing_pr_guard.py); changing it there is
[todo-2026-10-18-landing-guard-refusal-promises-checks](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-10-18-landing-guard-refusal-promises-checks.md).

**2026-10-18, later: not retired yet.** That item closed: the guard's
refusal now ends with `pull_request_route_note` on the ladder set's
`staging`
([themorgan/precedent-shared-ladder#106](https://github.com/themorgan/precedent-shared-ladder/pull/106)).
But the copy a session here runs, the untracked copy of the guard
the session start writes, still carries the old sentence, because it comes
from the ladder set's `main`. This retires once that copy says when no
check is coming, or a workflow here runs on pull requests into `staging`.

**Retired 2026-10-31, on its stated condition** (very deep check of
2026-10-30, pass 4). The copy a session runs comes from the ladder set's
`main`, and that `main` now carries the guard whose refusal ends with the
engine's `pull_request_route_note`, or, where the engine cannot be
imported, says to merge at once when the pull request lists no checks
(`route_note` in
[landing_pr_guard.py](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/landing_pr_guard.py)).
`check_land_refusal_says_whether_a_pull_request_gets_checks` in
[tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py)
pins the note.
