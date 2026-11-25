---
slug:              todo-2026-11-25-clean-the-record-out-of-the-instructions
kind:              analysis
domain:            practice
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "yes to the cleanup, rule and check first (Alex, 2026-11-25: \"I trust your judgement on both\")"
decision_strength: assented
waiting_on:        null
noted:             2026-11-25
closed:            null
---
## What

- [ ] **Clean names, dates and history out of everything a session is told to follow or that ships to another repository.** [record-not-instruction](../practices/record-not-instruction.md) is the rule, and the list of what is left is `record_in_instructions_before_the_rule` in [precedent.json](../precedent.json), which the check holds each file to. Alex asked for it on 2026-11-25 after reading the instructions file.

**What the check counted the day it landed:** 68 in 43 files: 3 in the instructions file, 9 in the rule text of 7 practices, 56 in 35 files under `templates/`.

**The order, agreed with Alex.**

- [ ] The instructions file, [AGENTS.md](../AGENTS.md). The rewrite is proposed to Alex before it replaces the current one (needs: decision -- Alex, on the proposed text).
- [ ] The templates, which ship into other people's repositories.
- [ ] The rule text of the 7 practices. Each stamp moves to that practice's Story or approval line, where it is not already there.
- [ ] Messages tools print. The check does not read these; they are found by searching what each tool writes to a session (needs: this session, after the three above).
- [ ] The header of the resident block, which shows a token count and a practice count to every session. The figure moves to the output of the check that measures it.
- [ ] Decide whether a practice's `## Detail` is covered (needs: decision -- Alex or Morgan).
- [ ] Have each practice set that takes the engine declare its own list, so the check holds it too (needs: this session or that set's own, at its next engine update).

**Not checked yet and probably needing the same:** root documents such as the README, where 5 of 11 files name a person, and `documentation/`.

**The cost of leaving it.** A repository that installs Precedent receives templates and rules that name two people it has never heard of, and reads the rules as theirs.

## How It Closes

`status` becomes `done` when the list in `precedent.json` is empty, or when Alex or Morgan says to stop.

## Notes

- 2026-11-25: the rule and its check landed first. The check refuses any rise from the day's counts.
