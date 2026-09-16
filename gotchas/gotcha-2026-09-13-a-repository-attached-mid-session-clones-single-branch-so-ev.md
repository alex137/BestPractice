---
slug:            gotcha-2026-09-13-a-repository-attached-mid-session-clones-single-branch-so-ev
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A repository attached mid-session clones single-branch, so every branch you create there reads as "unpushed" forever — including to a Stop hook that then blocks the turn.

## Story

**A repository attached mid-session clones single-branch, so every branch you
create there reads as "unpushed" forever — including to a Stop hook that then
blocks the turn.** `add_repo` hands you a `git clone --depth 1` whose only
refspec is `+refs/heads/main:refs/remotes/origin/main`. The push genuinely
succeeds, but no `origin/<branch>` ref is ever written, so `git rev-list
origin/<branch>..HEAD` cannot resolve. **Pushing again — the honest-looking
remedy — changes nothing, because the push was never the problem.** A second
trap sits on top: `add_repo`'s clone URL is lowercased, so GitHub answers
`remote: This repository moved`, which reads like the cause and is not.
Confirm with `git ls-remote origin refs/heads/<branch>` — that talks to the
server and ignores local refs — then repair rather than re-push: `git config
--unset-all remote.origin.fetch`, `git config --add remote.origin.fetch
'+refs/heads/*:refs/remotes/origin/*'`, a bounded `git fetch --depth=50 origin
<branch>`, and `git branch --set-upstream-to=origin/<branch>`. The refspec
half self-applies at session start now — but only where the hook runs, which
is not an attached sibling (see below). The clone-URL capitalization half is
never automated: nothing local knows the canonical spelling, so that stays a
manual `git remote set-url`.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
