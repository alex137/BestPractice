---
slug:            gotcha-2026-10-03-a-file-carried-by-hand-to-match-upstream-held-every-refresh-up
status:          live
noted:           2026-10-03
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

The session-start survey shows a practice set as STALE at every session
start, with a FAIL row ending "A reason is required. Do NOT reach for
`record-ci` here". The file the refresh calls hand-edited is identical to
BestPractice's own copy.

## Story

On 2026-10-03, rehearsing a Produce, the individual set's refresh refused
on `bootstrap/commit-identity.sh`. Its last commit there was a carry of
upstream's newer copy, made before the refresh that would have brought it.
The manifest still held the older copy's hash, so the refresh read the
carried file as a hand-edit and refused to overwrite it, though the file
was byte-for-byte what it would have written. Nothing told anyone the edit
was harmless, so the set stayed on its old engine.

## Fix

[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
refresh compares a drifted engine file or declared engine path with
upstream's copy, as the BestPractice clone already has it, before refusing.
An identical file is named and passed; a real edit is still refused. Hooks
and CI workflows keep their own review.

Until that reaches the set: an Update Vendors in it clears the refusal.
