---
slug:            gotcha-2026-09-20-freshness-guard-s-user-prompt-mode-hard-resets-a-mid-sess
status:          live
noted:           2026-09-20
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A local commit made mid-session, on a clean working tree, disappears between
one turn and the next -- `git log` shows the branch back at `origin`'s tip,
with no error, no warning shown to the model, and no dirty-tree complaint to
explain it.

## Story

A session on `precedent-beta-v01` committed a real change locally (working
tree clean afterward) and started a long-running background check. While
that check ran, another session pushed an unrelated commit to
`origin/precedent-beta-v01`, so the two branches diverged: one commit ahead
locally, one commit behind. The next turn began with a `<task-notification>`
about the background check finishing -- an ordinary prompt, containing
nothing about git. `git log` afterward showed `HEAD` back at `origin`'s tip;
the local commit was simply gone, recovered only because `git reflog` still
had it (`reset: moving to origin/precedent-beta-v01`).

**The mechanism is `.claude/hooks/freshness-guard.sh`, and it does exactly
what its own comments say -- for the wrong caller.** `mode_session_start`
contains a documented, deliberately safe reconcile: when a branch has
diverged from its own remote and the working tree is clean, it stashes the
old tip under `refs/freshness-guard/pre-reset/` and then
`git reset --hard origin/$branch`. The safety argument for this, written
directly above the code (`freshness-guard.sh` lines ~461-465), is explicit:

> "This is SessionStart, before this session's first turn -- nothing
> reachable from local HEAD can be this session's own work yet, so a
> diverged-but-CLEAN checkout here is safe to reconcile automatically,
> unlike the identical-looking check in `mode_pre_write` (which runs
> mid-session, where a local commit really could be this session's)."

That premise is true for the actual `SessionStart` hook, which fires once,
before the first turn. **It is false for `mode_user_prompt`**, which fires
on every `UserPromptSubmit` (throttled to once per
`precedent.freshness.intervalSeconds`, default 600s) for as long as the
session runs -- and `mode_user_prompt` does not have its own reconcile
logic. It delegates straight to `mode_session_start` (the file's own
comment: "Deliberately delegates to `mode_session_start` instead of
restating its checks"), which means the SessionStart-only safety argument
gets inherited by a call path that runs constantly mid-session, long after
local `HEAD` can and does hold this session's own unpushed commits. The
throttle limits how OFTEN this fires; it does nothing to limit WHEN in the
session's life it is allowed to fire.

A background task's completion notification counts as a prompt submission
for this purpose -- there is nothing user-typed about it, but
`UserPromptSubmit` does not distinguish the two, so the guard runs on the
same schedule either way.

**What made this a near-miss rather than a real loss**: the reconcile path
does rescue the discarded tip to `refs/freshness-guard/pre-reset/<branch>-<sha>`
before resetting, exactly as designed, and `git reflog` also kept it. Both
of those are lucky safety nets for a call this code path should never have
made, not evidence the behavior is fine -- a session that does not think to
check `git log` against its own memory of having committed, or that runs
`git gc` before reflog expiry, would simply lose the work.

## Fix

**Not fixed here.** The correct fix is in `mode_user_prompt`
(`.claude/hooks/freshness-guard.sh`): it should not delegate to the
unconditional-reconcile branch of `mode_session_start` at all, or
`mode_session_start`'s reconcile step needs a flag that only the real
`SessionStart` hook invocation sets, so a mid-session `UserPromptSubmit`
gets the `mode_pre_write` treatment (report and name the command; never
reset automatically) instead of the SessionStart treatment. Until that
lands, treat any `NOTE: freshness-guard: '<branch>' had diverged... --
reconciled it to origin/<branch>` seen mid-session (not on the session's
first turn) as a sign that a local commit was just discarded -- check
`refs/freshness-guard/pre-reset/` and `git reflog` immediately, before
anything else touches the branch.

**Immediate recovery, if it already happened**: the discarded tip is a real
commit object until reflog expiry actually runs, so `git reflog` (or the
named `refs/freshness-guard/pre-reset/<branch>-<sha>` ref) finds it. If
origin has moved on other files in the meantime, `git cherry-pick <sha>`
onto the new tip is safer than resetting back to the old one, since a hard
reset back would discard whatever else landed on `origin` since.
