---
slug:            gotcha-2026-09-13-your-commits-are-authored-by-the-bot-because-the-harness-set
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

Your commits are authored by the bot because the harness sets that identity in git's GLOBAL config AND in every clone's LOCAL config — so a global-only fix is silently overridden.

## Story

**Your commits are authored by the bot because the harness sets that identity
in git's GLOBAL config AND in every clone's LOCAL config — so a global-only
fix is silently overridden.** Measured 2026-09-11: `user.name=Claude`,
`user.email=noreply@anthropic.com` in `--global` and in both clones'
`--local`, and no backstop installed to refuse any of it. The cause is the
entry above — a session rooted one directory up, so `commit-identity.sh` never
ran — but the SYMPTOM reads as a git-config problem, and the config it reads
as is one somebody already set on purpose. **The cost is that a wrong-author
commit cannot be repaired after it merges** without rewriting `main`, which is
why `fab8d42` and two entries in the individual set's
`grandfathered_commit_shas` are permanent. **The remedy is one line, and it is
not `git config`:** ``` bash .claude/hooks/commit-identity.sh ``` It sets the
local identity, the GLOBAL one (so a clone attached later inherits a person),
repoints `/etc/localtime`, and installs the global `core.hooksPath` backstop
that refuses a bot-authored commit everywhere.
**`PRECEDENT_COMMIT_NAME`/`_EMAIL`/`_TZ` in the environment is what keeps it
fixed**, and two things that used to undo it are closed at that cause: a
harness run repointing the container's own `/etc/localtime`, and the hook's
fallback rung writing a timezone (TZ) value, `TZ=America/New_York`, into
untracked `.claude/settings.local.json`, where the harness reads it before
hooks run.
Both are archived in full as entry 33. Verified 2026-09-11 in a scrubbed HOME
with no private source, no credential and the bot identity preloaded: the hook
resolved at rung 1 and set the person and the declared offset, never reaching
the fallback. **Where those variables are absent it still bites**, so verify
by effect, never by reading the config you just wrote: `env -u GIT_AUTHOR_NAME
-u GIT_AUTHOR_EMAIL -u TZ git var GIT_AUTHOR_IDENT` must name the person and
the declared offset. **The trap that wastes the time is still live.** The
harness's own Stop hook flags commits whose committer is not
`noreply@anthropic.com` and asks you to `--amend --reset-author` onto exactly
the bot account the individual set's own `commit-author` practice refuses and
its own mechanical check fails on. Neither file is in this repository, which
is why neither is linked here. Following it recreates the violation this
repository spent a day fixing. **The repository's gate wins over generic
harness guidance**; say so and leave the commit alone.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
