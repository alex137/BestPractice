---
slug:            gotcha-2026-10-19-an-advisory-reply-requirement-is-never-shown-to-anyone
status:          live
noted:           2026-10-19
severity:        notable
retired:         null
retires_when:    "a session opened above its repositories runs the turn-start reply gate too, so the notice below reaches every session"
---
## Symptom

A reply breaks a rule the reply check carries, nobody is told, and the
person has to notice it and ask. The requirement is right there in
`reply_check.json`, with a pattern that matches the reply, and `--explain`
lists it. It is declared `"advisory": true`.

## Story

2026-10-19. A session's Boildown named a dated session branch and a file in
code font with no link. Morgan asked why, given that `rule-links` says every
file and branch gets a link on first use. The reply check had carried a
`rule-links` requirement since 2026-09-20, advisory because a name linked
once and named bare again later still matched. `main()` keeps only the
non-advisory findings and returns 0 on the rest, and a Stop hook that exits
0 shows nothing to the session. So the requirement had never reached
anyone, in any repository.

The same session found a second gap on the way: it was opened in
`/home/user`, above every repository, and the user-level settings the cloud
setup script writes carried the merge and push gates but no Stop entry. The
reply check did not run at all, blocking requirements included.

## Fix

The `rule-links` requirements are blocking now, with dated branches and file
paths in code font added. The imprecision that had justified advisory is
fixed: a name linked anywhere in the reply covers its later bare mentions.
[documentation/CLOUD_SETUP.md](../documentation/CLOUD_SETUP.md)'s setup
script writes a Stop entry that runs
[tools/precedent_global_gate.sh](../tools/precedent_global_gate.sh)
`stop-reply-check.sh`; an environment picks it up when its setup script is
updated and a new session starts.

The two requirements that stay advisory on Morgan's word (the archive line
and the compaction offer) are now named at the next turn's start, by
[tools/precedent_gate.py](../tools/precedent_gate.py)'s reply gate: "Your last
reply left these out". Nothing is refused. **That notice needs the turn-start
reply gate to run**, and a session opened above its repositories does not run
it yet; until it does, an advisory miss in such a session is still unseen.
