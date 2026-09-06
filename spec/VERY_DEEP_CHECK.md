<!-- Last updated: 2026-09-06, no run in progress -->

# Very deep check — run record

The state of the current [very deep check](../practices/very-deep-check.md),
and the ledger of the ones before it. The check is deliberately more than one
session's work, so a session picks up at the first pass below that is not
marked done rather than starting over. A pass is never quietly skipped: one
deliberately not run is recorded here as not run, with the reason.

**How to use this file.** A session starting or resuming a run fills in the
table, then records what each pass turned up under it: what was found, what
was fixed in the same pass, and what was deferred with the
[TODO.md](../TODO.md) line it went to. When the last pass is done, collapse
the run to one row under "Runs so far" and clear the table for the next one —
this document holds the run in progress, not an archive of every finding
([docs-are-current-state](../practices/docs-are-current-state.md); the
findings themselves live in the commits that fixed them and in
[TODO.md](../TODO.md)).

## Current run

**No run in progress.** The table below is the shape a run fills in.

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | not started | — | fresh install, migration, empty neighbourhood, permissions |
| 2 — mechanisms | not started | — | the thirteen questions |
| 3 — coherence read | not started | — | drift, links, keywords, cost |
| 4 — catalogue and housekeeping | not started | — | full practice audit, backlog, stale branches |

Roadblocks (pass 1 and 2 findings that strand an adopter) are fixed before
anything from passes 3 and 4, whatever order they were found in. A run is not
done while one is open.

## Runs so far

| Run | Passes completed | What it changed |
|---|---|---|
| — | — | no very deep check has been run against the four-pass definition yet |

The 2026-09-06 [pre-launch audit](PRELAUNCH_AUDIT.md) is the closest thing to
a prior run, and is where pass 1's method and all but one of pass 2's
questions come from — it was not run under this practice, and its own
still-open list is a separate document, kept there rather than copied here.
