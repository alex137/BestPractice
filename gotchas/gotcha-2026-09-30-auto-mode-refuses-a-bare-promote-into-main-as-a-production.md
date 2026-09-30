---
slug:            gotcha-2026-09-30-auto-mode-refuses-a-bare-promote-into-main-as-a-production
status:          live
noted:           2026-09-30
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A bare **"Promote"** correctly resolves to staging into `main`, and then
`python3 tools/precedent_branches.py --promote --to main` comes back
`Denied by auto mode classifier` with the reason `[Production Deploy]`.
Nothing in the repository refused it. The same move goes through when the
person says **"Produce"**.

## Story

**2026-09-30, a real consumer.** Pre-staging had nothing staging lacked, so
the session read "Promote" as staging into `main`, as
[promote](../practices/promote.md) says it should. Claude Code's auto mode
then refused the command. Its built-in `soft_deny` rules include production
deploys, and a soft block clears on the person's intent only when their
message "directly and specifically describes the exact action"
([Claude Code docs, auto mode config](https://code.claude.com/docs/en/auto-mode-config),
read 2026-09-30). "Promote" is too general for that; "Produce", the stage-5
word for exactly this move, got through.

The session then tried to add an allow rule itself and was refused again,
as `[Self-Modification]` / `[Auto-Mode Bypass]`. That refusal is correct.
A session that writes its own exceptions to the check has switched the
check off.

**Where an allow rule can live** (same docs page, 2026-09-30): the
classifier reads `autoMode` from `~/.claude/settings.json`, from managed
settings, and from `--settings`. It **never** reads it from a repository's
`.claude/settings.json` or `.claude/settings.local.json`, so nothing
Precedent vendors can carry one. A cloud session starts from a fresh
container, so a rule in its home directory does not outlast the session;
only managed settings reach every one.

## Fix

**In the session:** say in one line that Claude Code's own safety check
stopped the move, not the repository's rules, and ask for "Produce" (or
"Promote 5"). Never route around it: no other command, no GitHub API
merge, no settings edit of the session's own.
[promote](../practices/promote.md) and [produce](../practices/produce.md)
say this.

**The one durable fix is the person's**: an `autoMode.allow` entry in
managed settings (for cloud sessions, the organization's server-managed
settings), or in `~/.claude/settings.json` on a machine that keeps it.
**Keep `"$defaults"` in the list**: an `allow` list without it replaces
every built-in exception. For example:

```json
{
  "autoMode": {
    "allow": [
      "$defaults",
      "Precedent Promote into main: running tools/precedent_branches.py --promote --to main is allowed when the person asked in this session for Promote, Produce or Promote 5. That tool moves main only through a pull request, after the full local check and the GitHub test pass."
    ]
  }
}
```

The wording is prose the classifier reads, not a pattern. Afterwards,
`claude auto-mode config` shows whether it took. A session never adds
this itself.
