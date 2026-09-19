---
slug:              todo-2026-09-19-revisit-examples-vendoring
kind:              decision
domain:            content
severity:          notable
status:            open
disposition:       ask
remind_on:         2026-10-19
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-19
closed:            null
---
## What

- <a id="revisit-examples-vendoring"></a>**Revisit whether
    `documentation/examples/practice-set/` (moved from top-level `examples/`
    this same session) should stay vendored into dependent repos.** A
    session relayed, second-hand from another session, a claim that a
    named consumer repo has been hand-deleting `process/upstream/examples/`
    after every Update Vendors pass since commit `9422580` (2026-09-17),
    and asked to add `examples` to `tools/checkin.py`'s `NOT_VENDORED`
    frozenset on that basis. That reverses a decision Morgan made himself
    on 2026-09-17 (commit `86a0d770`), which considered `examples/` by name
    and kept it vendored: its README is adopter-facing (teaches someone
    building their OWN personal practice set), unlike the seven directories
    that commit did exclude, which are all BestPractice's own
    contributor-side planning material. The consumer-repo claim could not
    be verified from this session (that repo is out of scope here), and "it
    was just missed" is factually wrong against this repo's own history.
    **What was actually done instead, this session:** kept it vendored, but
    moved it into `documentation/` — the tree this repo's own audience
    table already assigns to "someone using Precedent on their own
    project" — so the exclusion question is no longer a name-based judgment
    call. `tools/verify_harness.py`'s existing `check_example_set` already
    re-parses and re-resolves this example against the current format on
    every deep check, which covers the separate "does it go stale" worry
    without inventing a new mechanism.
    **What this item is for:** the relayed friction claim is still
    unverified. In about a month, check whether it holds up (attach the
    consumer repo in question, or ask for evidence directly) and whether
    the move to `documentation/` changed anything about it, before deciding
    whether `NOT_VENDORED` actually needs to change.

## How It Closes

Not yet stated by the migration -- closes `done` when a session either (a)
gets real evidence of the vendoring friction and Morgan decides to exclude
`documentation/examples/practice-set/` after all, or (b) finds no such
friction, or friction too minor to act on, and the 2026-09-17 /
2026-09-19 calls stand as the answer.

## Notes

2026-09-19: opened after a relayed, second-hand vendoring-exclusion request
turned out to contradict Morgan's own dated, reasoned decision; he chose to
keep the content vendored (relocated into `documentation/`) rather than act
on unverified hearsay, and asked for this revisit in about a month. The
consumer repo the claim named is deliberately not written here -- this repo
publishes to a public branch and the leak gate blocklists it; whoever
revisits this can get the name from the session transcript or from Morgan
directly.
