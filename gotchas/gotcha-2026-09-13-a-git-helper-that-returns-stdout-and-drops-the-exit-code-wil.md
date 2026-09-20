---
slug:            gotcha-2026-09-13-a-git-helper-that-returns-stdout-and-drops-the-exit-code-wil
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A git helper that returns stdout and drops the exit code will hand you a confident wrong answer — this is the most-repeated bug in the project.

## Story

**A git helper that returns stdout and drops the exit code will hand you a
confident wrong answer — this is the most-repeated bug in the project.** Two
shapes, both live: `git rev-parse <missing-ref>` exits non-zero but *prints
the ref you asked for*, so `_git(...'rev-parse', ref) or <fallback>` never
falls back — it carries the string `origin/precedent-beta-v01` forward as a
hash, which reached continuous integration once as a 12-char truncation of a
ref name. And `git show <commit>:<path>` exits 128 with **empty stdout** for
two unrelated situations — the commit is not in this clone, or the path did
not exist at that commit — so a caller reading stdout alone answers an
unanswerable question. That one reported 69 lines of a vendored tree as LOST
on 2026-09-08, disprovable only by extracting both trees and diffing them by
hand. **Use `rev-parse --verify --quiet`, and consult the return code whenever
a command can fail for two different reasons.** Found in five separate tools
so far; the inventory is in the archive. Note the trigger for the first shape:
a *non-repo* prints nothing, so the plain form looks correct for years — it
only echoes on an unborn `HEAD` or a missing ref.

**A third shape, and it defeats the fix this entry recommends:
`rev-parse --verify --quiet` exits 0 and echoes back ANY well-formed 40-hex
string, present in the clone or not.** `--verify` checks that the argument
names a single revision — a full hash always does — never that the object
exists. Found 2026-09-08 by a negative-control fixture for
[tools/precedent_upstream_check.py](../tools/precedent_upstream_check.py): a
watermark pointing at 40 zeroes read as *present*, so the guard meant to say
"that commit is not in this shallow clone" never fired and the notice
announced a change it could not list. Ask the object database instead —
`git cat-file -e <sha>^{commit}`. `--verify` remains right for a *name*
(`origin/main`, `HEAD`), which is what the two shapes above are about.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
