---
slug:              todo-2026-09-13-wire-individual-hook-in-existing-sets
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "four repositories this session was not scoped to, under a different owner, each with its own merge rules — which is why it was handed off rather than done here."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-13
closed:            null
---
## What

- <a id="wire-individual-hook-in-existing-sets"></a>**Wire
    `precedent-individual-bootstrap.sh` into the four practice sets that
    already exist.** As of 2026-09-13
    [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
    installs and wires that hook in every set it creates, and
    [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
    vendors the `precedent_source_bootstrap.py` it execs — so a **new** set
    resolves the person's individual practices from its first session. The
    four real sets (`precedent-individual`, `precedent-team-writing`,
    `precedent-team-repo-maintenance`, `precedent-team-working-style`) predate
    both and get neither.

    **What they are missing is the hook FILE and one `SessionStart` command
    each**, ahead of `commit-identity.sh`, which reads the individual set for
    the author and the timezone. **Both halves are by hand**, and this item
    said otherwise until it was measured against the four real sets:
    [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
    `--apply` writes neither. A hook no `settings*.json` declares lands in
    that tool's `unwired` bucket rather than its `missing` one, and
    `_repairable()` excludes `unwired` deliberately — writing a file nothing
    declares produces a hook that still never runs, plus a diff nobody asked
    for, and rewriting somebody's existing `.claude/settings.json` is
    guesswork about a file they wrote. It reports the gap instead, per set,
    at every session start — measured 2026-09-13, all four: *"hooks present
    but no settings*.json wires precedent-individual-bootstrap.sh"*. Read
    that *"hooks present"* as the message's own stock wording for the wiring
    case, not as a claim about this hook: in all four sets the file is absent
    too.

    **Note the set's own layout differs.** `precedent-individual` wires its
    hooks from `bootstrap/` rather than `.claude/hooks/`, which its own
    `commit-author` practice documents, so the command added there names that
    path — the check reads what `settings.json` invokes, not where the
    generator would have put it.

    **HANDED OFF 2026-09-13, one session per set**, on Morgan's instruction
    to spawn them rather than carry the work cross-owner from here
    (`strength: decided` — he asked for it in those words). Each is rooted in
    its own set and seeded with the whole procedure: clone this public
    repository, `precedent_vendor_engine.py refresh` to pick up
    `precedent_source_bootstrap.py` (new to `ENGINE_FILES` in PR #284), then
    `precedent_bootstrap_source.py --write-session-hook`, the wiring, the
    end-to-end run under a fixture `HOME`, and the set's own checks.

    | Set | Session |
    |---|---|
    | `precedent-individual` | `session_01X7JgfabNF6mSvR7dpqVeAV` |
    | `precedent-team-writing` | `session_01BLrNAxdBkyD4QtMrg4Z57Q` |
    | `precedent-team-repo-maintenance` | `session_0185SF928m3c1dgtAj2uyFR8` |
    | `precedent-team-working-style` | `session_019Tas6QAJHUXwXwUv7ksDYf` |

    **A spawned session CAN report back** — `create_trigger` with
    `persistent_session_id` fires into a named session, established 2026-09-13
    — but these four were not seeded with a return address, so none of them
    will: each ends on a one-line status in its own transcript. This item
    closes when `precedent_refresh_sources.py` stops naming the set at session
    start, which is the check to run rather than a summary to trust.

    **Blocked on / out of scope:** four repositories this session was not
    scoped to, under a different owner, each with its own merge rules — which
    is why it was handed off rather than done here.
    **Disposition:** wait

## How It Closes

Not open until: four repositories this session was not scoped to, under a different owner, each with its own merge rules — which is why it was handed off rather than done here.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
