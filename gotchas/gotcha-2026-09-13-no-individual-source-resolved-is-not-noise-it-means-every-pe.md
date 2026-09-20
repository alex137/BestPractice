---
slug:            gotcha-2026-09-13-no-individual-source-resolved-is-not-noise-it-means-every-pe
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

"no individual source resolved" is not noise — it means every personal and team practice is silently absent, and the session will confidently apply the wrong rules.

## Story

**"no individual source resolved" is not noise — it means every personal and
team practice is silently absent, and the session will confidently apply the
wrong rules.** 2026-09-07: a session ran most of a working day here with none
of the account owner's personal practices loaded. `tools/precedent_resolve.py`
printed the reason on *every single run*, and the session read past it every
time as startup chatter — because the checks it prefixes all reported `0
violated`, and the line sits directly above the summary a session is reading
the output *for*. The cost is invisible while it happens: the practices that
did not load included `audience-register`, the owner's standing rule about how
replies are written, so **every reply that session was pitched by guesswork
while a rule saying exactly what to do sat unread**. The session's own
diagnosis each time was "I keep forgetting" — a misdiagnosis, since the rule
was never in front of it. **Stop and fix it before doing anything
rule-dependent:** `add_repo` for the private sources, then re-run `python3
tools/precedent_resolve.py --repo .` and confirm the count names `individual`
and `team`, not universal alone.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
