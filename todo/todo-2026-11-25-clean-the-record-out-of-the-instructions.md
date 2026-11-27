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

- [x] The instructions file, [AGENTS.md](../AGENTS.md). Rewritten on Alex's "Yes." of 2026-11-25, as proposed in [spec/AGENTS_REWRITE_PROPOSAL.md](../spec/AGENTS_REWRITE_PROPOSAL.md): 30,096 characters to about 24,050, and its count in `precedent.json` is gone.
- [ ] The templates, which ship into other people's repositories. 23 of the 56 stamps are out, from 13 files. The 33 left are of three kinds, each waiting on a decision (needs: decision -- Alex or Morgan):
  - **19 hook stubs**, one stamp each. Every stub is the same file, installed into each repository's `.claude/hooks/` and written never to change. Editing its comment changes a file under `.claude/` in every repository at its next update, which is the prompt the stub exists to avoid.
  - **8 in three workflow templates.** A workflow file's approval is pinned to its content, so a changed comment asks every repository's owner to approve the file again.
  - **6 in [templates/harness/LEDGER.md](../templates/harness/LEDGER.md)**, a dated ledger: settled 2026-11-27 on Alex's "your picks." The file declares itself a dated record and the check leaves such a file alone.
- [x] The rule text of the 7 practices. All 9 stamps are out of the rules. Where a person's words were only in the rule, they moved to that practice's Story word for word.
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
- 2026-11-25: the instructions file is done. One heading kept its old words, "Build-environment gotchas", because two tools find the section by them.
- 2026-11-27: templates, first pass. A starter practice under `templates/` is now read as a practice, its Rule only.
- 2026-11-27: the rule texts are done. 33 stamps remain, all under `templates/`, all waiting on the decisions listed above.
- 2026-11-27: Alex agreed to all three proposals put to him that day ("your picks."): the ledger is exempt as a dated record; the hook stub and the workflow templates are to be cleaned in one update; a session archives the sessions it created.
