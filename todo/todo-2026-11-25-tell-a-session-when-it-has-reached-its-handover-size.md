---
slug:              todo-2026-11-25-tell-a-session-when-it-has-reached-its-handover-size
kind:              analysis
domain:            engine
severity:          low
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "evidence -- a second project trying the handover rule by hand"
batch:             null
decision:          null
decision_strength: null
waiting_on:        "a second project using the rule by hand, and saying what size it declared"
noted:             2026-11-25
closed:            null
---
## What

- [ ] **Have the tooling tell a session when it has passed the size its project declared for handing over.** [coordinating-sessions-through-models](../practices/coordinating-sessions-through-models.md) now says a long-lived session hands over to a successor at a declared size. Today the session has to notice its own size. (needs: evidence -- a second project trying the rule by hand)

**What exists to build on.** The end-of-reply check already reads a session's context size from its record, to decide when the compaction offer in [the-boildown](../practices/the-boildown.md) is owed. The same reading could say a handover is owed. With that, the compaction offer should become an offer to hand over wherever a project declares a size.

**Why it waits.** One project has used the rule, with one size. When the rule was put to Alex on 2026-11-25, the proposal was to build the prompt only after a second project has tried the rule by hand, and he said yes to the rule on those terms, so the setting's name, its place and its default come from two uses and not one.

**The cost of leaving it.** A session that does not notice its size runs on until someone else does.

## How It Closes

`status` becomes `done` when the prompt is on `main` with a test, or when Alex or Morgan says it is not wanted.

## Notes

- 2026-11-25: filed when the rule landed.
