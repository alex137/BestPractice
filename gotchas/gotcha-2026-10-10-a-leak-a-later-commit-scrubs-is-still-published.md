---
slug:            gotcha-2026-10-10-a-leak-a-later-commit-scrubs-is-still-published
status:          live
noted:           2026-10-10
severity:        notable
retired:         null
retires_when:    "never: the fix is a check that keeps it from recurring, and the published commit stays published"
---
## Symptom

The leak gate refuses a landing over a private repository's name in a
file. You scrub the name in a new commit, the landing passes, and the
branch you landed on is clean. The first commit, the one with the name in
it, is still in the public branch's history: `git log -S'<name>'` finds
it, and anyone can read it on GitHub.

## Story

2026-10-10, BestPractice. A harness test written that afternoon gave its
fixture the name of a private practice pack. The landing's quick checks
ran the leak gate on the tree, saw five hits, and refused. A second commit
renamed the fixture, the tree came up clean, and the landing passed and
pushed `staging` with both commits. Every level of
[tools/precedent_push_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_push_check.py) ran
[leak_gate.py](https://github.com/alex137/BestPractice/blob/staging/tools/leak_gate.py) bare, which reads the files as they end up. It never used
the gate's own `--range` mode, which walks each commit and its message
and existed for exactly this case. Rewriting `staging` would undo the
publication only for people who had not fetched it yet, and staging and
main are never force-pushed, so the commit stays.

## Fix

The push check now also runs `leak_gate.py --range "HEAD --not --remotes"`
(`leak_gate_commits`) at every level: each commit the push would publish,
messages included, that no remote has yet. A leak a later commit scrubs
now refuses the push. Fix it by rewriting your own unpushed commits
(amend or rebase them on your working branch) before the push, never by
adding a scrub on top.
