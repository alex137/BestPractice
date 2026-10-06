---
slug:              todo-2026-10-05-very-deep-check-pass-3-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-05
closed:            null
---
## What

What the 2026-10-05 very deep check's pass 3 (does the writing hold
together) found and did not fix here. Read in full: the 2026-10-05
repo-maintenance drafts, every active writing-set Rule, the individual
set's ladder practices, the fold-related parts of the top-level documents
and the starter template, and each ladder copy that shares a slug with
universal. Swept, not read in full: the rest of the 174 universal
practices (every one changed since 2026-09-28, about 250,000 words), the
rest of the individual set, and the ladder's own 21.

Fixed the same day in BestPractice: AGENTS.md's stale fleet-sweep mention,
three INSTALL.md passages, 18 stale `approved_by` lines, `install`'s check
name, `deep-check`'s "this set", the template comment's set count, four
pages linking the root TODO.md stub, and README's "vendor in".

- **For Morgan: universal now has two meanings of "deep check".**
  `two-check-levels` defines it as the push suite; the `deep-check`
  practice folded in on 2026-10-05 says asking for one by name also starts
  a whole-repo read. Both are in force together. One sentence can separate
  them; folding the read half into `very-deep-check` would be cleaner, and
  is a call about the vocabulary.
- **The ladder set's copies of `the-boildown` and `vendor-update-runbook`
  have fallen behind universal's**, and they override universal for anyone
  who brings the ladder. Missing: the one-line Boildown when nothing is
  new, a batch of background jobs reporting once, practice ideas "at most
  two", and the [precedent_merge_vendors.py](../tools/precedent_merge_vendors.py) paragraph (plus pre-staging's
  `upstream_branch`, when it lands). Universal's own Story says "edit
  both". Root fix in the engine: a check that fails when a universal rule
  changes after a same-slug override in a set. The copies themselves are
  the ladder set's to fix.
- **The individual and writing sets still name the folded sets** in a
  README and in several deduplicated stubs ("in force there"). Nothing
  breaks, since lookup is by slug; each sentence is now false.
  `precedent_move` should write the slug alone.
- **The writing set's `curly-quotes` cites `fix-typos-keep-ambiguity`**,
  which exists in no source in scope.

## How It Closes

The decision is made and recorded, and each set item is fixed in its set
or recorded here as declined.
