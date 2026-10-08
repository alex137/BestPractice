---
slug:              todo-2026-10-08-tell-morgan-what-others-did
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"This new practice you define is great, approved\" -- a daily summary of what others did, opening the first session after 07:00 Buenos Aires time"
decision_strength: decided
waiting_on:        "Morgan: where the 'last told' mark is kept"
noted:             2026-10-08
closed:            null
---
## What

Morgan learned about changes Alex made to Precedent only after something
confusing happened. [WHATS_NEW.md](../WHATS_NEW.md) does not cover this: it
picks the three or four most important things done by anyone each day, and
since most of the work is Morgan's, it rarely shows him what someone else
did.

## Proposed

- **When:** at session start in this repository, when the person was last
  told before 07:00 Buenos Aires time today and it is now after 07:00. Before
  07:00, nothing.
- **What:** every commit that reached `main`, `staging` or `pre-staging`
  since the person was last told, written by anyone else. Someone else
  merging the person's own pull request is not their work.
- **How it reads:** the first reply opens with a short What's New-style
  summary (about three bullets, each opening in bold, any rule change always
  named), then answers the question. With nothing from anyone else, one
  line saying so.
- **Then** the person is marked as told.
- **Built by extending**
  [tools/precedent_beta_watermark_check.py](../tools/precedent_beta_watermark_check.py),
  which already tells a person once when someone else pushed, keyed per
  person, not by writing a second tool.
- **The practice belongs in the ladder set**, not the universal one, so
  it reaches only people who bring that set (Morgan, 2026-10-08).
- **Commits signed only "Claude"** are attributed by their `Claude-Session:`
  link: a session the person's account can open is theirs; one it cannot
  is someone else's, confirmed by who merged its pull request. Measured
  2026-10-08: `session_01B8YjZLeCQvJ6KZJbHmLovi` (2026-09-23) opens from
  Morgan's account; `session_01FsMPKqhoWLbSZ7hByp7MFF` (2026-10-02) and
  `session_01S2LLcA8ujJwyTYm5S19aKh` (2026-09-28 to 09-30) do not, and
  Alex merged both of their pull requests (#824, #762). A hook cannot open
  a session, so the hook marks these commits and the session checks the
  link before it writes the summary.

## How It Closes

Built and running: the first session of a day after 07:00 Buenos Aires
time opens with what others did since the last summary, and a second
session that day does not repeat it.

## Notes

**Decided 2026-10-08, Morgan: "This new practice you define is great,
approved" (strength: decided).**

Open: where the "last told" mark is kept. A branch kept only for it was
rejected ("weird and confusing and could be deleted"). Proposed instead:
the per-person file the beta-branch check already keeps,
[tools/beta_branch_watermark.json](../tools/beta_branch_watermark.json),
which Morgan agreed on 2026-09-22 may sit in this public repository.
