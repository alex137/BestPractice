---
slug:              todo-2026-09-06-done-2026-09-06-the-individual-source-bootstrap-hook-is-inst
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-06
---
## What

- **Done 2026-09-06 — the individual-source bootstrap hook is installed
    here, and this repo is now checked as a consumer of its own install
    instructions.** The item said this was blocked on a session that could
    reach the individual repo, "since an untested session-start hook must
    not be committed blind". That was the wrong blocker: what must never
    happen is a hook that blocks session start, and *that* is testable
    without any access at all — run it in an environment where its clone
    cannot succeed and require exit 0. It does, and
    [tools/verify_harness.py](../tools/verify_harness.py) now asserts it,
    alongside a case that this repo carries the hook at all. Writing it
    needed a real fix first: `--write-session-hook` was reachable only
    after `bootstrap()` created a whole individual set, so the "run it
    again against an already-bootstrapped set" both
    [INSTALL.md](../INSTALL.md) and
    [spec/BOOTSTRAP_NEW_SOURCES.md](../spec/BOOTSTRAP_NEW_SOURCES.md)
    documented could not be run — which is the real reason this repo had
    no hook. `--dest` is now optional for hook-only writes, both documents
    say so, and a harness case covers it.

## How It Closes

Already closed 2026-09-06 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
