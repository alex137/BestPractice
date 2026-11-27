---
slug:        record-not-instruction
title:       A person's name and a dated incident belong in the record, never in the instruction
tier:        on-demand
severity:    default
applies_to:  ["AGENTS.md", "CLAUDE.md", "GEMINI.md", "practices/**", "local/practices/**", "templates/**", "tools/*.py", "tools/*.sh", "reply_check.json", "*.md", "documentation/**"]
applies_to_why: "Its own applies_to. The occasion is writing text a session or another repository will be told to follow, and those are these paths: the instructions files, a practice's Rule, anything under templates/, the scripts and reply rules whose messages a session is shown, and the documents at the root and under documentation/ that tell a person or a session how to install, set up or use the repository. The path channel reaches it, so it costs no index line."
occasion:    "writing or editing an instructions file, a practice's Rule, a template, or a message a tool prints"
gates:       []
index_clause: "who decided and when goes in the record; an instruction says the rule, by role"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-11-25"
approved_by: "Alex, 2026-11-25: 'I trust your judgement on both', to a cleanup of the instructions file, the templates and the rule texts with this rule and its check landing first; he had asked the same day why the instructions file named him and Morgan and what would have prevented it"
strength: assented
---
## Rule
**Who decided a thing, and when, is the record. What to do is the instruction. Keep them in different places.**

**The record** is where a name, a date and a person's own words belong: a practice's `approved_by:` and `## Story`, a decision or an open item, a commit message, a comment in code beside the line it explains.

**The instruction** is what a session, or someone else's repository, is told to follow: an instructions file a session loads, a practice's `## Rule` and `## Detail`, anything under `templates/`, a message a tool prints, and a document that tells a person or a session how to install, set up or use the repository. It says what is true now and names people by role: the person, a code owner, the administrator. It carries no "Name, date" stamp, no strength marker, and no "until such a date this did X".

**A reader who wants the why follows a link to the record.** The instruction links the practice or the item; it does not retell it.

## Detail
**The test is who reads it.** A record is read by someone asking why a rule exists, and it has to be exact about who said what. An instruction is read on every call by sessions working for people who were never part of that conversation, in repositories that have never heard the names. To them a name is noise at best, and at worst it reads as "this rule is about those two people".

**A practice set is used by more than the people who wrote it.** A rule that says "no merge needs so-and-so's sign-off" is a rule about one repository's owner. Written as "a session may merge into the landing branch once its check passes", it is a rule anyone can use, and the person who granted it is in the approval line where a reader checking the grant will look.

**Dates that are the content stay.** A rule about the outside world carries the date it was true ([volatile-rules-carry-dates](volatile-rules-carry-dates.md)), a schedule says when it runs, and an example of a date format is an example. What goes is the date of the rule's own history.

**`## Detail` is covered.** It loads on demand, but when it loads it is read as what to do, by a session that has never heard the names in it. What stood behind a line of Detail (who asked, when, in what words) is in that practice's Story.

**The check counts, and the count only goes down.** A file that is not clean yet has its present count recorded, and the check refuses a file that rises above its count or a new file that carries any.

**What the check sees.** In an instructions file's hand-written part, in every active practice's `## Rule` and `## Detail`, in every text file under `templates/`, in every Markdown document at the root and under `documentation/`, in every string a script directly under `tools/` can print, and in every reason `reply_check.json` holds: a capitalised name followed by a date, a `(strength: ...)` marker, and a history opener such as "Until", "Since" or "Rewritten" followed by a date, at the start of a sentence or inside one ("retired 2026-..."). It cannot see a name with no date beside it or history told without one. Two openers are passed over in lower case, because there they are mostly content: "as of" a date is how a fact about the outside world carries its date ([volatile-rules-carry-dates](volatile-rules-carry-dates.md)), and "before" a date is usually a cutoff a check applies. It does not read a test, a script in a subdirectory of `tools/`, a registry other than `reply_check.json`, a document a tool generates whole, or one that declares itself a dated record with the record-doc marker.

**A tool's own record stays in the tool.** A comment and a docstring are the record, and so is a comment in code a tool emits. A string that is the record on purpose (an approval line a tool writes into `approved_by:`, a Story it writes into an open item, a table of who approved a check) carries the comment `# record-not-instruction: the record` on its statement or in the three lines above, and the check passes it over. In `reply_check.json` the reason a refusal prints is `why`; who asked for the rule, when, and the incident go in `_story` beside it, which nothing prints.

## Why
Two rules here pull against each other. One says a rule records the incident behind it and who approved it. Another says a document states what is true now. Nothing said where the first stops, so the citations spread from the stories into the rules, the instructions file and the templates, and only the first rule had a check.

## Story
2026-11-25. The person this repository belongs to opened its instructions file to look at the occasion index and read the rest. Its first paragraph said whose sign-off a merge did not need, relayed by whom, on what date, with a quoted question from two weeks later. He wrote: "It has specific mention of Alex and Morgan in the top, references to random history. It looks like it violates a bunch of best practices itself. BestPractice is not just for alex and morgan." A count the same day found a name-and-date stamp or a dated history line in the instructions file, in seven practices' rule text and in 35 files under `templates/`, which ship into other people's repositories. The session doing the count had added several itself that week, in tool comments and in the text a reply rule prints, by copying what the surrounding files did.

2026-11-27. Two things were left for a decision when the first cleanup finished: history that opens in lower case inside a sentence ("retired 2026-09-21"), which the check did not see, and a practice's Detail, which had been left out on purpose. Alex, asked both with a count and a pick for each: "yes for both." (strength: decided). The Detail sections then held close to three hundred pieces of the record, more than half of them in three long practices.

## Install
`precedent.json` carries `record_in_instructions_before_the_rule`: each instruction file's count from before the rule. A file may fall below its count and never rise above it, and a file not listed may carry none. Cleaning a file lowers or removes its entry in the same commit. A repository that declares no such list is skipped by the check until it adds one, as `{}` or with its own counts.
