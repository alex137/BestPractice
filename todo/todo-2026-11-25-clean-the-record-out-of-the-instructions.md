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
- [x] The templates, which ship into other people's repositories. All 56 stamps are settled: 50 rewritten, and the ledger's 6 left as a dated record. The hook stub's comment changed in all 35 copies and three workflow templates changed, on Alex's "your picks." of 2026-11-27; each repository sees one approval prompt for them at its next update.
- [x] The rule text of the 7 practices. All 9 stamps are out of the rules. Where a person's words were only in the rule, they moved to that practice's Story word for word.
- [x] Messages tools print. The check reads them now: every string a script directly under `tools/` can print, and every reason in [reply_check.json](../reply_check.json). Eleven stamps came out of six tools, each kept as a comment beside its line, and all twenty reasons in `reply_check.json` were rewritten to say the rule, with each old text kept word for word in a `_story` key nothing prints. Strings that are the record on purpose (approval lines, a Story a tool writes) are marked as such in the code.
- [ ] Decide whether history that opens in lower case is covered: "retired 2026-09-21", "since 2026-09-28". The check matches a capitalised opener only, so these pass. Measured 2026-11-27 with the opener matched in either case: 43 in 17 files under `templates/`, 34 in 11 tools' printed strings, 1 in a practice's Rule. Some are content (a cutoff a check applies, a date GitHub changed something); most are a tool's or template's own history (needs: decision -- Alex or Morgan; cleaning the templates sends each consuming repository another approval prompt).
- [x] The header of the resident block, which showed a token count and a practice count to every session. It is `## Resident block` and nothing else. The figures are in the output of the tools that measure them ([tools/build_views.py](../tools/build_views.py)'s summary line, the resolver's and the materializer's), and a tool that needs them from a committed file calls `build_views.resident_block_measure`, which still reads a heading written before the change. A repository's own block loses its figures the next time it is regenerated.
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
- 2026-11-27: printed messages are done and checked. Left out on purpose, as the record: [tools/test_verdicts.json](../tools/test_verdicts.json) (each verdict carries its date and who gave it), the `approved_by` lines in `precedent.json` and [tools/session_load_budgets.json](../tools/session_load_budgets.json), and `_comment` keys everywhere. Tests under `tools/harness/` are not read; their fixtures plant stamps on purpose.
- 2026-11-27: the list in `precedent.json` is empty. What the check reads is clean: the instructions file, every rule text and every template. Still open above: messages tools print, the resident block's header, root documents, and whether a practice's Detail is covered.
