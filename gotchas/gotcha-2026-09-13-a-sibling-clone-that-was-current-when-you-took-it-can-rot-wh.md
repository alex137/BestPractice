---
slug:            gotcha-2026-09-13-a-sibling-clone-that-was-current-when-you-took-it-can-rot-wh
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A sibling clone that was current when you took it can rot while you work, and a "these copies do not match" failure will blame the code rather than your clone.

## Story

**A sibling clone that was current when you took it can rot while you work,
and a "these copies do not match" failure will blame the code rather than your
clone.** 2026-09-07: `verify_harness.py` reported three copies of
`commit-identity.sh` disagreeing. The check was correct that they differed and
wrong about what that meant — the attached clone was 2 commits behind, and one
`git -C <clone> pull --ff-only` made all three agree with no change to any
file here. **The direction of the mistake is what makes this worth a rule**:
the failure reads as "this repo's file is wrong", and the obvious remedy —
copy the clone's older version over the newer one — silently reverts
somebody's just-landed work. Confirm which side is stale first: `git -C
<clone> fetch && git -C <clone> rev-list --count HEAD..origin/<branch>`. Same
reasoning for a check younger than your branch: rule out "never been green
here" by running it against the untouched tip before fixing it.

**Second instance, 2026-09-11, where the stale clone was the LEAK GATE's
blocklist** — and it put a wrong finding in a pull request. The gate
reported 30 undeclared-repo hits; a session read them as a real defect,
wrote "red on the base branch too" into its gate block, and filed a TODO
item for a fix already merged. Its clone of the private set predated a
repository rename by hours, so it lacked the allowlist line those 30
references needed. **A correct gate, correct output, stale input —
indistinguishable from a real failure by construction.** The gate says so
itself now: on failure it names the blocklist's clone and how far behind
it is. It never claims a clone is current (an unfetched remote-tracking
ref cannot prove that) and never fetches, since a gate that reaches the
network to grade itself can hang on a push. **When a gate whose input
lives in another repository fails, ask how old the input is before
believing the finding.**

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
