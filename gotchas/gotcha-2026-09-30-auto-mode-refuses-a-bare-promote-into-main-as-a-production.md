---
slug:            gotcha-2026-09-30-auto-mode-refuses-a-bare-promote-into-main-as-a-production
status:          live
noted:           2026-09-30
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A request that moves work into `main` without naming main -- "merge it",
"push it", or a working-method command that ends there -- comes back
`Denied by auto mode classifier` with the reason `[Production Deploy]`.
Nothing in the repository refused it. The same move goes through when the
person's message names `main`.

## Story

**2026-09-30, a real consumer.** Pre-staging had nothing staging lacked, so
the session read "Promote" as staging into `main`, as
`promote` says it should. Claude Code's auto mode
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
`promote` and `produce`
say this.

**The one durable fix is the person's**: an `autoMode.allow` entry in
managed settings (for cloud sessions, the organization's server-managed
settings, which need a Team or Enterprise plan and an Owner to set them),
or in `~/.claude/settings.json` on a machine that keeps it. The
step-by-step for a person is in
[documentation/CLOUD_SETUP.md](../documentation/CLOUD_SETUP.md).
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

**Prevention: nothing mechanical, deliberately**, because the refusal is
Claude Code's own safety check, outside this repository. The only durable
fix is an allow rule in the person's managed or home settings: no file
Precedent vendors can carry one, and a session must never write one for
itself. A check here would have nothing to read. What the repository can
do it already does: `promote` and `produce` tell the session what to say
and which word gets through. (Written 2026-10-06, after the 2026-10-05
very deep check found no answer recorded.)
