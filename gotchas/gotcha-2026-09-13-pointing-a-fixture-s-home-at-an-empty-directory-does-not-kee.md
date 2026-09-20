---
slug:            gotcha-2026-09-13-pointing-a-fixture-s-home-at-an-empty-directory-does-not-kee
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

Pointing a fixture's `HOME` at an empty directory does not keep it empty: `precedent_resolve.load_config()` CLONES the individual source into it.

## Story

**Pointing a fixture's `HOME` at an empty directory does not keep it empty:
`precedent_resolve.load_config()` CLONES the individual source into it.** The
self-heal re-runs `.claude/hooks/precedent-individual-bootstrap.sh` whenever
the individual source looks unusable, so any tool that resolves sources -- the
leak gate among them -- writes `.config/` and a whole `precedent-individual/`
clone into whatever `HOME` you handed it, then reports that the source
RESOLVED. 2026-09-08: a fixture built to reproduce "no private source could be
attached" turned itself into "a private source resolved" mid-run, and the
gate's refusal was read as a bug in the gate for an hour. **The tell is the
fixture home having contents you did not put there** -- `ls -a` it after the
run, not before. To hold the unresolved state, unset `CLAUDE_CODE_REMOTE` as
well: the self-heal is deliberately narrow and fires only in a hosted session.
Same shape as [fixture-owns-its-state](../practices/fixture-owns-its-state.md),
one level further out -- the fixture owned its `HOME` and still did not own
what the code under test would do to it.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
