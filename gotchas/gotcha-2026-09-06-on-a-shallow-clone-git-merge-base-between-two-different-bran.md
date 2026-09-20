---
slug:            gotcha-2026-09-06-on-a-shallow-clone-git-merge-base-between-two-different-bran
status:          retired
noted:           2026-09-06
severity:        null
retired:         "2026-09-06"
retires_when:    null
---
## Symptom

On a shallow clone, `git merge-base` between two *different* branches

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **On a shallow clone, `git merge-base` between two *different* branches
  can exit 1 ("no common ancestor") even when the branches genuinely share
  history — and that false negative reads exactly like a destructive
  force-push.** On 2026-09-06, comparing `precedent-beta-v01` against an
  older feature branch this way returned exit 1, which looked like proof
  the two had disjoint, independently-rewritten histories; the session
  nearly asked the user to confirm a branch rewrite that had never
  happened. `git merge-base <A> origin/main` and `git merge-base <B>
  origin/main` each resolved fine in the meantime — the shallow fetch
  simply didn't reach far enough back to contain the real common ancestor
  of `<A>` and `<B>` themselves, even though each one individually had a
  shorter path back to `main`. `git merge-base` exiting 1 is not by itself
  evidence of a rewritten or discarded branch: `git fetch --unshallow
  origin` (or a deep enough bounded `git fetch --depth=<N> origin
  <branch>`, per the entries above) and recheck before concluding
  anything about two branches' relationship.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
