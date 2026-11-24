---
slug:              todo-2026-11-23-the-text-printed-every-turn-outweighs-the-opening
kind:              analysis
domain:            engine
severity:          medium
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Alex or Morgan saying to shorten it; what a session is shown each turn is theirs to cut, and the session that found this was asked only to measure"
noted:             2026-11-23
closed:            null
---
## What

- [ ] **The text this repository prints at the start of every turn costs more than everything a session loads at its start.** Measured on one turn of one session, 2026-11-22: 2,177 tokens (rough count), against 6,712 for the whole opening. Three turns outweigh the opening, and the session-load budget counts only the opening. Found while researching [shared openings](../spec/SHARED_OPENINGS.md). (needs: decision -- Alex or Morgan)

**What it is.** The reply-moment rules: a list of every practice that fires when a reply is written, and the hard requirements for the closing section, printed in full each turn.

**What to look at.** Whether the full text is needed after its first printing in a session, or a short pointer would do on later turns, the way the missing-source reminder already shortens itself. And whether the load budget should count a per-turn figure beside the opening's.

**The cost of leaving it.** Every turn of every session in every repository that uses Precedent carries it. Unlike the opening, it is new text each time, so each turn pays to write it before any later turn reads it cheaply.

## How It Closes

`status` becomes `done` when the per-turn text has been measured over a whole ordinary session, and Alex or Morgan has said whether to shorten it; on a yes, when the shorter form is on `main`.
