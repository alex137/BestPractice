---
slug:            gotcha-2026-09-13-a-source-set-s-hooks-drift-after-installation-and-nothing-ha
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A source set's hooks drift after installation and nothing has ever refreshed them — there was an install path and no repair path.

## Story

**A source set's hooks drift after installation and nothing has ever refreshed
them — there was an install path and no repair path.** Measured 2026-09-09
across five real private sets: one carries a `freshness-guard.sh` three
thousand bytes shorter than canonical, supporting only `session-start` and
`pre-write` with no user-prompt mode (its settings.json wires no
`UserPromptSubmit` to match, so it is self-consistent, just older), and
`commit-identity.sh` is one version behind in **all five**, which is what
uniform drift looks like when canonical moved on after installation.
[tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
installs both hooks when a set is created and nothing revisits them; its
settings.json is also written only `if not settings.exists()`, so
bootstrapping INTO a directory that already has one — which is what a
migration is — yields hooks without wiring, or wiring without hooks. `python3
tools/precedent_refresh_sources.py --apply` now restores a
declared-but-missing hook, **independently of engine staleness**, since the
two go stale independently. Bringing a drifted-but-present hook up to
canonical is still a person's call, and [TODO.md's `source-hook-drift`
item](../todo/todo-2026-09-09-source-hook-drift.md) holds it.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
