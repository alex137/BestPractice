---
slug:            gotcha-2026-10-05-a-ci-run-that-never-got-a-runner-reads-as-ci-failed
status:          live
noted:           2026-10-05
severity:        notable
retired:         null
retires_when:    "tools/precedent_ci_verified.py tells a run that never started from one that ran and failed"
---
## Symptom

The merge gate says **"CI FAILED on the commit you are about to merge"**,
naming "Leak gate", and the job has no log at all: GitHub answers 404 for
it. The job sat queued for about fifteen minutes and then ended
`cancelled`, with `runner_id: 0` and no runner name. A re-run does the same
thing. The workflow RUN still reports its conclusion as `failure`, which is
all [tools/precedent_ci_verified.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_ci_verified.py)
reads, so the gate cannot tell this from a check that ran and found
something.

## Story

**2026-10-05, booking the practice-standing work (PR #893).** The branch's
leak-gate run queued, waited fifteen minutes and was cancelled; the one
allowed re-run did the same. Runs for other sessions' feature branches were
stuck the same way at the same time, while pushes to `pre-staging` and
`main` were still getting runners -- until, a few minutes later, the run
for the merge commit on `pre-staging` stalled too. Nothing in the diff was
involved: `python3 tools/leak_gate.py --range origin/pre-staging..HEAD`,
which runs the private blocklists on top of the structural half CI runs,
passed locally. The session spent about three quarters of an hour finding
that out.

## Fix

Before treating a red leak gate as a finding, open the job, not the run:
`runner_id: 0`, no runner name and a log that will not download mean it
never started. Then list the workflow's recent runs: if other branches are
queued or cancelled the same way, GitHub has no runners for the repository
right now and the change is not the cause. Run the same check locally --
the leak gate locally is a superset of the CI half -- and decide on that;
the merge gate's CI line is advisory for exactly this reason. One re-run is
the most it is worth. The upstream fix is for that tool to
read the job, not just the run, and say "never started" instead of
"FAILED"; it costs a second API request against an unauthenticated budget,
which is why it is not done yet.
