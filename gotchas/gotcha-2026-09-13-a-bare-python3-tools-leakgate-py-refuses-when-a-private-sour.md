---
slug:            gotcha-2026-09-13-a-bare-python3-tools-leakgate-py-refuses-when-a-private-sour
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A bare `python3 tools/leak_gate.py` refuses when a private source RESOLVED and no blocklist is set — and allows, loudly, when the private sources could not be attached at all.

## Story

**A bare `python3 tools/leak_gate.py` refuses when a private source RESOLVED
and no blocklist is set — and allows, loudly, when the private sources could
not be attached at all.** The distinction is the whole rule and it was got
wrong once, in both directions, on 2026-09-08. First the gate reported PARTIAL
and **exit 0** for a session that could attach neither private source; it
pushed into a public repository with only the structural rules applied and
reported it afterwards. So the requirement was derived from `precedent.json`
DECLARING a private source. **That refused every session that could not attach
one** — a live, intermittent condition here — and within the hour it blocked a
real session out of pushing at all, whose commit then "dies with the
container": `repo-is-memory` losing outright, in exchange for no safety. **The
threat model was backwards.** Private vocabulary reaches a session by the
session READING the private sources' text. A session that could not attach
them never read a word and has nothing from them to leak; the one that DID
attach them is the one writing to a public tree with private text in context.
So **resolution, not declaration, requires the list**. Practically: if the
sources resolved, export `PRECEDENT_LEAK_BLOCKLIST` — you have the repository,
so you have the file. If they did not resolve, the push goes through and the
gate says out loud what it could not cover: a private term that reached the
session some other way, most plausibly the person's own messages. **Say that
in the reply.** A caller that only ever wants the structural half says so by
name with `--structural-only`; CI and `verify_harness.py` both pass it, and
both call themselves structural.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
