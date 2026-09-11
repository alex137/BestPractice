---
slug:        session-load-budget
title:       Every always-loaded surface carries a declared ceiling, in every repo in force
tier:        on-demand
severity:    default
applies_to:  ["AGENTS.md", "CLAUDE.md", "**/AGENTS.md", "**/CLAUDE.md", "templates/*AGENTS.md*", "tools/session_load_budgets.json"]
occasion:    "adding to a file every session loads, or asking what a session pays before it starts work"
gates:       []
index_clause: "declare a ceiling for what every session loads; reduce by archiving"
checked_by:  "tools/precedent_check.py"
defines:     ["always-loaded surface", "session load"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-11"
approved_by: "Morgan, 2026-09-11 (strength: decided) -- asked whether the very deep check reviews token cost across this repo and the repos it calls, and said the review and the reduction that follows it should be a rule"
---
## Rule
**Everything a session loads before it does any work carries a declared
ceiling, and every ceiling lives in one registry** —
[tools/session_load_budgets.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/session_load_budgets.json).
That is the instructions file, anything it includes, the generated resident
block, and the session-start file the private sources write. A surface that
is loaded and not in the registry is the finding; so is one over its ceiling.

**Measure every repo in force, not the one you are rooted in.** A session
loads its own instructions file *and* whatever each attached team,
individual and repo-local source contributes, and the cost is the sum. A
per-repo cap that is green in each repo separately says nothing about what
any session actually pays.

**A cap on one part is not a cap on the whole, and reading it as one is the
failure this exists to prevent.** The resident block's 2,000-token cap
governs the resident block. It governed about 4% of this repository's own
session load while the rest went unmeasured for weeks.

**Then reduce — and reduce by moving, never by deleting.** The question for
each part is **"would a session hit this today"**, never "how big is it". What
still bites stays, whatever it costs; what no longer bites moves to a linked
archive **in full**, because the payload of a gotcha is the story of what
failed ([environment-gotchas](environment-gotchas.md)). A trimming pass that
chases the total deletes the entries that are working, and leaves a live
section of unexplained rules behind.

**A ceiling is a watermark, not an endorsement.** It is set at what the
surface measured when it was last reviewed, so it ratchets down and never
drifts up unnoticed. Raising one is a decision made on purpose, in a commit,
with the reason written in the registry — never a way to make a red check
green.

## Detail
**What counts as an always-loaded surface.** Anything in a session's context
before its first turn: `AGENTS.md` and `CLAUDE.md` (and whichever of the two
the harness reads), the generated resident block and occasion index inside
them, `.precedent/SESSION_PRACTICES.md`, and each attached source's own
instructions file. Not: a practice's Rule pulled on occasion, a spec read
because somebody asked, or anything reached through a link. The line is
whether a session pays for it having decided nothing.

**Two ceilings that are not the same ceiling.** `resident_block_tokens` is a
hard build cap — [tools/build_views.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/build_views.py) refuses to
generate a resident block over it, so the trade is forced at the moment
somebody promotes a practice. A surface `ceiling` is a review trigger: it
fails the check, and what it asks for is a reduction pass, not a deletion.
`section_review_tokens` is neither — it is the size at which
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py)'s SESSION LOAD
section flags one `##` section as worth splitting.

**Where the reduction usually is.** In practice it is one section, not the
whole file: a gotchas section that has accumulated settled entries, an index
that has grown a row per file rather than a row per question, a preamble
that has become a changelog. Read the per-section table SESSION LOAD prints
and work the largest one; the total is an outcome, never the target.

**This does not license trimming a source you do not own.** A team or
individual source over its ceiling is a finding to report to whoever owns it
([cross-source-rollout](cross-source-rollout.md)), not an edit to make from
here.

## Why
Nothing is wrong at any single commit. Every line in an always-loaded file
was right to add on the day it was added, and it only goes wrong in
aggregate, months later — which is exactly the failure a per-commit gate
cannot see, and exactly the failure a declared ceiling can.

The cost is real and it is paid on every turn of every session. It is also
paid *first*, before the work, so it comes out of the same budget the work
needs — a repository that spends twenty thousand tokens explaining itself has
that much less room for the thing it was opened to do.

The reason this needs a rule rather than a habit is that the measurement and
the remedy pull in opposite directions. Measuring rewards deletion; the
content being measured is the accumulated cost of every trap this project has
already paid for once. **A rule that only said "measure" would reliably make
the repository worse.** So the ceiling and the "would a session hit this
today" test ship together, and the archive-in-full clause is the part that
does the work.

## Story
**Morgan asked for it on 2026-09-11**, as a question about
[very-deep-check](very-deep-check.md): does the very deep check review token
use across the repo *and the repos it calls*, check the 2,000-token cap at
its various points, and then look for where usage can be reduced — and if
not, that should be a rule.

Half of it was already there and half was not. Pass 3 of the very deep check
carries "What every session loads, and what it costs", added 2026-09-08 after
the resident block's 2,000-token budget was found reporting green for weeks
while [AGENTS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md) around it passed 17,000 — the budget
governing 4% of the cost, with nothing measuring the rest. That pass moved 24
gotcha entries' full text to
[record/GOTCHAS_ARCHIVE.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS_ARCHIVE.md) and took ≈4,900
tokens off every session, deleting nothing.

**What was missing was everything that makes it a rule rather than a
paragraph.** It ran only inside the very deep check — on request, rarely, by
a session that thought to ask. It measured only `repo_root`, so the attached
sources were never counted despite the very deep check's own scope sentence
saying every repo in force. And no surface had a declared ceiling, so
"reporting green" meant only that no single section had crossed a flag: the
file as a whole could not be over anything, because it was not under
anything.

Measured the day this was written, on this repository: `AGENTS.md` **19,687
tokens**, of which the gotchas section is 10,494, the occasion index 2,678 and
the resident block 894 — plus `.precedent/SESSION_PRACTICES.md` at 2,887.
**22,624 tokens before the first turn**, with a cap declared over 894 of them.

**It fired on its own repository within the hour**, which is the part worth
keeping. The ceiling was set at 19,000 against a checkout 14 commits behind;
merging `precedent-beta-v01` brought a freshness-guard gotcha added upstream
the same day and put the file at 19,687, over its own ceiling. The rule's
first demand is a reduction pass, so that is what was run: every entry
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) flagged as claiming its
own trap settled was read against the tree, and each still bites — including
the new one, which says in its own words that the shape of the trap survives
the fix. So nothing was archived and the ceiling was raised once, to 20,000,
with that reasoning written into the registry entry. **A ceiling raised after
the review is the mechanism working; one raised instead of it is the failure
the clause is about**, and the difference is only ever visible in what the
`why` field says.

## Install
The registry is
[tools/session_load_budgets.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/session_load_budgets.json): one
entry per always-loaded surface, each carrying `ceiling`, the `measured` size
and the date it was `reviewed`, plus the `resident_block_tokens` cap
[tools/build_views.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/build_views.py) enforces at build time and
the `section_review_tokens` flag
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) prints against. Both
tools read the registry rather than carrying their own literal, so no cap is
spelled twice.

`python3 tools/precedent_check.py --only session-load-budget` runs the
mechanical half in any repo the engine is vendored into: it fails on a loaded
surface with no entry, and on one over its ceiling. An adopting repo with no
registry gets a named skip, not a pass.

The sum across every repo in force — and the reduction pass itself — is
[very-deep-check](very-deep-check.md)'s SESSION LOAD section, which prints
this checkout and each attached source, section by section.
