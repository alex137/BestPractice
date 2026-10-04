---
slug:              todo-2026-10-04-two-small-engine-leftovers-from-the-produce
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-04
closed:            null
---
## What

- <a id="two-small-engine-leftovers-from-the-produce"></a>**Three small
  engine leftovers, found landing the 2026-10-04 Produce; none is wrong
  today.**

  1. **A second answer to "which paths are someone else's copy".**
     [tools/precedent_regenerate.py](../tools/precedent_regenerate.py)
     keeps its own `VENDORED_TREES` (`process/upstream/` only), and
     [tools/precedent_check.py](../tools/precedent_check.py)'s
     `_vendored_trees()` reads it. `precedent_resolve.mirrored_prefixes`
     is the one place that question is answered, and also names
     `precedent/universal/` where a repository vendors the catalogue. The
     sync's link scan hit exactly this gap: it skipped a hand-kept list
     that missed the catalogue copy, and the full check caught it. Both
     readers should derive from `mirrored_prefixes(repo)` and the
     constant should go.
  2. **`--from-ref` mislabels its source.**
     `precedent_vendor_engine.py refresh --from-ref REF` prints
     "main @ <sha>" for a sha taken from REF, because the branch name is
     the constant `SOURCE_BRANCH`. `precedent_update.py --from-ref` also
     runs whatever tool the BestPractice clone has checked out, so it
     must run from a clone at REF. The consumer rehearsal found the
     second; the label is the first. The label should name REF, and the
     update should either refuse a clone not at REF or run REF's own
     copy.

  3. **A Promote into main says a GitHub test is due where none exists.**
     For a practice set that is not declared private,
     `precedent_branches.py --promote --to main` printed "GitHub test: DUE
     -- every Promote gets it", and `--wait-main-test` on the same branch
     answered "no GitHub test is installed here" (all four shared sets,
     2026-10-04). The Promote's line should read the same installed-test
     fact the wait reads.

  Queued rather than done in the session that found them: all sit
  outside the launch that was authorized, and none blocks anything.

## Closes when

Both readers of vendored paths derive from `mirrored_prefixes`, with no
second list left, and `--from-ref` names the ref it took and refuses or
re-runs from a clone not at that ref, and a Promote into main reports a
GitHub test as due only where one is installed. Each change has a harness case shown
failing without it.
