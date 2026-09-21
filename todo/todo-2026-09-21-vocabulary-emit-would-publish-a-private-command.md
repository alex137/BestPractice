---
slug:              todo-2026-09-21-vocabulary-emit-would-publish-a-private-command
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan -- which of the two fixes below he wants; both change what an adopter reads"
noted:             2026-09-21
closed:            null
---
## What

**`python3 tools/doc_sync.py --write` would publish a private practice's
command into a public, tracked file**, and the drift gate is currently asking
for exactly that.

[documentation/DAILY_HABITS.md](../documentation/DAILY_HABITS.md) carries a
`<!--gen:vocabulary-->` block fed by
[tools/precedent_vocabulary.py](../tools/precedent_vocabulary.py) `--emit
vocabulary`. That script reads **every** resolved source by design — universal,
shared, individual — because the spoken `Vocabulary` command has to list every
phrase actually in force. The document it feeds is an adopter-facing guide in a
repository that declares `visibility: public`.

So on any session where the individual source resolves, the emitter produces a
row for `So what?` ([so-what-test], individual), the gate reports drift, and
the documented remedy — `doc_sync.py --write` — writes that row into a public
file. The 20 rows committed today are all universal; nothing has leaked yet.

**CI is green on it, which is why nobody has caught it.** The workflow runs
without the credential that clones the private sources, so the emitter there
sees only the universal set and the block matches. The drift — and the offer to
write it — appears only in a working session, which is the one place a person
is likely to run `--write` to clear a red gate.

**The leak gate does not catch it.** [tools/leak_gate.py](../tools/leak_gate.py) matches blocklist patterns
against text, and a command name and its gloss are not on any blocklist — the
problem is not the words, it is the level the words came from.

## Why It Is Filed Rather Than Done

Two fixes exist and they give an adopter different documents, so the choice is
not the session's:

1. **Filter the `--emit` path to publicly-shippable sources**, the way
   [tools/build_views.py](../tools/build_views.py) already filters the loader
   block for the same reason, in the same repository. The interactive listing
   keeps every level. Cost: the table in a public guide is then *not* the list
   of commands its reader actually has, and nothing on the page says so.
2. **Say on the page that the table is the universal set**, and have the
   emitter fail loudly rather than silently include a private row.

The session that found this was landing unrelated branch-deletion practices
and had no mandate to pick. **The drift is left unwritten deliberately** — the
deep check reports one violation until this is decided, which is the honest
state.

## Closing Condition

`python3 tools/doc_sync.py` returns clean on a session where the individual
source has resolved, and
[documentation/DAILY_HABITS.md](../documentation/DAILY_HABITS.md) holds no row
sourced from a non-public practice set.
