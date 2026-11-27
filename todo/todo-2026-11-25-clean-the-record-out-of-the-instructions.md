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
- [x] History that opens in lower case is covered: "retired 2026-09-21", "since 2026-09-28". Alex, 2026-11-27: "yes for both" (decided), to this and to the Detail question below, with the pick that went with it: tool messages and the one rule now, the templates in one batch. The check sees these openers anywhere in a sentence. It passes over a lower-case "as of" a date, which is how an outside-world fact carries its date, and "before" a date, which is usually a cutoff. Thirty came out of 12 tools' printed strings and one out of a practice's Rule.
- [ ] Clean the lower-case history out of the templates: 37 in the files `precedent.json` lists under `templates/` (needs: one update that ships them together, so each consuming repository is asked to approve once).
- [x] The lower-case history is out of the root documents and `documentation/`: fifty places. The commit that removed them lists each date and what it was attached to.
- [x] The header of the resident block, which showed a token count and a practice count to every session. It is `## Resident block` and nothing else. The figures are in the output of the tools that measure them ([tools/build_views.py](../tools/build_views.py)'s summary line, the resolver's and the materializer's), and a tool that needs them from a committed file calls `build_views.resident_block_measure`, which still reads a heading written before the change. A repository's own block loses its figures the next time it is regenerated.
- [x] A practice's `## Detail` is covered (Alex, 2026-11-27: "yes for both", decided), and the check reads it. 294 pieces of the record left the Detail of 49 practices, counted with lower-case history included; each is in that practice's Story, quotations word for word. About twenty names with no date beside them, which the check cannot see, went the same way.
- [ ] Have each practice set that takes the engine declare its own list, so the check holds it too (needs: this session or that set's own, at its next engine update).

- [x] Root documents and `documentation/`. Seventeen stamps came out of [INSTALL.md](../INSTALL.md), [SETUP.md](../SETUP.md) and five pages under `documentation/`, and the index row that named a person says the role. The check holds every Markdown document at the root and under `documentation/` to none. Left as they are: [MAP.md](../MAP.md)'s table of retired practices, which is generated from each one's withdrawal reason, and [WHATS_NEW.md](../WHATS_NEW.md), a dated log.

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
- 2026-11-27: root documents. The three quotations that left them, kept here: on a first install going straight to `main`, Morgan, 2026-10-08, "Why not install it straight to main?" (decided); on the leak gate running locally, Morgan, 2026-10-10, "the check must be local to avoid lots of github minutes billing issues"; on the loader install being the default, Morgan, 2026-09-14, on the very deep check's recommendation (assented). The per-person hook step in the cloud setup page was judged not worth asking of everyone by Alex, 2026-10-20.
- 2026-11-27: the list in `precedent.json` is empty.
- 2026-11-27, later: the list holds the templates' lower-case history again, 37 places, until one update ships them together.
- 2026-11-27, later still: dated asides. Alex: "Dated asides seem like they belong in document records and not in documents as per the practice we already have for this." (decided). About 130 dates standing on their own left 40 practices' Rules and Details for their Stories, and about 75 left the root documents and `documentation/`, each aside either folded into a plain present-tense note or removed; the commit lists the documents' dates. The check refuses a bare date in those places and passes the forms that say what the date is. Not read by it, and not cleaned: undated history ("this once shipped ..."), the templates, and what tools print. [practice-standing](../practices/practice-standing.md)'s Rule names the two approvers of the universal set on purpose and was left alone (needs: decision -- Alex or Morgan, whether that Rule names roles).
