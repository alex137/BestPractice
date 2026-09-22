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
decision:          "Neither of the two fixes below. The offending row is not a
  vocabulary command in the first place and loses its `command:` field at the
  source, in precedent-individual. What stays open here is only the guard, so
  the next private command cannot recreate this."
decision_strength: decided
waiting_on:        null
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

## What Morgan Decided, 2026-09-21

**Neither option below.** His reading, in his own words: *"that's not a vocab
word, it is just a practice, so it shouldn't have it in the vocab lists even
privately."* The `so-what-test` practice fires automatically on every reply --
it is not a phrase he says to trigger something -- so the `command:` field on
it is simply wrong, and the emitter was reporting it correctly. Removing that
field at the source drops the row, the block matches again, and no filter is
needed. **strength: decided.**

**That fixes the instance and not the class.** The next private practice that
declares a `command:` recreates this exactly, and the person who meets it will
be a session staring at a red gate whose documented remedy is `--write`. What
remains open here is only the guard: either the emit path refuses to render a
non-public source into a tracked public document, or it says loudly which
source each row came from so the mistake is visible before somebody writes it.

## Why the Two Options Below Were Not Taken

They were the session's framing, and both accepted the premise that a private
command legitimately belongs in that list. They are kept here because the
guard still has to choose between refusing and disclosing:

1. **Filter the `--emit` path to publicly-shippable sources**, the way
   [tools/build_views.py](../tools/build_views.py) already filters the loader
   block for the same reason, in the same repository. The interactive listing
   keeps every level. Cost: the table in a public guide is then *not* the list
   of commands its reader actually has, and nothing on the page says so.
2. **Say on the page that the table is the universal set**, and have the
   emitter fail loudly rather than silently include a private row.

**The drift is left unwritten deliberately** — the deep check reported one
violation until the source fix landed, which was the honest state.

## Part 1 Is Done, Measured 2026-09-21

The source fix landed on `main` in the individual set, as commit `09190a7`,
*"Drop so-what-test's `command:` field -- it is a practice, not vocabulary"*
(read off that clone's `origin/main` here; the repository itself is not
reachable from a session rooted in BestPractice, so the commit subject is the
whole of what can be cited): the practice's `command:` field is `null`,
`defines` was deliberately kept (a separate list — it feeds the glossary, not
the vocabulary), and nothing else about the practice moved.

**Verified here rather than taken on report.** With the individual source
pointed at its `origin/main`, in this checkout:
`python3 tools/precedent_vocabulary.py` emits no row from a non-public set, all
four `doc_sync` blocks read `OK` — `documentation/DAILY_HABITS.md [vocabulary]`
included — and [precedent_check.py](../tools/precedent_check.py) returns **0 violated**. Nothing in this
repository needed changing; the block was already correct and was waiting for
the emitter to agree.

**A trap surfaced on the way**, worth knowing before anyone works part 2:
editing a practice inside its own source repo does not change what the engine
tools report, because the resolved copy silently overwrites the local one.
[The gotcha](../gotchas/gotcha-2026-09-21-editing-a-practice-in-its-own-source-repo-does-not-change-the-tools-answer.md)
has the mechanism and the non-destructive way to verify.

## Closing Condition

Both halves:

1. `python3 tools/precedent_vocabulary.py` no longer lists a row sourced from a
   non-public set, and `python3 tools/doc_sync.py` returns clean on a session
   where the individual source has resolved.
2. Something prevents the recurrence — the emit path refuses a non-public
   source, or names the source per row — so the next `command:` in a private
   practice cannot be written into
   [documentation/DAILY_HABITS.md](../documentation/DAILY_HABITS.md) by a
   session clearing a red gate.

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

