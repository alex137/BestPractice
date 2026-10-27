---
slug:            gotcha-2026-10-27-a-citation-of-a-set-practice-passes-locally-and-fails-on-github
status:          live
noted:           2026-10-27
severity:        notable
retired:         null
retires_when:    "code-cites-practice judges a slug it cannot find as could-not-verify when a declared or brought set is absent, instead of as a violation"
---
## Symptom

GitHub's test on `main` fails with `VIOLATION code-cites-practice ...
cites 'SLUG', which is not a real practice slug`, right after a Produce
whose local checks all passed. The slug is real: it belongs to a practice
set, such as the ladder set.

## Story

2026-10-27. A session moving the branch cleanup page into its own database
wrote `(practice: stale-branch-cleanup; ...)` in a docstring of
[`tools/precedent_stale_branches.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_stale_branches.py). That practice lives in the ladder set.
The session's container had the set cloned beside BestPractice, so the
push check and the land tool's quick checks found the slug and passed.
GitHub's runner has no practice set on disk, so the same check found no
such practice and failed `main` after the merge. Moving the set aside and
running `python3 tools/precedent_check.py --only code-cites-practice`
reproduced it at once.

## Fix

In engine code, never write `practice: SLUG` for a practice that lives in a
set: name it in words ("the ladder set's stale-branch-cleanup"), as the
rest of the engine does. To check before pushing, move the set's clone
aside and run `python3 tools/precedent_check.py --only
code-cites-practice`, then move it back.
