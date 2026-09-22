---
slug:            gotcha-2026-09-22-a-pr-s-check-runs-read-in-progress-long-after-the-jobs-fin
status:          live
noted:           2026-09-22
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A pull request's check runs read `in_progress` for tens of minutes after the
jobs actually finished

## Story

**The symptom.** You open a pull request, wait for the Deep check, and poll
it the obvious way — the GitHub Model Context Protocol server's
`pull_request_read` with `method: "get_check_runs"`. Two of the four rows
keep coming back `"status": "in_progress"`, with a `started_at` and no
`completed_at`, poll after poll. Forty minutes of it, on a workflow whose own
history says it takes under two.

Nothing about the response looks stale. The other two rows are `completed`
with a conclusion, so the call is clearly reaching GitHub and clearly
returning live data — it is just returning **the wrong live data** for the
rows you care about.

**What was actually true.** The jobs had completed at 13:54:50 and 13:55:57,
about ninety seconds after they started, exactly in line with every other run
of that workflow. `actions_list` with `method: "list_workflow_jobs"` on the
run id said so plainly while `get_check_runs` was still reporting
`in_progress` on the same two jobs. Somewhere between the check-runs view and
the jobs view, one of them is cached far longer than the other, and the
check-runs view is the one that lies.

**What it costs.** The whole point of polling is to know when to merge, so a
row that is wrong in the "still working" direction stalls the merge
indefinitely and burns real wall-clock — here, forty minutes of waiting on
something that had been finished for thirty-eight of them. It also invites
the wrong diagnosis: a job "stuck at step 5" for forty minutes on a
markdown-only diff reads as a hang in CI, and the obvious next moves —
cancel, re-run, go hunting for what in the diff could possibly hang a
harness — are all wasted.

## Fix

**Confirm a slow-looking job against `actions_list` before believing it.**
Take the run id from the check run's `html_url`
(`/actions/runs/<run_id>/job/<job_id>`) and call `actions_list` with
`method: "list_workflow_jobs"` and that run id. It returns each job's real
`status`, `conclusion` and `completed_at`, plus the per-step breakdown.

The rule of thumb that catches it: **a job running far longer than its own
history says it should is a stale read until proven otherwise.** Pull the
workflow's recent runs (`method: "list_workflow_runs"`) and compare
durations. A job whose siblings all finish in ninety seconds does not
suddenly take forty minutes on a documentation change.

Job logs are a second tell, though a weaker one:
`get_job_logs` on a genuinely in-progress job returns HTTP 404, and so does
one on a job the API is merely *reporting* as in progress — so a 404 does not
distinguish them. The jobs view does.
