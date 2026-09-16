---
slug:            gotcha-2026-09-07-no-individual-source-resolved-is-not-noise-it-means-every-pe
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

"no individual source resolved" is not noise — it means every personal

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **"no individual source resolved" is not noise — it means every personal
  and team practice is silently absent, and the session will confidently
  apply the wrong rules.** 2026-09-07: a session ran most of a long working
  day in this repository with none of the account owner's personal
  practices loaded.
  `tools/precedent_resolve.py` printed the reason on *every single run* —
  *"no individual source resolved … which usually means its clone could
  not be fetched (a private repository this session was never granted)"* —
  and the session read past it every time as startup chatter, because the
  checks it prefixes all reported `0 violated` and the line sits directly
  above the summary a session is reading the output *for*. (The counts in
  an earlier draft of this entry -- "twenty turns", "fifteen times" --
  were impressions written as figures and neither was counted; the
  frequency is *every run*, which is the part that matters and the part
  that is checkable.)
  The cost is invisible while it is happening, which is what makes it
  worth an entry: the practices that did not load included
  `audience-register`, the owner's standing rule about how replies to him
  are written, so every reply that session was pitched by guesswork while
  a rule saying exactly what to do sat unread in a repository nobody had
  fetched. He had asked for that register repeatedly across days, and the
  session's own diagnosis each time was "I keep forgetting" — a
  misdiagnosis, since the rule was never in front of it.
  **When you see that line, stop and fix it before doing anything that
  depends on the rules:** call `add_repo` for the private sources (the
  banner at the top of this file), then re-run
  `python3 tools/precedent_resolve.py --repo .` and confirm the count says
  `individual` and `team` rather than universal alone. A single-digit
  source count where you expected four is the same signal in a different
  shape.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
