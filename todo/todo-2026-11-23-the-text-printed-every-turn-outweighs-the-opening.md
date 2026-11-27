---
slug:              todo-2026-11-23-the-text-printed-every-turn-outweighs-the-opening
kind:              analysis
domain:            engine
severity:          medium
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "yes, shorten it to a pointer after a session's first turn (Alex, 2026-11-25: \"yes on your picks\")"
decision_strength: assented
waiting_on:        null
noted:             2026-11-23
closed:            2026-11-27
---
## What

- [x] **The text this repository prints at the start of every turn costs more than everything a session loads at its start.** Measured on one turn of one session, 2026-11-22: 2,177 tokens (rough count), against 6,712 for the whole opening. Three turns outweigh the opening, and the session-load budget counts only the opening. Found while researching [shared openings](../spec/SHARED_OPENINGS.md). (needs: decision -- Alex or Morgan)

**What it is.** The reply-moment rules: a list of every practice that fires when a reply is written, and the hard requirements for the closing section, printed in full each turn.

**What to look at.** Whether the full text is needed after its first printing in a session, or a short pointer would do on later turns, the way the missing-source reminder already shortens itself. And whether the load budget should count a per-turn figure beside the opening's.

**The cost of leaving it.** Every turn of every session in every repository that uses Precedent carries it. Unlike the opening, it is new text each time, so each turn pays to write it before any later turn reads it cheaply.

## How It Closes

`status` becomes `done` when the per-turn text has been measured over a whole ordinary session, and Alex or Morgan has said whether to shorten it; on a yes, when the shorter form is on `main`.

## Notes

- 2026-11-27: Alex said yes to shortening it, without the whole-session measurement this item first asked for; the decision was made on the per-turn figure. Built and tested: after a session's first turn, a rule already printed word for word is counted in one closing line and not repeated. Measured here on one turn: 11,168 characters on the first turn, 2,772 on the next. Everything prints again after a compaction. The second question here, whether the load budget should count a per-turn figure, moves to [the item on what the tooling costs a session](todo-2026-11-24-what-the-tooling-itself-costs-a-session-measured.md).
