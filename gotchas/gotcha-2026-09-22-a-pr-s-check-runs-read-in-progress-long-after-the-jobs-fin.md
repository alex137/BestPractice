---
slug:            gotcha-2026-09-22-a-pr-s-check-runs-read-in-progress-long-after-the-jobs-fin
status:          live
noted:           2026-09-22
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A pull request's check runs read `in_progress` for jobs the workflow-jobs
view already reports as completed

## Story

**The symptom.** You poll a pull request the obvious way — the GitHub Model
Context Protocol server's `pull_request_read` with
`method: "get_check_runs"`. Two rows keep coming back
`"status": "in_progress"`, with a `started_at` and no `completed_at`. Call
`actions_list` with `method: "list_workflow_jobs"` on the same run id and
those same two jobs are `"status": "completed"`, `"conclusion": "success"`,
with completion timestamps already in the past. **Two views of one run,
disagreeing, in the same minute.**

**What is actually established.** The disagreement itself, measured
2026-09-22: `get_check_runs` reported `in_progress` for jobs
`list_workflow_jobs` reported completed at 13:54:50 and 13:55:57. The jobs
view is the one that matched the logs. That is the whole of what was
observed, and it is enough for the fix below.

**The first diagnosis written here was bigger than the evidence, and is
corrected.** The original entry said the stale view cost forty minutes of
waiting. It did not. The jobs themselves ran about ninety seconds; the forty
minutes was the session's own polling cadence — long background sleeps
spread across several conversational turns — and attributing that to GitHub
made a mechanism out of what was mostly a session waiting badly. **How long
the check-runs view lags, and whether it lags at all rather than having been
read once at an unlucky moment, is NOT established here.** One observation
of a disagreement is one observation.

**A second, tidier explanation was tested and is false**, which is the more
useful half of this entry. It looked as though the container's clock might
freeze while the session is suspended between turns, which would make every
elapsed-time judgement in a session unreliable. Measured directly — stamp
`date +%s`, run `sleep 60` in the background, stamp again on completion —
the clock advanced **64 seconds**. It does not freeze. The apparent
contradiction that suggested it came from comparing two different stretches
of the session as though they were one.

**The lesson that survives both wrong turns.** A session reading its own
sense of elapsed time is reading something it has no instrument for: work
happens in bursts separated by gaps of unknown length, and "this is taking
ages" is not a measurement. Timestamps from the service being polled are,
and they are free.

## Fix

**Confirm a slow-looking job against `actions_list` before believing it.**
Take the run id from the check run's `html_url`
(`/actions/runs/<run_id>/job/<job_id>`) and call `actions_list` with
`method: "list_workflow_jobs"` and that run id. It returns each job's real
`status`, `conclusion` and `completed_at`, plus the per-step breakdown that
says which step is actually running.

**Judge elapsed time from the service's own timestamps, never from how long
the session feels it has been waiting.** The job's `started_at` against the
workflow's recent runs (`method: "list_workflow_runs"`) answers "is this run
unusual" in one call. A job whose siblings all finish in ninety seconds and
whose own `started_at` is two minutes old has not stalled — it is running,
and the waiting is the session's.

`get_job_logs` is not a tell either way: it returns HTTP 404 for a job that
is genuinely in progress **and** for one the check-runs view is merely
reporting as in progress. The jobs view distinguishes them; the logs do not.
