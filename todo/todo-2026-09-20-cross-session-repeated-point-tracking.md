---
slug:              todo-2026-09-20-cross-session-repeated-point-tracking
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-20
closed:            null
---
## What

- <a id="cross-session-repeated-point-tracking"></a>**Design a way to notice when Morgan has made the same point to a
  session multiple times, across sessions, and stop re-arguing it.** Raised
  2026-09-20, mid-conversation, as a maybe-bad-idea he explicitly did not
  ask to be built: he'd just spent real back-and-forth convincing a session
  a cost concern was real, and wants sessions to learn from that instead of
  re-litigating the same point next time.

  **What's already covered.** A single point, decided once inside one
  session, already gets marked so it doesn't get re-argued there —
  [decision-strength](../practices/decision-strength.md)'s `decided`/
  `assented` marking handles that.

  **What isn't.** Carrying "he's said this before" *across* sessions is a
  different, heavier mechanism: it needs somewhere durable to log that a
  point was made, and a judgment call about what counts as the same point
  restated versus a genuinely new one. A practice file's prose rule isn't
  enough on its own — this is closer to a registry
  ([registry-source-of-truth](../practices/registry-source-of-truth.md)'s
  shape) that something writes to and something else reads before
  re-arguing a position, plus the harder open question of matching "this
  sounds like that."

## How It Closes

Not yet designed. Closes once a session works out (a) where a
made-more-than-once point gets logged, (b) what makes a new instance count
as "the same point" rather than a new one, and (c) what a session does
differently once it recognizes a repeat — and Morgan signs off on the
design before anything gets built from it.

## Notes

2026-09-20: filed as an open idea only, per his own framing — not a build
request. He was explicit that raising it now was about focusing back on
the issue at hand (a real GitHub Actions cost concern) and having this
design conversation separately, later.
