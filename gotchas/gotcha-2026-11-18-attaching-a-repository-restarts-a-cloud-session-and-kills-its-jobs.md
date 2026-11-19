---
slug:            gotcha-2026-11-18-attaching-a-repository-restarts-a-cloud-session-and-kills-its-jobs
status:          live
noted:           2026-11-18
severity:        notable
retired:         null
retires_when:    the cloud harness attaches a repository without restarting the session's container
---
## Symptom

A long job running in the background of a cloud session dies with no
error, and `uptime` shows the machine has been up for a minute. The
conversation carries a notice that instruction files "were re-read when
this session started". Nothing in the job's log explains it.

## Story

2026-11-18, in a dependent repo, several times in two days. Each restart
followed an `add_repo` call: attaching a repository to a running cloud
session restarts its container. Background processes started before the
attach are gone afterward, and anything they held only in memory is gone
with them. Files on disk survive.

It took until the fifth restart to connect the two, because the attach
and the death of the job were minutes apart in the conversation and the
job's own log said nothing. One of those restarts killed a run two thirds
of the way through; it resumed only because it had begun saving its
progress after each unit an hour earlier.

## Fix

Attach every repository a session will need at its start, before any long
job is running. If one has to be attached later, first make sure each
running job saves its progress and can resume
([slow-steps-report-and-cache](../practices/slow-steps-report-and-cache.md)),
then attach, then restart the jobs.
