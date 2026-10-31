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

The fix went into `main` and the next test failed the same way from a
different angle: an open item linked the ladder note tool by a relative path under tools/ladder/,
a file the ladder set installs into this checkout but that the repository
does not track, so the light check's link test found it locally and not on
the runner.

## Fix

In engine code, never write `practice: SLUG` for a practice that lives in a
set: name it in words ("the ladder set's stale-branch-cleanup"), as the
rest of the engine does. Link a file a set installs (anything under
`tools/ladder/`, which this repository does not track) by its GitHub
address in the set, never by a relative path. To check before pushing, run
`python3 tools/precedent_check.py` in a fresh clone of the branch, with the
set's clone moved aside, then move it back.

Prevention: `code-cites-practice` catches it, in the full tier: the Debut, and GitHub's test after a Produce. Measured 2026-10-30, it reads only this repository's own `practices/` and `local/practices/`, as it did on 2026-10-27, and it fails a planted `practice: stale-branch-cleanup` with the ladder set cloned beside. So the set on disk is not what let it through; the quick checks before a push never run [tools/precedent_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py) at all (the quick tier is closed to it), and a Produce taken without a Debut on the same pair reaches GitHub's test first. No planted case holds the set-on-disk direction yet. The second half, a relative link to an untracked file a set installs under `tools/ladder/`, is still found locally and missed only on the runner: nothing catches it before GitHub does. (2026-10-30 very deep check, Pass 2 question 20.)
