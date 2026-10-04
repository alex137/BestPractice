---
slug:            gotcha-2026-10-02-a-config-named-for-a-test-reset-the-real-individual-clone
status:          live
noted:           2026-10-02
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

In a hosted session, the individual set's clone keeps moving back onto
`main` while you work on a branch of it. Nothing you ran checked it out.
Checks that read the individual set from its working tree (the leak gate's
allow lines, say) then read `main` and refuse what the branch allows.

## Story

On 2026-10-02 a session building a change across BestPractice and the
individual set put the individual clone on its feature branch several
times, and each time it was back on `main` minutes later. The reflog
showed plain checkouts, at moments when the session was running the
harness, or commands for a pretend person with no individual set.

The cause was the resolver's individual-source self-heal. When the user
config it reads does not exist, on a hosted session, it runs the project's
individual-source bootstrap hook, to recover from a hook that ran before
this session's repository access existed. A test fixture or a pretend
person says "nobody works here" by pointing `PRECEDENT_USER_CONFIG` at a
file that does not exist. The self-heal read that as the too-early case and
ran the hook, and the hook works in `$HOME`: it found the real clone,
which it had made, and moved it to its pinned branch, as session start
does. Every fixture that named a config of its own did this.

## Fix

The self-heal does not run the hook when `PRECEDENT_USER_CONFIG` names a
file outside `$HOME`, since that config is somebody other than the person
whose home the hook works in; an absent config named there is a definite
"no individual set". A fixture that moves `$HOME` along with its config is
still healed, in its own home
(`precedent_resolve._self_heal_individual_source`). Until that reaches
you: commit or push your work on the individual clone before running the
harness, and check `git -C ~/precedent-individual branch --show-current`
before anything that reads it.
