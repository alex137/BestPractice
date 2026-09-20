---
slug:            gotcha-2026-09-08-the-session-s-primary-repo-does-not-run-its-sessionstart-hoo
status:          retired
noted:           2026-09-08
severity:        null
retired:         "2026-09-08"
retires_when:    null
---
## Symptom

The session's PRIMARY repo does not run its SessionStart hooks either,

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The session's PRIMARY repo does not run its SessionStart hooks either,
  when the harness rooted the session one directory ABOVE it — and this
  project's own required layout is what causes that.** The entry above is
  about an attached sibling; this is its mirror image and reads as the
  opposite, because here the repository *is* the one you are working in,
  its hooks are committed, executable and correctly wired, and they still
  never fire. 2026-09-08, a session opened with four Precedent repos side
  by side under `/home/user` — the layout a team source requires, since it
  resolves as a *sibling clone* — and the harness set the session root to
  that parent. Every hook in
  [.claude/settings.json](../.claude/settings.json) is written as
  `$CLAUDE_PROJECT_DIR/.claude/hooks/…`, `/home/user` has no `.claude/`,
  so every one of them resolved to nothing. Silently: a hook whose path
  does not exist is not an error anybody sees.
  What was absent, all at once: the commit identity (so `user.email` was
  still `noreply@anthropic.com`, and every commit would have been a
  wrong-author commit this repo's own check refuses), the global commit
  backstop, the freshness guard, the `pip install`, the path-trigger
  channel, the Stop-time git check — and
  `.precedent/SESSION_PRACTICES.md`, which is the ONLY route by which the
  private team and individual practices reach a session at all. That file
  did not exist, so **53 practices that bind work here were silently not
  in force**, including `audience-register`, which governs how every reply
  in the session is written. AGENTS.md's own Standing Instruction told the
  session to read a file that was never generated.
  **Do not diagnose this from `env`** — `CLAUDE_PROJECT_DIR` is usually
  not set in a tool shell at all, so reading it proves nothing either way.
  Test the *effects*:
  [tools/precedent_session_check.py](../tools/precedent_session_check.py)
  checks each guarantee by what
  it left behind (does `.precedent/SESSION_PRACTICES.md` exist, is
  `user.email` a person, is `core.hooksPath` set, do `cmarkgfm` and
  `markdown` import, does `remote.origin.fetch` carry `refs/heads/*`, is
  the checkout behind origin) and `--apply` runs the three SessionStart
  hooks by hand. It cannot itself be a hook, for the obvious reason: the
  failure *is* that hooks do not run, so anything waiting to be triggered
  is the one thing guaranteed not to fire — the same shape as the
  freshness guard that shipped inside the checkout it guarded.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
