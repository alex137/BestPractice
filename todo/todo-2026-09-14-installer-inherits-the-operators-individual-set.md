---
slug:              todo-2026-09-14-installer-inherits-the-operators-individual-set
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "deciding whether [tools/precedent_install.py](../tools/precedent_install.py) should run the sync and the check with the individual source masked, or whether the sync should never materialise a source the target's own `precedent.json` does not declare."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="installer-inherits-the-operators-individual-set"></a>**The
    one-command installer writes the OPERATOR's individual practices into
    the adopter's project, and the adopter's first check reads `3
    violated` where SETUP.md promises `0`.** Found by the evening very deep
    check of 2026-09-14 ([spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md)),
    rehearsing [SETUP.md](../SETUP.md)'s exact command into a scratch project
    from this container. The project's `precedent.json` declares only the
    universal source, but the sync and `precedent_check.py` also resolve
    the container's user-level individual source, so the adopter's
    committed `AGENTS.md` carries three private practices in its resident
    block (`audience-register`, `reply-fits-one-screen`, `reply-is-short`)
    and the check runs three individual checks (`claude-web-bootstrap`,
    `commit-author`, `fresh-before-write`) that a fresh project cannot pass.
    SETUP.md itself says an individual source "is never touched by this
    session at all". Private text in a stranger's tree is the class the
    leak gate exists for. **Blocked on:** deciding whether
    [tools/precedent_install.py](../tools/precedent_install.py) should run the
    sync and the check with the individual source masked, or whether the
    sync should never materialise a source the target's own `precedent.json`
    does not declare. **Disposition:** ask (2026-09-14, the evening very
    deep check)

## How It Closes

Not open until: deciding whether [tools/precedent_install.py](../tools/precedent_install.py) should run the sync and the check with the individual source masked, or whether the sync should never materialise a source the target's own `precedent.json` does not declare.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
