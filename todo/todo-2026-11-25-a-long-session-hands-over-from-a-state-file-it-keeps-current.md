---
slug:              todo-2026-11-25-a-long-session-hands-over-from-a-state-file-it-keeps-current
kind:              decision
domain:            practice
severity:          medium
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "yes (Alex, 2026-11-25: \"yes ot both\", to the rule with the size declared per project; the size prompt waits for a second project)"
decision_strength: assented
waiting_on:        null
noted:             2026-11-25
closed:            2026-11-25
---
## What

- [x] **Should every long-lived session keep a short state file current, and hand over to a fresh session at a set size instead of compacting?** Sent 2026-11-25 by a project's coordinating session, which relayed Alex asking: "Should we or do we have a BestPractice function that has each thread periodically save a short bit of what it is currently doing so it can be restarted whenever a coordinator thinks it is running too long? Or perhaps it can restart itself when it recognizes it has run too long? Maybe as it sees its context getting big, it does a restart? Is this better than context compression?" Nothing is drafted into a practice yet. (needs: decision -- Alex)

**The short answer to his question.** Part of it exists. [coordinating-sessions-through-models](../practices/coordinating-sessions-through-models.md) already says a long-lived worker is replaced by a fresh session at the end of a unit, after committing a short handoff. What does not exist: the file being kept current all along, a size at which a session retires itself, and anything that tells a session it has reached that size.

**What that project measured, by hand, in a day.** The figures are that session's, not re-measured here.

- Fresh sessions did a unit of work for 2 to 5 dollars; old ones cost 8 to 22 dollars for one turn after sitting idle.
- Three coordinators in a row were replaced at about 400,000 tokens from a handoff file, each cleanly.
- Automatic compaction on those sessions was set near 784,000 tokens, well past the point where a restart was cheaper.
- The handoff files were written on request, and sometimes by a third session from notes, because waking the old session cost more than writing the file.

**The rule proposed.**

1. Every long-lived session keeps one short state file in the repository: what it owns, how to build and check it, what is in flight with its prediction, traps met, what waits on whom. It is updated and pushed at the end of every unit, so a successor can start at any moment without asking the old session anything.
2. A session watches its own context. At a set size it finishes its unit, brings the file current, and tells its tasker to start a successor, or starts one itself where it has the tool.
3. A tasker may retire any session at any time on the strength of that file.
4. Restarting from the file is preferred to compaction. If a successor cannot work from the file, the file was wrong.

**How it weighs against the rules in force.** It extends one sentence of the coordinating practice and takes nothing back. [repo-is-memory](../practices/repo-is-memory.md) already requires that nothing live only in a thread; the state file is how that gets tested. Two things need care. The size is a number nobody has decided for anyone but that project, so it belongs in a project's declared settings and not in the rule ([constants-are-risk-inputs](../practices/constants-are-risk-inputs.md)). And [the-boildown](../practices/the-boildown.md) today offers compaction when context has grown by a set amount; with this rule, that offer should become an offer to hand over.

**What could be built.** The end-of-reply check already reads a session's context size from its record, to decide when the compaction offer is owed. The same reading could tell a session it has passed its declared size and owes a handover. No session can restart itself in place; it can start a successor only where it has a tool for creating sessions.

**This session's pick.** Yes to all four as a few sentences added to the coordinating practice, with the size declared per project. Build the size prompt after the rule has been tried by hand in a second project.

**The cost of leaving it.** Long sessions keep paying for their own history on every call, and handoff files keep being written late, by whoever is cheapest to wake.

## How It Closes

`status` becomes `done` when Alex has said yes or no; on a yes, when the rule is on `main` with his words in its `approved_by:`, and the size prompt is either built or filed as its own item.

## Notes

- 2026-11-25: recorded from the relayed message.
- 2026-11-25: Alex said yes. The rule is in [coordinating-sessions-through-models](../practices/coordinating-sessions-through-models.md), Detail, and lands with the pull request that carries this line. The size prompt is filed as [its own item](todo-2026-11-25-tell-a-session-when-it-has-reached-its-handover-size.md).
