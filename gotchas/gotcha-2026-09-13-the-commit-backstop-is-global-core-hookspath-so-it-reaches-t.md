---
slug:            gotcha-2026-09-13-the-commit-backstop-is-global-core-hookspath-so-it-reaches-t
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

The commit backstop is GLOBAL (`core.hooksPath`), so it reaches throwaway fixture repositories too — and refused them.

## Story

**The commit backstop is GLOBAL (`core.hooksPath`), so it reaches throwaway
fixture repositories too — and refused them.** A repo attached mid-session
inherits the container's *global* identity (measured:
`noreply@anthropic.com`), so a per-checkout fix cannot cover it even in
principle. The cost landed immediately: `verify_harness.py` builds dozens of
temporary repos and commits in them without `TZ`, and the backstop refused the
first one, taking the whole run down in a mechanism unrelated to what was
being tested. **A fixture commit is not a person's commit** — the harness sets
`PRECEDENT_ALLOW_ANY_AUTHOR=1` for every subprocess it spawns. Any other tool
that creates scratch repositories needs the same, and the symptom will not
look like an identity problem. `core.hooksPath` also makes git look THERE AND
NOWHERE ELSE, so the global hooks chain to each repository's own
`.git/hooks/<name>` first — without that, every repo's own gates vanish
silently. Resolve that path with `rev-parse --absolute-git-dir`, never
`rev-parse --git-path hooks`: the latter *respects* `core.hooksPath` and so
names the global directory.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
