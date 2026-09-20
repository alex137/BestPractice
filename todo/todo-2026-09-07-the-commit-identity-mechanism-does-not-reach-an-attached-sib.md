---
slug:              todo-2026-09-07-the-commit-identity-mechanism-does-not-reach-an-attached-sib
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing here. What remains is per-repo wiring, and a correction to the declining repo's reasoning when someone next works there."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            null
---
## What

- **The commit-identity mechanism does not reach an attached sibling
  repo, so `commit-author` is silently unenforced in exactly the sessions
  that do cross-repo work.** Found 2026-09-07 by the
  [very deep check](../spec/VERY_DEEP_CHECK.md)'s pass 2. All four clones in
  that session carried `Claude <noreply@anthropic.com>`, the precise failure
  the individual set's `commit-author` Story records as having been replaced
  by a mechanism on 2026-09-06. The mechanism is correct; it is a
  `SessionStart` hook, and a repo that is not the session's primary never
  runs one — which AGENTS.md's own `add_repo` gotcha already states in
  general terms. What is new is the consequence: a practice with a real
  mechanical check goes unenforced without anything saying so, and the
  session must notice and set four git configs by hand.
  **Answered 2026-09-07, and the answer was a third layer.** The question
  this item posed — whether the `pre-commit` backstop can be installed by
  something other than a hook that never fires — has a yes:
  [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh) now runs
  the individual set's own `bootstrap/commit-identity.sh` once per attached
  Precedent repo, with `CLAUDE_PROJECT_DIR` pointed at each. The PRIMARY
  repo's hook does fire, so it carries the reach the sibling's own hook
  never gets. No name, address or zone is copied anywhere — it runs that
  set's script, which reads that set's `identity.json`, still the single
  declaration (registry-source-of-truth). The timezone half went the same
  way and one step further: the script now derives the declared zone into
  `.claude/settings.local.json`'s `env` block, so it reaches the whole of
  the next session rather than being retyped per commit (see
  [INSTALL.md](../INSTALL.md)'s commit-identity section).
  **What is still open, and it is narrower than this item was:** all of that
  reaches a repo only from a session whose primary repo carries the updated
  `session-start.sh`. A repo that has not wired `commit-identity.sh` at all
  is untouched — and at least one dependent repo declined to wire it,
  reasoning that it "resolves an identity" where that repo's `commit-author`
  practice fixes one. That reasoning inverts what the hook does: resolution
  is how it avoids naming a person in a shared file, and when the answer
  comes from a DECLARATION (an `identity.json`, or an explicit override) it
  then ENFORCES that exact author and timezone with a `pre-commit` refusal —
  which is the mechanical enforcement `commit-author` otherwise does not
  have. The hook also needs no Precedent layout: it reads `identity.json`
  from the repo root or from the individual source named by
  `~/.config/precedent/config.json`, so a classic-layout repo can wire it
  today without migrating anything.
  **Blocked on:** nothing here. What remains is per-repo wiring, and a
  correction to the declining repo's reasoning when someone next works
  there.

## How It Closes

Not open until: nothing here. What remains is per-repo wiring, and a correction to the declining repo's reasoning when someone next works there.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
