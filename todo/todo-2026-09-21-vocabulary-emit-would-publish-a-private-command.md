---
slug:              todo-2026-09-21-vocabulary-emit-would-publish-a-private-command
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan -- deferred 2026-09-21: 'hold off for now, we'll deal with that later'. Disposition moved ask -> wait on that, so no session chases him for the choice; the three fixes below are ready when he comes back to it"
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

## A second session reached the same finding independently, 2026-09-21

A session landing the very-deep-check deepening work ran the deep check
before pushing, hit the same red gate, and filed it separately before the
two branches met. That item is folded in here rather than kept beside this
one. It adds two things:

**The measurement.** Same tree, same commit: the emitter produces **21 rows
with the individual source resolved and 20 without**. The committed document
has the 20, so the gate is red in every session that resolves a private
source carrying a command and green in CI — the document cannot satisfy
both, which is the sharper version of "CI is green on it" above.

**A third fix, beside the two already named.** Drop the pair from
[tools/doc_sync.py](../tools/doc_sync.py)'s `PAIRS` entirely and let the
page carry a pointer to `python3 tools/precedent_vocabulary.py` for the live
answer. That is the same reasoning that already keeps the branch report out
of `PAIRS` — its output depends on the session it runs in rather than on the
tracked tree, which is precisely this block's problem. Cost: the page stops
carrying a table at all.

Two sessions finding this the same day, from opposite directions, is the
argument for it being decided rather than left.

**Deferred by Morgan, 2026-09-21** — *"hold off for now, we'll deal with
that later."* Disposition moved from `ask` to `wait` on the strength of that
sentence, so nothing chases him. **Not parked**: he said later, which is a
different thing, and the three fixes above are waiting rather than dropped.
Nothing is published in the meantime — the drift is left unwritten, which is
the safe side of it.

