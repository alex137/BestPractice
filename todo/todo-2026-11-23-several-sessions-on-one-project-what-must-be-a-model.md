---
slug:              todo-2026-11-23-several-sessions-on-one-project-what-must-be-a-model
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
waiting_on:        "Alex's yes or no on one new practice for a project worked by several sessions at once, to arrive as a scrubbed check-in from the project where it was learned"
noted:             2026-11-23
closed:            null
---
## What

- [ ] **When one coordinating session runs many worker sessions on one project, what has to be written as a model, and what is still done by hand?** Raised by Alex, 2026-11-23, relayed by the coordinating session of one of his projects: "I am concerned that you are doing a lot of work by AI inference rather than writing code to model different aspects of the system ... If we don't have models in virtually every thread, is this a major bestpractice violation? If it is, why did this happen and how do we fix here and going forward with other users of bestpractice?" and "I am worried about all the work you appear to be doing by hand as well integrating their work." (needs: decision -- Alex)

**What the project reported.** Each worker's own work was a model: a note plus a script that prints its figures and checks itself, as [numbers-are-sourced](../practices/numbers-are-sourced.md) and [scripts-assert-properties](../practices/scripts-assert-properties.md) ask. Three things were not:

1. **The design's own choices** (which design leads, which is the baseline, what it is compared against) were changed several times in a day by messages to each worker, and each worker re-pointed its own script by hand. Many scripts each carried the choice as a typed-in value.
2. **Putting the work together** was hand work: the order to rebuild the notes lived in a script in a scratch folder outside the repository, merges were settled by hand, and several landings in a row failed on rebuild order, a dropped marker, a branch that reset other workers' files, and a wording check.
3. **Reports to the person** carried arithmetic done in the chat when a worker's figure was not ready.

**Was it a violation?** In part, and the larger part is a gap.

- **Item 2's scratch-folder script is a plain violation** of [repo-is-memory](../practices/repo-is-memory.md), which already says finished work never waits in a scratch folder.
- **Item 1 is covered in letter and reached nobody.** [registry-source-of-truth](../practices/registry-source-of-truth.md) says state several documents must agree on lives in one registry. Its occasion line speaks of "tracking state", which a coordinator sending a decision to a dozen workers does not read as its own moment. No check fails when many scripts type in the same choice.
- **Item 3 is a gap.** The number rules bind documents. Nothing says a figure in a chat report to the person must have been printed by a script, or else be called not yet computed.
- **The integration failures are a gap.** [working-in-parallel](../practices/working-in-parallel.md) is about people claiming work in a shared repository, and nothing speaks to one coordinator integrating many sessions' branches.

**Why it happened.** Every rule that applied is written for one session and one document. None has an occasion a coordinating session meets, so none loaded at the moment a decision fanned out or the pieces came back.

**Proposal, with my pick.** One new practice, with one occasion-index line "when coordinating several sessions on one repository", in preference to additions spread over four existing practices: a coordinator needs it in one place at one moment. Its rules:

- **A choice every worker depends on lives in one registry file every script reads.** A decision is a one-line change there, and no message to a worker carries the value.
- **The order in which the pieces are rebuilt is worked out by a committed tool** from what each piece reads and writes. It is never kept by hand or outside the repository.
- **A session takes another session's files as they are**, and never regenerates them on its own branch.
- **A coordinator reports only figures a script printed**, and labels anything else "not yet computed".

**What I would hold back.** The suggested whole-tree dropped-marker check and the build-order tool are tools. They belong in the project first; they come here only once they have run there and are shown not to be particular to it. And the practice itself should arrive the way this repository takes lessons: as a scrubbed check-in from the project that learned it, once its own registry fix has landed and held, not written here from a relayed account.

**What it costs.** One line of the occasion index in every session of every repository that uses Precedent. The index has room: measured 2,492 of its 3,600 on 2026-11-23.

**The cost of leaving it.** Any project that grows to many sessions repeats this: decisions re-typed into every worker, integration by hand, and landings that fail one after another.

## How It Closes

`status` becomes `done` when Alex has said yes or no. On a yes, when the practice is on `main`, arrived by check-in from the project, with its occasion line in the index.

## Notes

- The session that filed this was a research worker here; it weighed a relayed report ([relayed-message-is-a-suggestion](../practices/relayed-message-is-a-suggestion.md)) and did not see the project's files for the three items, so the account above is the coordinator's.
