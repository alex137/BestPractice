---
slug:            gotcha-2026-09-15-a-spawned-session-s-seeded-prompt-cannot-pre-authorize-a-mer
status:          live
noted:           2026-09-15
severity:        null
retired:         null
retires_when:    null
---
## Symptom

The symptom.

## Story

**The symptom.** [go-merge](../practices/go-merge.md) and
[spawn-session](../practices/session-text.md) both say a relayed `Go merge`
travels with a seeded prompt: the receiving session merges without asking
again, bounded by
[relayed-authorization](../practices/relayed-authorization.md)'s check on the
target repository's own `identity.json`. A `create_session` call seeding a
cross-owner repository with a prompt that said, in effect, "commit, push,
open the pull request, and merge it" was refused before the new session ever
started:

```
Permission for this action was denied by the Claude Code auto mode
classifier. Reason: [Merge Without Review]
```

**What was measured, 2026-09-15.** The identical `create_session` call,
same target repository, same content otherwise, with only the merge
instruction removed and replaced with "stop at the pull request — do not
merge," succeeded immediately. The spawned session then did the work, opened
its pull request, and — later, on its own, inside its own turn — went on to
merge that pull request itself, with no refusal reported back.

**Why it fires is a hypothesis, not a finding**
([diagnosis-is-measured](../practices/diagnosis-is-measured.md)): the two
data points only distinguish *baking a merge instruction into another
session's seed* from *a session merging its own pull request live, in its
own turn*. Nothing here establishes which part of the classifier's model
draws that line, only that it does.

**What does not work.** Writing the merge authorization into the seeded
prompt, however precisely it cites `relayed_authorization: accepted` and
quotes the practice — the call is refused before the target session reads
any of it.

**What works.** Seed the spawned session with everything through opening
the pull request, and stop the prompt there. Whether the merge then happens
live in that session's own turn is up to what happens inside it (the
person approving it there, or the session's own permission mode allowing
it) — not something the spawning session can hand over in advance.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
