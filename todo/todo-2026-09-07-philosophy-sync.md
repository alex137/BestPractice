---
slug:              todo-2026-09-07-philosophy-sync
kind:              decision
domain:            content
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Morgan chose to move the philosophy essays into this repo outright (philosophy/) rather than a dated snapshot or a vendored-and-synced copy, and retired the source notebook."
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            2026-09-07
---
## What

- <a id="philosophy-sync"></a>**~~Decide how `philosophy/` stays current with the notebook it came from.~~
    Settled 2026-09-07: there is nothing to stay current with.** The
    question was which of three options to take — dated snapshot,
    vendored-and-synced, or move the originals here. Morgan chose the
    third and went further: the project's own prior notes repository is retired, and
    [philosophy/](../philosophy/) is the only copy of these essays. No
    manifest, no sync, no drift — by construction rather than by
    discipline. [philosophy-declares-its-source](../local/practices/philosophy-declares-its-source.md)
    survived the change with its purpose rewritten: the provenance line
    is now a historical record of where the text was argued out, not a
    pointer to something live.
    **Left over, and not this repository's to do:** the notebook itself
    still exists until Morgan deletes it in GitHub's settings — no tool
    available here can delete a repository. Its 220 commits of history,
    its own `TODO.md` and its `GETTING_STARTED.md` go with it. The five
    content-side open questions were rescued into
    [philosophy/ASSORTED_NOTES.md's Open Questions](../philosophy/ASSORTED_NOTES.md#open-questions) first.

    **Its `process/PRECEDENT_MIGRATION.md` was read and deliberately not
    rescued** (2026-09-07). A first pass flagged it as the one document
    worth importing, because
    [spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md)
    cites it as the worked example's own record. Reading it reversed that:
    it says outright that its own reusable half *"is written up generically
    upstream ... so the next dependent repo doing this same migration
    doesn't have to rediscover it"*, and its one finding of consequence —
    that a consumer's scrub gate structurally cannot pass once the
    blocklist term appears in legitimately-vendored upstream documents — is
    already recorded in
    [spec/PRELAUNCH_AUDIT.md](../spec/PRELAUNCH_AUDIT.md), with the remedy.
    What remains is one repository's bookkeeping about itself: its manifest
    entries, its paused workflow, its resolver output, its own
    "audit these entries before the beta pin lifts" note. Importing 28KB of
    that into a public repo where nothing points at it would be a copy kept
    for the feeling of not having thrown anything away.

## How It Closes

Already closed 2026-09-07 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
