---
slug:              todo-2026-09-16-review-portability-plan
kind:              manual
domain:            content
severity:          notable
status:            open
disposition:       ask
remind_on:         "2026-09-19"
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-09-16
closed:            null
---
## What

Review [spec/PROVIDER_PORTABILITY_PLAN.md](../spec/PROVIDER_PORTABILITY_PLAN.md)
closely — the dependency inventory of what in this repo is coupled to
Claude Code specifically, and the phased plan for closing the gap so
ChatGPT/Codex, Grok and other providers get the same level of automation.
Two of its five phases have already been acted on in the same conversation
that produced it: [practices/session-text.md](../practices/session-text.md)
no longer creates or wakes a session (always hands over paste text now),
and [practices/todo-reminder.md](../practices/todo-reminder.md) was updated
to the current per-item format with a standing prohibition on
scheduled-trigger reminders. The document's own Phase 4 note records what
that traded away. Phases 1, 2, 3 and 5, and the still-open
[archive-command.md](../practices/archive-command.md) dependency, have not
been started.

## How It Closes

`status` becomes `done` when Morgan has read the plan and either approves
it to continue as written, asks for changes, or decides not to pursue the
remaining phases.

## Notes
