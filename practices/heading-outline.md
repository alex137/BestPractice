---
slug:        heading-outline
title:       "A document's heading levels form an outline, with nothing skipped"
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "adding or re-levelling a heading in any document"
gates:       []
index_clause: "never jump a heading level; a heading one below its parent, or deeper by one"
checked_by:  "tools/precedent_check.py"
defines:     ["skipped heading level"]
status:      active
supersedes:  []
overrides:   null
added:       "2026-09-06"
approved_by: "Morgan"
source_practice_number: null
---
## Rule
A heading is never more than one level deeper than the heading before it.
`##` may be followed by `##` or `###`, never by `####`: a heading two or
more levels down has no parent, and every renderer that builds an outline
from the document — a table of contents, a sidebar, an accessibility tree,
a fold in a reader — has to guess what it belongs to.

The rule is exactly that one, and deliberately no wider. Two neighbouring
rules that look like they belong here do not, because neither survives
contact with a real corpus:

- **"The first heading is an H1" is not a rule.** 80 of this repository's
  153 tracked markdown files open at `##`. A convention four fifths of the
  corpus disagrees with is not the convention.
- **"Siblings share a rank" cannot be checked.** A section legitimately
  nests deeper than the one before it, and no tool can tell that from a
  section that was demoted by accident. The skip is the part that is
  decidable, and it is where the actual damage is.

## Why
Heading level is the only structure a markdown document has. Prose can be
reordered and a reader copes; a broken outline silently misfiles a whole
section under the wrong parent, and the document still looks right in the
editor where it was written — the damage appears in the rendered view, the
table of contents, and the screen reader, all of which the author is not
looking at.

It is also the cheapest possible check: three lines of state, no
dictionary, no judgment, no false positives. A rule that costs this little
to enforce should not be left to attention.

## Story
This rule is a restoration, not an invention. A team-level practice
`header-caps` carried two rules at once — headline capitalization *and*
heading-level consistency — under one slug, one check, and one `**/*.md`
scope. When the capitalization half was promoted to the universal
catalogue on 2026-09-06 as
[headline-capitalization](headline-capitalization.md), the team rule was
retired whole, and the outline half went with it: it had been mechanically
checked, and for a few hours it was checked nowhere. The audit that
retired it said so explicitly rather than letting it pass — *"that is a
document-outline rule, not a capitalization rule, and the universal
practice does not address it anywhere. Now unenforced."*

The lesson worth more than the rule: a practice carrying two unrelated
rules loses one of them the moment the other moves, and nothing about
promoting the first will mention the second. `header-caps` bound both
halves to `**/*.md`, and that single scope is what made the split look
like a loss on both sides. It was not. **Capitalization is an
outward-facing concern only** — how a heading is *styled* matters where
people outside the project read it, and nowhere else, which is why
[headline-capitalization](headline-capitalization.md) binds
`documentation/` deliberately and correctly (confirmed by Morgan,
2026-09-06). Whether an outline is *broken* is not a matter of audience,
so this half takes the wide scope and that one does not. Two rules, two
scopes, which is exactly what one slug could not express.

## Install
[tools/doc_lint.py](../tools/doc_lint.py)'s `scan_heading_skips` is the
detector, reported in the light check that runs before every commit and
failing it in scope. `tools/precedent_check.py`'s `heading-outline` gate
calls the same function on changed documents — one detector, two callers,
so the warning and the gate cannot drift apart.

Fenced code blocks are skipped, so a `#` comment inside an example is
never mistaken for a heading.
