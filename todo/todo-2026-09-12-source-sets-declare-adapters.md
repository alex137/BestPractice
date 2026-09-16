---
slug:              todo-2026-09-12-source-sets-declare-adapters
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "two things, in order. Each set's vendored engine has to carry the new [tools/precedent_materialize.py](../tools/precedent_materialize.py) before a declaration does anything at all — all four were behind `precedent-beta-v01` at the time of writing, and their own refresh is what moves them. And then it i"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-12
closed:            null
---
## What

- <a id="source-sets-declare-adapters"></a>**Have the private source sets
    declare their harness adapters.** Each of the four attached sets ships
    `bootstrap/*.sh` that its own practices tell a consuming repo to copy into
    `.claude/hooks/` by hand — the individual set's `freshness-guard.sh`,
    `commit-identity.sh` and `session-start.sh` most of all, which are the
    scripts whose silent staleness this mechanism was built for. Declaring
    them is a three-line `adapters` block in each set's own `precedent.json`
    (see [spec/SOURCES.md](../spec/SOURCES.md)'s "Harness adapters travel with the
    source"). This is the
    [cross-source-rollout](../practices/cross-source-rollout.md) half of the
    change, deliberately not taken in the session that built the mechanism.
    **Blocked on / out of scope:** two things, in order. Each set's vendored
    engine has to carry the new
    [tools/precedent_materialize.py](../tools/precedent_materialize.py) before a
    declaration does anything at all — all four were behind
    `precedent-beta-v01` at the time of writing, and their own refresh is what
    moves them. And then it is the same deliberate call as
    `universal-adapters-undeclared`:
    the first sync after a declaration starts writing into consuming repos
    that may hold an older copy on purpose.

    **Measured 2026-09-14, with all four sets on disk, and two of this
    item's own claims are wrong.** First: *"each of the four attached sets
    ships `bootstrap/*.sh`"* — only the individual set does. The three team
    sets have no `bootstrap/` directory at all, so there is nothing for them
    to declare and the work here is one set, not four. Second, and this is
    the blocker: *"each set's vendored engine has to carry the new
    `precedent_materialize.py` before a declaration does anything at all"* —
    none of the four carries it, and the individual set's three declared
    adapters are being written into consuming repos anyway. A SOURCE never
    materializes; the CONSUMER does, out of its own engine. The sets vendor
    a source-set subset that deliberately has no
    `precedent_materialize.py` or `precedent_sync_views.py` in it. So the
    stated blocker was never the real one, and the engine-currency report
    that seemed to clear it was answering a different question.

    **What is actually left here:** the individual set declares three of its
    five `bootstrap/*.sh` — `session-start.sh` and
    `precedent-universal-catalogue.sh` are not declared, and nothing says
    whether that is a decision or an oversight. That question, and nothing
    about the team sets, is this item.

    **Unblocked 2026-09-14**, now that a consuming repo can decline an
    adapter with a reason (see item 72). Declaring the two remaining scripts
    no longer forces every consumer that does not want them into a
    permanent violation, which was the real cost of doing this early. The
    work is one repository — `precedent-individual` — and it is a session
    rooted there, not here: this repository is a different owner and
    `add_repo` refuses across owners (*"cross-tier adds are not supported in
    v1"*, measured 2026-09-14). A push probe from a session holding the clone
    is refused the same way: *"access denied by the git proxy:
    themorgan/precedent-individual is not in this session's authorized
    repository set"*.

    **Universal declared its own seven on 2026-09-14**
    (`universal-adapters-undeclared`,
    now closed), so the pattern this item asks the sets to follow now exists
    upstream to copy.
    **Disposition:** wait (2026-09-12 — a session filed this; nobody has set
    it to `ask`)

## How It Closes

Not open until: two things, in order. Each set's vendored engine has to carry the new [tools/precedent_materialize.py](../tools/precedent_materialize.py) before a declaration does anything at all — all four were behind `precedent-beta-v01` at the time of writing, and their own refresh is what moves them. And then it i

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
