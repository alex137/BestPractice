---
slug:              todo-2026-09-14-consumer-cannot-resolve-upstream-commit
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "whichever source is chosen, and one call that must not be made by accident — what the scrub does when upstream's text is unreachable. Skipping the hit silently would rebuild the exact bug `load_blocklist` was written to kill, where a check that did not run reported a pass."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="consumer-cannot-resolve-upstream-commit"></a>**A consumer repo
    cannot read upstream's own text at `upstream.commit` — nothing local
    resolves it — so no check that runs there may assume it can.** Measured
    2026-09-14 in a real consumer, not reasoned about: `process/upstream/` is
    a plain mirrored working tree, not a submodule and not a remote, so the
    repository holds no upstream objects at all; `process/manifest.json`'s
    `commit` is a recorded string, not a resolvable ref; and `git cat-file -e`
    on that commit failed there until BestPractice was cloned separately and
    the fetch deepened.
    **Why it is worth writing down here rather than there.**
    [tools/practice_audit.py](../tools/practice_audit.py) and
    [tools/checkin.py](../tools/checkin.py) are this repo's tools running in
    somebody else's repository, and the natural next feature for the audit's
    scrub — skip a blocklist hit inside `upstream.vendored_at` whose line is
    byte-identical at `upstream.commit`, since a line that arrived FROM
    upstream is upstream's to fix
    ([fix-the-original](../practices/fix-the-original.md)) — reads exactly like
    something a consumer could check locally. It cannot. The only two sources
    for upstream's text there are a source clone passed in as an argument, the
    way [precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
    `refresh <clone>` already takes one, or the mirrored file on disk, which
    proves nothing about the pinned commit.
    Today the scrub's only "this came from upstream" mechanism is the
    hand-maintained `!prefix` path exemption inside the blocklist, which the
    byte-identity idea would generalize.
    **Blocked-on:** whichever source is chosen, and one call that must not be
    made by accident — what the scrub does when upstream's text is
    unreachable. Skipping the hit silently would rebuild the exact bug
    `load_blocklist` was written to kill, where a check that did not run
    reported a pass.

## How It Closes

Not open until: whichever source is chosen, and one call that must not be made by accident — what the scrub does when upstream's text is unreachable. Skipping the hit silently would rebuild the exact bug `load_blocklist` was written to kill, where a check that did not run reported a pass.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
