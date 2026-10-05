---
slug:            gotcha-2026-10-05-a-ci-run-that-never-got-a-runner-reads-as-ci-failed
status:          retired
noted:           2026-10-05
severity:        notable
retired:         2026-10-05
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
allowed re-run did the same. Listing every job in the repository from
19:30 to 20:30 UTC showed the shape: about half of all jobs, on every
workflow and every branch -- feature branches, `pre-staging`, and the deep
check on `main` after a Produce -- sat with no runner for fifteen minutes and
were cancelled, while the other half ran normally, some of them on the very
same branches. Nothing in any diff was involved:
`python3 tools/leak_gate.py --range origin/pre-staging..HEAD`, which runs
the private blocklists on top of the structural half CI runs, passed locally. The session spent about three quarters of an hour finding
that out.

## Fix

Before treating a red leak gate as a finding, open the job, not the run:
`runner_id: 0`, no runner name and a log that will not download mean it
never started. Then list the workflow's recent runs: if other branches are
queued or cancelled the same way, GitHub has no runners for the repository
right now and the change is not the cause. Run the same check locally --
the leak gate locally is a superset of the CI half -- and decide on that;
the merge gate's CI line is advisory for exactly this reason. One re-run is
the most it is worth. **Fixed the same day:** that tool now reads
the jobs of a run that did not pass -- one more API request, only then --
and the merge gate says "CI NEVER STARTED" with this advice instead of
"CI FAILED". GitHub's capacity can still stall a run; it no longer reads
as a finding.
