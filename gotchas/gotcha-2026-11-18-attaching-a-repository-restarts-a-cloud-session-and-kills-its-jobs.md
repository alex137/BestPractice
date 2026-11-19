---
slug:            gotcha-2026-11-18-attaching-a-repository-restarts-a-cloud-session-and-kills-its-jobs
status:          live
noted:           2026-11-18
severity:        notable
retired:         null
retires_when:    a cloud session's container is shown not to restart under a running job, or the harness says when it does
---
## Symptom

A long job running in the background of a cloud session dies with no
error, and `uptime` shows the machine has been up for a minute. The
conversation carries a notice that instruction files "were re-read when
this session started". Nothing in the job's log explains it.

## Story

2026-11-18, in a dependent repo, several times in two days: a cloud
session's container restarted under a running job. Background processes
started before the restart were gone afterward, and anything they held
only in memory was gone with them. Files on disk survived. One restart
killed a run two thirds of the way through; it resumed only because it
had begun saving its progress after each unit an hour earlier.

**What was observed, and what was inferred.** Observed: the restarts, and
that several of them came minutes after an `add_repo` call. Inferred from
that timing, and never tested: that attaching a repository is what
restarts the container. Two later observations say it is not the whole
cause. The same session reported restarts that followed plain idleness,
with no attach near them. And on 2026-11-19 another cloud session
attached two repositories a few minutes after it started and its machine
did not restart (`uptime` still counted from the session's start). So an
attach is one thing a restart has followed, not a thing that always
causes one, and a session that attaches nothing can still lose its jobs.

## Fix

Treat a restart as something that can happen to any long job in a cloud
session, whatever the session did: each running job saves its progress as
it goes and can resume
([slow-steps-report-and-cache](../practices/slow-steps-report-and-cache.md)).
Attaching every repository a session will need at its start, before any
long job is running, costs nothing and removes the one trigger that was
seen more than once. After a job dies with no error, check `uptime`
before looking for a fault in the job.
