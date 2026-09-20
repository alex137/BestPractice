---
slug:            gotcha-2026-09-07-a-sibling-clone-that-was-current-when-you-took-it-can-rot-wh
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

A sibling clone that was current when you took it can rot while you

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A sibling clone that was current when you took it can rot while you
  work, and a "these copies do not match" failure will blame the code
  rather than your clone.** The entry above is about a clone that is
  behind when a session *starts*; this is the same trap arriving later,
  and it is the shape that will keep recurring now that several sessions
  routinely work these repositories at the same time. 2026-09-07:
  `verify_harness.py` came back `1 failed` on
  *"every reachable copy of commit-identity.sh is byte-identical (3 copies
  found)"*, listing this repo's two copies in agreement and the copy in
  the attached `precedent-team-repo-maintenance` clone differing. The check was
  correct that the files differed and wrong about what that meant: the
  clone had been taken hours earlier, another session had pushed to that
  repository twice since, and it was **2 commits behind**. A single
  `git -C <clone> pull --ff-only` made all three hashes agree, and the
  re-run was `0 failed` with no change to any file here.
  **So before believing any cross-copy mismatch: refresh every attached
  sibling clone and run it again.** The reason this is worth a rule rather
  than a shrug is the direction the mistake runs — the failure reads as
  "this repo's file is wrong", and the obvious remedy is to copy the
  clone's older version over the newer one, which silently reverts
  somebody else's just-landed work. Confirm which side is stale before
  editing either: `git -C <clone> fetch && git -C <clone> rev-list --count
  HEAD..origin/<branch>` answers it in one line.
  The same reasoning applies to the check itself when it is the new thing:
  this one had landed minutes before it fired, so "a check that has never
  been green here" was also on the table, and ruling that out meant
  running it against the untouched branch tip first. A failure in a check
  younger than your branch is worth locating before it is worth fixing.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
