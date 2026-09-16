---
slug:            gotcha-2026-09-13-a-background-sleep-is-not-a-wait-and-using-one-as-a-wait-mak
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A background `sleep` is not a wait, and using one as a wait makes you invent elapsed time.

## Story

**A background `sleep` is not a wait, and using one as a wait makes you invent
elapsed time.** 2026-09-11: a session polling a continuous integration job ran
`sleep` four times as a BACKGROUND task, then queried the API immediately each
time — a background task returns a task id at once and pauses nothing. It
believed roughly thirteen minutes had passed. Real elapsed time between its
polls was near zero, so every poll returned the same `in_progress`, which it
read as a hung job. **The second half is the expensive one.** It then reported
the job as hanging "after 18 minutes" — a figure it got by comparing the job's
`started_at` against a present moment it had never measured. It had not run
`date` once. The job had in fact finished in 5 seconds, failing normally on a
pre-existing violation, 26 seconds BEFORE the session merged over it; the last
poll it acted on returned stale data. The invented figure went into a merge
commit on `precedent-beta-v01`, where it cannot be corrected in place —
published history — so the correction lives as a comment on the pull request
instead. **Read the clock before claiming any duration.** `date -u` costs
nothing, and a timestamp compared against an imagined now is not a measurement
— it is [no-invented-specifics](../practices/no-invented-specifics.md) failing in
the one place the invention looks like arithmetic. Note also that the harness
DOES notify when a background task completes; those notifications arrived,
just after the merge. The mechanism was there and went unused. **The symptom
impersonates a real failure**, which is why this is worth a gotcha rather than
a shrug: a stale `in_progress` and a genuinely hung job render identically,
and "it's been N minutes" is exactly the sentence that makes a session stop
waiting.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
