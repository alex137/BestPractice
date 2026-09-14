---
slug:        reduction-pass
title:       "\"Reduction pass\" reduces what every session loads, and reports what moved"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Reduction pass\", or an always-loaded surface is near its ceiling"
gates:       []
index_clause: "\"Reduction pass\" -- work the menu in order, move never delete, report what moved"
checked_by:  null
defines:     ["Reduction pass"]
command:     {"Reduction pass": "Measure everything a session loads before it starts work, make room by moving things rather than deleting them, and show you exactly what moved and what it saved."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "Morgan, 2026-09-14 -- asked for the command in the thread that answered the AGENTS.md ceiling question: \"Do we have a command to do a 'reduction' pass listing what you did? Let's define that command if you think that's a good idea.\""
---
## Rule
When the person says **"Reduction pass"**, measure every always-loaded
surface, make room by **moving text rather than deleting it**, and end with a
report of **what moved, where it went, and what each move cost**.

**Work the menu in order. The cheap moves are first, and they are first
because they are provably lossless** — a session loses nothing, because the
text is still somewhere it already reads.

1. **Delete what is duplicated.** Text that already sits, in full, somewhere
   a session reaches on demand. Verify it word for word rather than assuming.
2. **Retire what cannot happen any more.** A trap that is closed, a rule
   about a mechanism that is gone. It moves to a linked archive **in full**,
   with the verdict that moved it.
3. **Split what is still live and still long.** The section becomes an
   **index** — one line per entry, and a link — and the bodies move to a
   linked file, word for word. Nothing is rewritten: the split changes the
   loading, not the text.
4. **Cap the generated half.** The loader's own blocks cannot be trimmed by
   hand, so they get their own declared budgets. The cost then lands on
   whoever adds a practice, at the moment they add one.
5. **Set the ceiling on purpose.** Compose it — the generated caps, plus a
   *declared* allowance for hand-written prose — rather than ratcheting it
   off whatever the file happened to measure.
6. **Move a whole surface out of the always-loaded set.** Last, and usually
   empty: most such surfaces are the only channel something has.

**Never raise a ceiling to make a red check green.** That is
[session-load-budget](session-load-budget.md)'s line and this command does
not soften it. Step 5 is a number decided on purpose, in a commit, with the
reason recorded — which is a different act from clearing a red.

**The report is not optional, and it is the half people skip.** Per surface:
tokens before, tokens after, and the ceiling. Per move: what moved, from
where to where, and whether anything was rewritten. Then **what was NOT done
and why** — the move you considered and rejected is the most useful line in
it, because the next pass will consider it again.

## Detail
**"Move, never delete" is the whole discipline.** The payload of a gotcha is
the story of what failed; the payload of an index row is the thing it points
at. A pass that chases the total deletes the entries that are working and
leaves a live section of unexplained rules behind. If a move would lose
text, it is not one of the six above.

**Measure with the tool, never by eye:**
`python3 tools/session_load_trend.py` reports headroom, the growth rate, and
— the number that decides which step applies — **how much of each surface is
generated**. A pass aimed at prose when the growth is generated is a pass
that cuts muscle and changes nothing.
`--since <ref>` produces the before/after ledger the report needs, measured
against the tree rather than typed from memory.

**The trap in step 3, learned the hard way:** a section may be required to
exist by a practice of its own. Precedent's quick index is
[quick-index](quick-index.md)'s, mechanically checked for at least five
rows. So the split kept the rows sessions reach for constantly *inline* and
moved the long tail — which satisfies the check and the practice's own
intent, where moving the whole table would have broken both. **Check what
requires the section before you move it.**

**The trap in step 4:** a practice whose `applies_to` is `["**"]` and which
declares no gate is reachable **only** through the occasion index — that
glob matches everything and therefore routes nothing. Dropping its
`occasion:` to fit under a cap un-routes the rule silently. Give it a real
glob or a gate first, or leave it alone.

**A pass that finds nothing is a finished pass.** Say so and stop. The menu
runs out, and a session that invents a seventh move to look thorough is
doing the damage this practice exists to prevent.

## Why
The ceiling check is binary: green one token under, red one token over. It
therefore reports the wall only once somebody has hit it, and the person who
hits it is whoever happened to be editing that day — not whoever caused the
growth.

Measured in Precedent's own repository over 2026-09-13 and 09-14:
`AGENTS.md` crossed its ceiling **four times in two days**, and **three
different sessions** paid a reduction pass mid-task for growth none of them
had added. Each pass was done well and none of them was written down as a
method, so each session rediscovered the menu from scratch and worked it in
whatever order occurred to it.

**Naming the pass turns a recurring tax into a thing somebody asks for.**
The person decides when it runs, the order is fixed so the lossless moves
happen before the judgment calls, and the report means the next pass starts
from what the last one already rejected.

## Story
**Coined by Morgan, 2026-09-14**, closing the thread that answered
[TODO.md's `agents-md-ceiling-policy` item](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/TODO.md#agents-md-ceiling-policy).
Handed a costed menu of five options for what to do when `AGENTS.md` meets
its ceiling, he chose three of them and then asked for this: *"And document
these options, it's a good list for reducing it in the future. Do we have a
command to do a 'reduction' pass listing what you did? Let's define that
command if you think that's a good idea."*

**The menu above is that list**, generalized off the options he was choosing
between. Steps 1–3 were already `session-load-budget`'s three moves; steps
4–6 are the ones the costing added, and step 4 is the one that mattered
there — the occasion index had grown every day for a fortnight, to 29% of
the file, and no reduction pass was allowed to touch a token of it.

**Placed at universal from the start**, on the same reasoning as
[go-merge](go-merge.md) and [park-it](park-it.md): a phrase that lives in one
person's private set is a phrase a session that has not attached that set
cannot read, and it will go and ask what it means — the exact interruption
the phrase exists to prevent. Any repository with an always-loaded
instructions file has this problem, which is what makes it universal rather
than Precedent's own.

## Install
**Nothing mechanically checks that a pass was performed or that its report is
honest**, and that is a considered "no" rather than an unexamined one. The
report describes moves across files and asserts that nothing was rewritten;
a script can compare two trees, but whether a section still says what it
meant is a reading. The same limit
[go-merge](go-merge.md) and [park-it](park-it.md) record.

**What IS mechanical, and already runs:**
[session-load-budget](session-load-budget.md)'s own check fails any surface
over its declared ceiling or missing from the registry, so a pass that did
not do enough is caught by the thing that prompted it.
`tools/session_load_trend.py --since <ref>` computes the before/after ledger,
so the report's figures are measured rather than asserted — the half of the
report most likely to drift is the half a tool now produces.

An adopting repository needs no setup: the phrase reaches every session
through the generated occasion index, and the tool ships with the engine.
