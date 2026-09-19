---
slug:              todo-2026-09-14-setup-default-is-the-loader
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          ""anything you think we should do, just do it and Go Merge" -- Morgan delegated the call; SETUP.md was flipped to install the loader (§0) by default instead of the classic vendored model (§1)."
decision_strength: assented
waiting_on:        null
noted:             2026-09-14
closed:            2026-09-14
---
## What

- <a id="setup-default-is-the-loader"></a>**Decide whether [SETUP.md](../SETUP.md)'s
    guided install should install §0 (the loader) instead of §1 (the classic
    vendored model).** Raised 2026-09-14 by the very deep check, which
    rehearsed all three paths with fresh eyes. What a non-technical
    administrator gets today from the one document written for them is the
    classic model: the vendored prose, the audit, the check-in loop — and
    **not** the resident block, the occasion index or the enforced checks,
    which is everything [documentation/ADOPTING.md](../documentation/ADOPTING.md)
    and [README.md](../README.md) promise ("they show up when they matter";
    "where a practice can be checked, it is"). The classic template
    ([templates/AGENTS.md.template](../templates/AGENTS.md.template)) carries no
    generated block at all, and §1 never runs the sync. A §1 project that
    later wants the loader takes
    [spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md),
    which the same check found is still a rough road. §1's reasons to stay
    the default — the export gate and check-in loop, the manifest audit —
    are optional by their own headings (§3, §4), and §0 was rehearsed
    against a real project on 2026-09-14 with the defects it found fixed the
    same day. The session's recommendation: flip the default to §0 and keep
    §1 for a project that wants the check-in loop, in one change that also
    retires §1's `reply-gate.sh`/`precedent-paths.sh` wiring problem (next
    item). **Blocked on:** Morgan's decision — it changes what every new
    adopter receives. **Disposition:** ask (2026-09-14, the very deep check)

    **CLOSED 2026-09-14 — flipped, the same day.** Morgan, on the check's
    reply: *"anything you think we should do, just do it and Go Merge"*
    (`strength: assented` — the recommendation was the session's, and he
    delegated rather than chose). [SETUP.md](../SETUP.md) now installs §0
    through [tools/precedent_install.py](../tools/precedent_install.py), a
    one-command install added in the same change so that the nine prose
    steps a rehearsal had just found drifting stop being steps a person
    follows. §1 stays documented for a project that wants the classic
    check-in loop.

## How It Closes

Already closed 2026-09-14 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
