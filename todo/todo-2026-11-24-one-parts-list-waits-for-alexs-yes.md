---
slug:              todo-2026-11-24-one-parts-list-waits-for-alexs-yes
kind:              decision
domain:            practice
severity:          medium
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "yes (Alex, 2026-11-24: \"Yes and granted\", to the drafted rule as written)"
decision_strength: assented
waiting_on:        null
noted:             2026-11-24
closed:            2026-11-24
---
## What

- [x] **A new practice, [one-parts-list](../practices/one-parts-list.md), is drafted on the branch `claude/parts-list-practice` and waits for Alex's yes** (needs: decision -- Alex). Proposed 2026-11-24 by the coordinating session of a dependent project, which relayed Alex asking "Why are we only now discovering all the missing parts? Do we need a practice for this?". That is a question, so the draft is held and not landed.

**What it says.** Anything built or tested in pieces keeps one parts list in its registry, each part marked real, stand-in or missing, with the basis it was built on. A run that leaves a part out updates the list in the same commit. "What is left before X?" is answered by reading the list.

**Where it sits.** It is an addition to [prediction-before-the-run](../practices/prediction-before-the-run.md), so it loads with that rule and costs no line of its own in the opening index. The rules it was weighed against cover neighbouring ground and not this: [registry-source-of-truth](../practices/registry-source-of-truth.md) says status has one home but not that a run's caveats are status; [name-the-target-case](../practices/name-the-target-case.md) labels a stand-in case, not a stand-in part; [test-data-is-a-choice](../practices/test-data-is-a-choice.md) names the data behind one result, not the basis under each part.

**One change from what was proposed, for Alex to rule on.** The proposal had the build refuse any joined run while a part is a stand-in, missing or on another basis. The draft lets such a run happen as a check of how the parts fit, prints the list's state with it, and refuses to report its result as the whole thing's figure. A flat refusal is right for the project it came from and wrong for work where joining early with stubs is how interface faults are found. If Alex wants the flat refusal, item 3 of the Rule is the line to change.

**The cost of leaving it.** The next project built in pieces finds its gaps the same way: late, by asking.

## How It Closes

`status` becomes `done` when Alex has said yes or no; on a yes, when the practice is on the landing branch with his words in its `approved_by:`.

## Notes

- 2026-11-24: drafted; no pull request opened.
- 2026-11-24: Alex said yes, to the rule as drafted. It lands with the pull request that carries this line.
