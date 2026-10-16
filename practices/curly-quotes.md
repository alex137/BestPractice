---
slug:        curly-quotes
title:       Markdown keeps plain quotes and hyphens; anything built for an outside reader gets curly quotes and real dashes
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Any file can be built into something an outside reader sees, and the Markdown half is about every Markdown file, so no narrower path holds. The occasion clause reaches a session building an output; the engine applies the rule itself to every HTML page it writes (tools/finish_html.py). Decided: 2026-10-16, on the move to universal."
occasion:    "building a Word document, a web page, any HTML output or any other format an outside reader sees, or writing quotes and dashes in Markdown"
gates:       []
index_clause: "plain quotes and hyphens in Markdown; anything built for a reader converts them"
checked_by:  null
ships:       []
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-16"
approved_by: "Morgan F, 2026-10-16, moved here from the writing practice set at his choice (\"Option 3\"), its typography.py made an engine file; before the move: Morgan F, 2026-09-18, via Go Update -- moved here from a private repo-local set, generalized from a hardcoded directory list to a repo's own declared output_paths; dashes added 2026-10-13 at his own request (\"the same for -- and --- becoming n- and m-dashes\", \"the dashes should also be a practice\"), by judgment rather than count; Markdown keeps hyphens and straight quotes, the conversion moves to building outward formats, real dashes stay allowed in Markdown, 2026-10-13 (\"In Markdown documents, we should only use normal hyphens ... whenever we format it for external use, such as creating a [Microsoft] Word document or on a website, then the double dashes should always become an M dash\"; \"within internal markdown documents, the M-dash and N-dash can optionally be used, so their use should not cause any errors\"); quotes follow the same model, first on his go-ahead to the proposal that said so and then in his own words, 2026-10-13 (\"the same structure should apply to curly quotes as well. Anything for external use should change them. And internal use, we do not expect to use them, but there's no error if they are used\"); code is the exception, 2026-10-13 (\"make sure in code blocks that are for public use, like examples for the public, that those are not replaced, because double dashes and dashes have particular meanings in code\"); every HTML output, 2026-10-16 (\"Note that that is an artifact web page and it applies there and also it should apply when we make real web pages as well like we do in [a project repository], basically in any html file or html output\")"
strength:    decided
---
## Rule
**Markdown is typed with plain keys.** A straight quote (`"`, `'`), a hyphen,
and two hyphens with no spaces for a long dash (`word--word`) are what a
Markdown file is expected to hold, outward-facing ones included. A real em
dash (—), en dash (–) or curly quote typed into one is not expected, and is
never an error either: nothing flags either form.

**Anything built from Markdown for an outside reader gets finished
typography**: a Word document, a web page, and any format added later.
**Every HTML output counts**, whoever it is for: a page published as a
Claude Artifact, a generated website, any `.html` file a script writes.
Its builder runs the text through
[`tools/typography.py`](https://github.com/alex137/BestPractice/blob/staging/tools/typography.py)'s `smarten()`, the one copy
of these rules, never a copy of its own; an HTML builder runs its finished
page through `smarten_html()`, which changes the text a reader sees and
never a tag, an attribute, a comment, a script or code:

- `--` and `---` always become an em dash (—), spacing kept as typed.
- A hyphen between two numbers that make a range becomes an en dash:
  1990-2000, pages 10-20, 9-5, 3:00-5:00. A date (2026-10-13), a phone
  number, and a hyphen next to a letter (PR-173, B-52) stay hyphens.
- A range in words ("Monday-Friday") keeps its hyphen; a writer who wants
  the en dash there types it.
- Straight quotes become curly ones.
- **Code never changes**: a code span (`` `git push --force` ``) and a
  fenced code block keep every character as typed, because in code `--`
  and `-` mean something exactly. That holds for examples written for the
  public too.
- A web link's address and a backslash-escaped character never change.

## Detail
- **A builder that skips `smarten()` is the bug**, not the Markdown it
  read. The writing set's Word builder (`create-word-doc`) calls it on
  every paragraph and heading; a
  web-page or slide builder for outside readers does the same.
- Code is never prose. `smarten()` skips a code span itself, so a
  builder gets that for free; a fenced block never reaches `smarten()` at
  all. That builder sets both in a fixed-width face, the span
  without its backticks.
- **Why not convert the Markdown itself**: the source stays easy to type
  and to search, two writers never fight over which dash key to press, and
  the rules sit in one function that every output shares, so changing one
  of them changes every format at once.

## Why
Untidy typography is one of the cheapest "reads like it wasn't cared for"
signals a reader hits, and it is entirely mechanical to avoid. It belongs
where the reader meets the text -- the Word file, the page -- not in the
working copy, where plain keys are faster and nobody outside sees them.

## Story
Raised by Morgan, 2026-09-18, in a private repo, in the
same thread that produced two practices local to that repo (on glossing
Hebrew terms, and on fixing typos without resolving an ambiguity), asking
for a third standing practice specifically about converting straight
quotes to curly ones. Only this one moved to a shared set; the other two
are in no shared or universal source, so neither is cited as a rule here.
Writing the mechanical check per `checkable-gets-checked` surfaced that essentially the entire
existing outward-facing corpus predated the convention -- all 23 outward
files that repo had at the time carried at least one straight quote in
prose scope -- so the check was wired in with that full list
grandfathered rather than left `checked_by: null` or shipped in a form
that would fail every future push until someone did an unplanned,
unscoped rewrite of the whole cluster.

Same day: Morgan asked whether a book manuscript -- the file
the practice's own Why section pointed to as the house style's own
example -- had actually been converted. It hadn't: it was sitting on the
grandfather list from the initial audit, unconverted, and the Word export
(`create-word-doc`) was faithfully carrying the straight quotes through
from source, which is what surfaced the gap. Converted (19 straight-
double-quote pairs, all self-contained with no nesting; no straight
apostrophes were present) and dropped from the list.

**Moved to `precedent-team-writing` on 2026-09-18**, from
a private repo-local set, alongside `create-word-
doc` in the same reconsideration: the rule is about the craft of writing
for a reader, not about that repo's subject. The move required real
generalization, not a copy -- the original check imported that repo's
own title-case tool for its outward-file boundary and hardcoded its
23-file grandfather list; both are repo-specific and cannot travel as
team content. The boundary is now the `output_paths`/`internal_paths`
`deliverables-carry-no-process` already reads generically, and the
grandfather list is now a repo-declared `precedent.json` key the
consuming repo owns. `Go update`.

**Turned around on 2026-10-13.** The same day the dash rule was added, the
check began flagging `--` in outward Markdown, and a consuming repo's
README failed on a command example (`--check`) that wrapped across a line.
Morgan then set the model this file now states: Markdown keeps plain
hyphens, `--` stands for the long dash while drafting, and the conversion
happens only when something is built for an outside reader. A real dash
typed into Markdown stays allowed. Quotes moved to the same model, so the
Markdown check and its grandfather list
(`curly_quotes_grandfathered`) were removed, and the rules moved out of
the writing set's Word builder into [`tools/typography.py`](https://github.com/alex137/BestPractice/blob/staging/tools/typography.py) for every builder to share.
The same change made `--` always an em dash, where it had been an en dash
when spaced or between numbers, and made a hyphen between two numbers an
en dash.

Later the same day Morgan confirmed quotes follow the same model in his own
words, and named the exception: code. The Word builder until then had no
idea what code was, so a command in backticks or a fenced example would
have had its `--` turned into a dash. `smarten()` now skips a code span,
and the writing set's Word builder sets fenced blocks and code spans as typed.

## Install
[`tools/typography.py`](https://github.com/alex137/BestPractice/blob/staging/tools/typography.py) is an engine file: every
repository that vendors the engine has it in `tools/`, and every builder
imports it from beside itself (`from typography import smarten`, or
`smarten_html` for a page). `python3 tools/typography.py "text"` prints the
converted text; `--html` converts a page read on standard input. Every
HTML page the engine writes goes through
[`tools/finish_html.py`](https://github.com/alex137/BestPractice/blob/staging/tools/finish_html.py), which applies it.

Until 2026-10-16 this practice and the file lived in the writing practice
set, which shipped the file to the repositories that declared
it. A repository updated since takes the engine's copy instead; the same
bytes, so nothing changes in what it builds.

**A repository that took this practice before 2026-10-13** loses
the retired curly-quotes check and its test on its next update.
Three things in its own files can still name them, and each refuses the
landing until it goes:

- the `precedent.json` key `curly_quotes_grandfathered`, which nothing
  reads any more: delete it;
- a repo-local stub practice that deduplicates this one: set its
  `checked_by:` to `null`;
- any other file, a closed open item included: drop or repoint the
  check's name.

Update Vendors lists every file of the third kind as left for the person
(engine from 2026-10-15 on), rather than printing it and finishing.
