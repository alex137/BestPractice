---
slug:            gotcha-2026-09-06-a-repository-attached-mid-session-clones-single-branch-so-ev
status:          retired
noted:           2026-09-06
severity:        null
retired:         "2026-09-06"
retires_when:    null
---
## Symptom

A repository attached mid-session clones single-branch, so every

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A repository attached mid-session clones single-branch, so every
  branch you create there reads as "unpushed" forever — including to a
  Stop hook that then blocks the turn.** `add_repo` hands you a
  `git clone --depth 1` whose only refspec is
  `+refs/heads/main:refs/remotes/origin/main`. Push a feature branch and
  the push genuinely succeeds, but no `origin/<branch>` ref is ever
  written, so `git rev-list origin/<branch>..HEAD` cannot resolve and every
  freshness check reports the branch as having unpushed commits with no
  remote counterpart. 2026-09-06: this fired on both consumer repos after
  their work was already safely on GitHub, and the honest-looking remedy —
  push again — changes nothing, because the push was never the problem.
  A second trap sits on top of it: `add_repo`'s clone URL is lowercased
  (the owner and repo name lowercased), so GitHub answers with
  `remote: This repository moved`, which reads like the cause and is not.
  Confirm with `git ls-remote origin refs/heads/<branch>` — that talks to
  the server and ignores local refs entirely — then repair the clone rather
  than re-pushing:
  `git config --unset-all remote.origin.fetch`,
  `git config --add remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'`,
  a bounded `git fetch --depth=50 origin <branch>`, and
  `git branch --set-upstream-to=origin/<branch>`. Setting the remote URL to
  the canonical capitalization at the same time stops the misleading
  redirect notice.
  **The refspec half of that repair now applies itself** — 2026-09-06,
  [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh) here and
  [templates/bootstrap.sh](../templates/bootstrap.sh) for dependent repos both
  widen `remote.origin.fetch` at session start when it carries no
  `refs/heads/*` mapping, before the freshness block runs. It is local
  config only, idempotent, and announced on stderr rather than done
  silently. Verified against a real `--single-branch` clone: pushing a
  feature branch from one left `git rev-list origin/feature..HEAD` unable
  to resolve at all, and the repair plus one fetch made it answer `0`. The
  clone-URL capitalization half is *not* automated — nothing local knows
  the canonical spelling — so that stays a manual `git remote set-url`.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
