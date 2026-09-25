---
slug:            gotcha-2026-09-25-a-session-rooted-above-every-repo-it-touches-gets-hooks-and
status:          live
noted:           2026-09-25
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A hosted session whose project directory sits ABOVE every repo it touches
(`/home/user` holding several sibling clones, none of them
`$CLAUDE_PROJECT_DIR`) gets its git state reset mid-session -- the commit
identity in `~/.gitconfig` flips back to the container's own bot account
with no `git config` command in between, and `HEAD` moves onto the base
branch with no repo tool in the loop -- by something outside any repo's own
tooling entirely.

## Story

Working session `session_0167nayvKnbUWA3e6UHih7jS`, 2026-09-25, across four
sibling clones (`precedent-individual`, `precedent-shared-working-style`,
`precedent-shared-writing`, `precedent-shared-repo-maintenance`), none of
them `$CLAUDE_PROJECT_DIR`.

**Every hook, in every repo, all session.** `$CLAUDE_PROJECT_DIR` was empty
the whole time; neither `/home/user/.claude` nor `/root/.claude/settings.json`
existed. [commit-identity.sh](../.claude/hooks/commit-identity.sh),
[freshness-guard.sh](../.claude/hooks/freshness-guard.sh),
[doc-lint-gate.sh](../.claude/hooks/doc-lint-gate.sh),
[push-check-gate.sh](../.claude/hooks/push-check-gate.sh) and
[precedent-paths.sh](../.claude/hooks/precedent-paths.sh) -- SessionStart
and PreToolUse alike -- never fired, for any of the four repos. The
existing gotcha
([The session's PRIMARY repo does not run its SessionStart hooks either](gotcha-2026-09-13-the-session-s-primary-repo-does-not-run-its-sessionstart-hoo.md))
already covers a session rooted one directory above its primary repo; this
is the same mechanism generalized one step further -- when the session root
sits above *every* attached repo and none of them is `$CLAUDE_PROJECT_DIR`,
there is no privileged repo whose hooks fire at all. "The primary repo's
hooks are inert" understates it in this topology: nothing's are.

**With hooks inert, the global identity flipped on its own, mid-session.**
`~/.gitconfig` is one file shared by every repo in the container, with no
per-repo override. It started the session as `Claude <noreply@anthropic.com>`
(the harness's default signing identity). Hand-running `commit-identity.sh`
fixed it to the session's own resolved individual identity (name and email,
per the identity resolution order in
[commit-identity.sh](../.claude/hooks/commit-identity.sh)) and turned off
`commit.gpgsign`. Later in the *same* session, with no `git config` command
run in between, the same global file was back to
`Claude <noreply@anthropic.com>` when checked from a different repo.

**The signing helper is a live process with a documented hand in git
config.** `git config --global gpg.ssh.program` is `/tmp/code-sign`, a
symlink to `/opt/env-runner/environment-manager` -- the container's session
orchestrator, running as a persistent process (`ps aux` showed
`environment-manager task-run --stdin --session <id> --session-mode
resume`). It is the only thing in the container with both a motive (session
lifecycle) and a documented hand in git config: it is the commit-signing
helper. It is flagged here as the best-fit suspect for the identity flip,
not established as its cause -- no reproduction isolated `environment-manager`
doing it.

**This is the same unexplained shape [tools/precedent_session_check.py](../tools/precedent_session_check.py)
row 7 already carries from 2026-09-08**, where a checkout moved from its
working branch onto the declared base branch mid-session with none of the
three obvious suspects (`precedent_vendor_engine.py seed`,
`precedent_refresh_sources --apply`, `checkin.py fresh`) responsible. This
session independently hit the same shape -- `HEAD` moved to `main`
mid-turn -- on two different repos, with none of those three tools in play,
consistent with the same external cause as the identity reset above. Row 7's
own comment already says the cause is not known; this session adds a second,
independent occurrence rather than a diagnosis.

**The one mechanism this repo already fixed for a mid-session reset does not
apply here.** A retired gotcha
([freshness-guard's user-prompt mode hard-resets a mid-session branch](gotcha-2026-09-20-freshness-guard-s-user-prompt-mode-hard-resets-a-mid-sess.md)
-- `mode_user_prompt` hard-resetting a diverged clean branch) covered
exactly this symptom shape and was fixed 2026-09-23 by removing the reset
from every mode. That fix lives inside a hook. In this topology the hook
never runs at all -- so whatever moved `HEAD` here cannot have been
`freshness-guard.sh`, fixed or not, and the branch-flip is corroborating
evidence that row 7's cause sits outside every repo's own tooling, exactly
as its comment already guesses.

**Unconfirmed theory, flagged as a theory and not a finding.**
`CLAUDE_CODE_WORKER_EPOCH` was `3` by the time it was checked this session. A
worker recycle re-running `environment-manager`'s own init is a plausible
reason the flip lands mid-turn rather than at a clean turn boundary -- it
would explain why identity and `HEAD` are both touched by the same
external actor, and why neither move lines up with anything a repo's tools
did -- but nothing this session did caught the epoch changing in the act,
so treat this as a lead for whoever investigates next, not as the cause.

## Fix

**Not established beyond documenting it defensively.** No reproduction
isolated what flips the identity or moves `HEAD`, so there is nothing to
patch in this repo's own tooling -- the actor is outside every repo's
tooling by this session's own evidence. Until a cause is confirmed:

- In this topology (a multi-repo session rooted above every clone it
  touches, none of them `$CLAUDE_PROJECT_DIR`), do not treat a clean
  [tools/precedent_session_check.py](../tools/precedent_session_check.py)
  run near session start as good for the rest of the session -- both the
  identity and row 7's branch check can go bad again later with nothing in
  the transcript to explain it. Re-run it before any commit or push, not
  only once.
- Row 7's own baseline stamp only catches a branch move on a run *after*
  the one that recorded the baseline -- it does nothing if the flip happens
  before the first check ever runs. In this topology, run
  [tools/precedent_session_check.py](../tools/precedent_session_check.py)
  (by hand; the hook that would otherwise gate this never fires) as close
  to the start of work as possible, specifically so the baseline exists
  before anything can move `HEAD` off it.
- Verify `git config user.email` immediately before authoring a commit
  rather than trusting an earlier fix to have held -- this session's own
  fix did not hold.
