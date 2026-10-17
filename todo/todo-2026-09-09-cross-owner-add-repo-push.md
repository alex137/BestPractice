---
slug:              todo-2026-09-09-cross-owner-add-repo-push
kind:              verify
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        "a session rooted under the other owner (a private practice-set repository), which this repository's sessions cannot start for themselves."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-09
closed:            2026-10-17
---
## What

- <a id="cross-owner-add-repo-push"></a>**Measure whether `add_repo` refuses a cross-owner attachment in the
   REVERSE direction, with `access: "push"`.** Every measurement so far ran
   one way — from a session rooted in this repository, reaching for a
   private practice-set repository under another owner — and the refusal
   ("cross-tier adds are not supported in v1") is well established there,
   including as a session's very first tool call and, as of 2026-09-09, at
   `access: "push"` as well — so nothing about THIS direction is still worth
   re-testing. The other direction is
   still unknown, and it decides whether the two-session split is permanent
   or an artefact: if a session rooted in a private set can attach this
   repository with credentials, one session can hold every private source
   *and* push here, and the token work stops mattering.
   Two attempts on 2026-09-09 failed to answer it, both for reasons that
   are now their own gotchas: the first asked for `access: "read"`, which
   short-circuits on the anonymous git proxy for a public repository and
   never reaches the authorization check at all; the second could not run
   because the spawned session had lost the tool itself mid-run. **The exact
   call that settles it** is `add_repo` with `access: "push"` for
   `alex137/bestpractice`, made from a session rooted in a private
   practice-set repository, as that session's opening turn.
   **Blocked-on:** a session rooted under the other owner, which this
   repository's sessions cannot start for themselves — and, given the
   tool-loss above, one where a person can read the answer out of the
   transcript. It carries no disposition, so it is `wait`
   ([open-item-disposition](../practices/open-item-disposition.md)).

## How It Closes

Not open until: a session rooted under the other owner (a private practice-set repository), which this repository's sessions cannot start for themselves.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.

2026-10-17, very deep check pass 4 (ambiguous, asked of the person): the split it measures looks gone (sessions working for Morgan push to BestPractice and to his sets; this run's session holds clones from both owners), but nothing here shows one session pushing to both owners, and the exact call it names (add_repo push for alex137/bestpractice from a set-rooted session) was not made. Same question as gotcha-2026-09-22-a-cross-owner-source-clone-fetches-fine-and-cannot-be-pushed: one answer from the main session about its own pushes settles both.

## Closed

Closed 2026-10-17 by the very deep check, pass 4, on what the item was for: whether one session can hold every private source and push here. It can. A cloud session created with this repository and three private practice sets of another owner as its sources pushed working branches to both owners on 2026-10-17 (this repository and the individual set), with no token work. The narrower `add_repo` measurement was never taken and no longer decides anything. The gotcha about a cross-owner clone that is not a session source still holds and stays live.
