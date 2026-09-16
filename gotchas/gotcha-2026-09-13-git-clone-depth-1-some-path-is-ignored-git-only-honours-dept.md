---
slug:            gotcha-2026-09-13-git-clone-depth-1-some-path-is-ignored-git-only-honours-dept
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

`git clone --depth 1 /some/path` is ignored; git only honours `--depth` over a transport.

## Story

**`git clone --depth 1 /some/path` is ignored; git only honours `--depth` over
a transport.** A phase-2 smoke test believed it was exercising a shallow clone
for an hour and was not — the bug it was written to catch was still there. Use
`file:///some/path` to force a genuinely shallow local clone. (Used again
2026-09-08 to build the fixture that proves the carry check refuses rather
than inventing lost content.)

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
