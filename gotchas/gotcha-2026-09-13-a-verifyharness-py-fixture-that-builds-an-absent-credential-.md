---
slug:            gotcha-2026-09-13-a-verifyharness-py-fixture-that-builds-an-absent-credential-
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A `verify_harness.py` fixture that builds an "absent credential" scenario inherits the container's real one, and so asserts the opposite of what it ran.

## Story

**A `verify_harness.py` fixture that builds an "absent credential" scenario
inherits the container's real one, and so asserts the opposite of what it
ran.** Three separate variables have done it — `PRECEDENT_GIT_TOKEN`,
`PRECEDENT_SOURCE_BASE_URL` and `PRECEDENT_FRESHNESS_ALSO` — and the diagnosis
fails in the expensive direction each time: the failure reads as *missing*
access you in fact have, or as a guard blocking on a repository the fixture
never created. **Separate the two by re-running with the variables unset** —
failures that *disappear* were inheritance, not absence. All three are
scrubbed at the head of [tools/verify_harness.py](../tools/verify_harness.py)
now, and `check_fixtures_own_the_credential_environment` plants them and
asserts they come back gone, so this bites only a NEW variable nobody has
scrubbed yet. **The generalization is the part worth keeping: an ABSENCE is
state too** — a fixture constructing "nothing is available" owns that absence
and must clear the environment, not merely decline to set anything
([fixture-owns-its-state](../practices/fixture-owns-its-state.md)). Full story,
all three instances, in [record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md)
entry 32.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
