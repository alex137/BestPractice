---
slug:              todo-2026-11-24-twelve-lessons-from-a-night-over-the-usage-limit
kind:              decision
domain:            practice
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Alex's yes or no, in the session that drafted them, on landing the drafted rules; his yes so far is relayed"
noted:             2026-11-24
closed:            null
---
## What

- [ ] **Twelve lessons from a night in which about fourteen worker sessions and a coordinator ran past a weekly usage limit, proposed for Precedent.** Sent 2026-11-24 by that project's coordinating session, with Alex's relayed words: "Yes let's update. But first do a review and see if you see improvements on your ideas before sending". Each was weighed against the rules already in force. Ten are drafted on the branch that carries this item, folded into existing practices where they fit; two are declined as already covered. (needs: decision -- Alex)

**Taken, and where each went.**

| Lesson | Where it is drafted |
|---|---|
| Count the never-counted items before a headline moves; the headline says how many it leaves out | [coordinating-sessions-through-models](../practices/coordinating-sessions-through-models.md), Detail |
| A figure that moves a headline is counted twice, independently | the same paragraph |
| A producer marks an output moving or settled; a consumer's build refuses unsettled or changed inputs; work is released in dependency order by one command | the same practice, Detail |
| Notes read each other's figures at build time; a cycle is a build failure | the same practice. It replaces a sentence that said a cycle is rerun until it settles, which this night showed to be wrong |
| Land per settled step; wake only the sessions concerned; the coordinator writes to the person only on a landing, a changed conclusion or a decision | the same practice, Detail |
| Every task carries a ceiling in time | the same paragraph |
| Run it before arguing; an estimate by ratio is a placeholder | new: [calculate-before-reasoning](../practices/calculate-before-reasoning.md), an addition to numbers-are-sourced |
| A pass mark says whether it was measured or assumed | [score-the-incumbent-first](../practices/score-the-incumbent-first.md), Detail |
| A setting the code does not carry out stops the run; one setting name, one meaning | new: [settings-are-carried-out](../practices/settings-are-carried-out.md), an addition to prediction-before-the-run |

**Declined, as already covered.**

- **"A coordinator does not rebuild a worker's note before that worker has its inputs."** The coordinating practice already says a session never regenerates another session's files, and [prediction-before-the-run](../practices/prediction-before-the-run.md) already puts the prediction before the result.
- **"A relay or bookkeeping session runs on a smaller model."** [session-spend-follows-the-task](../practices/session-spend-follows-the-task.md) says it. The lesson was that it was not applied, which a second copy of the rule would not change.

**None of these costs a line in the opening index.** The two new practices load with the rule each adds to, and the rest is detail inside practices already there. The universal set stays at 2,499 of its 2,500.

**The missing instrument, and a partial answer.** The project could not say how much of the overage these would have prevented, because a session cannot see what it has spent. A coordinator can see what each worker's turn cost, though: where a harness records a finished turn's cost and turn count, a session that started the worker can read it. The session that drafted this read exactly that for two small sessions it started on 2026-11-23. The drafted practice says to record it against each landing. A tool that does it is not built.

**The settled-and-moving marks and the release command are a project's own tools.** The practice states what they must do. Whether one of them belongs in the engine waits until a second project needs it.

**The cost of leaving it.** The next project with many sessions meets the same three costs: rework from headlines that move on uncounted figures, dependent work started on inputs still moving, and coordination chatter that nobody can measure.

## How It Closes

`status` becomes `done` when Alex has said yes or no; on a yes, when the drafted rules are on `main` and GitHub's test on `main` passes.
