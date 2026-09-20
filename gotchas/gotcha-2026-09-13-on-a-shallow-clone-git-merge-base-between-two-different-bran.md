---
slug:            gotcha-2026-09-13-on-a-shallow-clone-git-merge-base-between-two-different-bran
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

On a shallow clone, `git merge-base` between two *different* branches can exit 1 ("no common ancestor") even when the branches genuinely share history — and that false negative reads exactly like a destructive force-push.

## Story

**On a shallow clone, `git merge-base` between two *different* branches can
exit 1 ("no common ancestor") even when the branches genuinely share history —
and that false negative reads exactly like a destructive force-push.** On
2026-09-06 a session nearly asked the user to confirm a branch rewrite that
had never happened. `git merge-base <A> origin/main` and `git merge-base <B>
origin/main` each resolved fine meanwhile: the shallow fetch simply didn't
reach the real common ancestor of `<A>` and `<B>`. Exit 1 is not evidence of a
rewritten branch — fetch deeper and recheck before concluding anything about
two branches' relationship.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
