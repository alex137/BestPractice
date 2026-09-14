---
slug:        session-bootstrap
title:       Session bootstrap is code, not memory
tier:        on-demand
severity:    default
applies_to:  [".claude/**", "**/hooks/**", "**/bootstrap*", "templates/harness/**"]
occasion:    "setting up a new repo's session start"
gates:       []
index_clause: "setup lives in a session-start hook, not in memory"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 13
---
## Rule
Environment setup that sessions need (packages, dependencies,
submodule init) lives in a session-start hook — idempotent, fast when cached,
warning loudly on failure. Routine safe commands the agent runs constantly go
in a permissions allowlist so sessions don't stall on prompts. Where the
harness also supports a hook at the *other* end of a turn, the same
discipline applies in reverse: don't rely on the agent remembering to check
its own git hygiene before stopping — a stop hook that blocks on
uncommitted, untracked, or unpushed work makes that guarantee automatic
instead.

## Detail

## Why
The gotchas of [environment-gotchas](environment-gotchas.md), applied: writing the fix down is good;
having it apply itself is better. The hook is where "install the one package
whose absence cost two sessions" lives as code — and where "don't end a
session with unpushed work sitting in the tree" lives as code too, rather
than a habit the agent has to remember on its own each time.

## Story

## Install
[templates/bootstrap.sh](templates/bootstrap.sh) →
`tools/bootstrap.sh` (harness-neutral; all real setup lives here), wired in
per-harness via [templates/harness/](templates/harness/README.md): a hook
that runs it automatically where the harness supports one (hard guarantee),
an instructions-file directive where it doesn't (soft guarantee), plus a
permission allowlist where the harness has that concept. Where the harness
also supports a blocking stop/teardown hook (Claude Code does; see
[templates/harness/claude-code/hooks/stop-git-check.sh](templates/harness/claude-code/hooks/stop-git-check.sh)),
install that too — some managed environments already provide an equivalent
check outside the repo, but this makes the same guarantee travel with the
practice layer for the ones that don't.

**The bootstrap also checks upstream freshness — detection automated, the
take deliberate.** A dependent repo learns its practice layer is stale only
when someone remembers the periodic check-in, so the hook runs
`checkin.py fresh`: one clone-free `ls-remote` of the public upstream against
the manifest's recorded base, printing a single notice line only when
upstream has moved (silent when current or offline; never a gate).
*Applying* the update stays a deliberate step (INSTALL.md §2): installs are
adaptive, and unattended mirrors are the mechanism class that loses content —
the carry gate exists because even attended ones did.
