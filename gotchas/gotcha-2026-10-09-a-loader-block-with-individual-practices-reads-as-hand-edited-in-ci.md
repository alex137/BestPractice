---
slug:            gotcha-2026-10-09-a-loader-block-with-individual-practices-reads-as-hand-edited-in-ci
status:          live
noted:           2026-10-09
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A consuming repository's pull request fails GitHub's light check with:

```
VIOLATION generated-artifact-provenance — build_views --check FAIL: hand-edited or stale, drifted from regeneration: AGENTS.md
```

Nothing is stale, and the same check passes in the session that made the
commit. The committed loader block carries some individual-level practices,
its resident header says so (`(5 individual, 6 universal)`), and it has the
paragraph saying the tree "came from an INDIVIDUAL source" and is
"machine-dependent".

## Story

A person's individual set never appears in a repository's `precedent.json`.
It resolves through their user-level config, so a session on their machine
renders it into the block, and a bare GitHub runner has no such config.

`build_views.py --check` already knew that a source it cannot reach makes
the block unverifiable rather than stale: when a declared source is missing,
it says NOT VERIFIABLE and exits 0. That guard looked only at what
`precedent.json` declares, though. On the runner the individual set was not
"missing", it was simply not there, so the guard never fired. The check
regenerated a block without the individual practices, compared it with the
committed one built with them, and reported the difference as a hand-edit.
`precedent_sync_views.py --check` did the same thing and reported every
individual practice file as one a sync would delete. Reproduced on a real
consumer by running the check with `PRECEDENT_USER_CONFIG` pointed at
nothing and `HOME` emptied.

## Fix

`build_views.individual_not_verifiable()` now makes that call for every
reader of the block. It reads the committed evidence (the block's
paragraph, its header count and the levels in `MANIFEST.json`) through one
helper. If those show individual practices and no individual source
resolves, `build_views --check` and `--budgets` say NOT VERIFIABLE,
`precedent_sync_views --check` says the same, and `precedent_check` reports
generated-artifact-provenance and loader-within-caps as COULD NOT VERIFY.
Where the person's set does resolve, a hand-edit still fails. A write goes
ahead and says which practices it leaves out. The harness case is
`check_loader_block_with_an_absent_individual_set`.

To get a real verdict, run the check where the person's individual set
resolves, normally the session that made the commit.
