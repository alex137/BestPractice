---
slug:              todo-2026-10-06-remind-after-produce-the-stale-produce-fix
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         2026-10-06
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-06
closed:            null
---
## What

Morgan, 2026-10-06, about point 1 of that day's reply (*"Is it solved
going forward?"* -- a Debut that ran while a Produce pull request waited on
its GitHub test, so the pull request went stale and was refused): *"On #1
-- please remind me to do this after we are done with this produce (I want
to get it live)."*

The fix went in the same day as
[alex137/BestPractice#915](https://github.com/alex137/BestPractice/pull/915):
a Debut waits while a Produce pull request into main is open, and the merge
check tells a stale copy to make a fresh Produce rather than retarget.
Raise this once that Produce has landed on main, so he can go through
point 1 with it live.

## How It Closes

Raised with Morgan after the Produce that carries #915 is on main, and he
has said what he wants done with it.
