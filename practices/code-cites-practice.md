---
slug:        code-cites-practice
title:       Code that exists because of a practice cites it by slug, in place
tier:        on-demand
severity:    default
applies_to:  ["tools/**"]
occasion:    "writing code because a specific practice requires it"
gates:       []
index_clause: "cite the practice's slug in a comment, right where the code is"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "pending review"
---
## Rule
When a line of code exists because a specific practice requires it — not
because of ordinary program logic — the code carries a `# practice: SLUG`
comment naming that practice, right at the point of implementation. The
slug is the citation, never a position number, a paraphrase of the title,
or a bare mention of the practice's subject with no way to look it up.

## Detail
This is deliberately narrow. It does not ask every function to explain
itself — most code exists for ordinary reasons a comment would only
restate. It applies only when the *reason* a piece of code exists is "a
practice says so," which is exactly the case where a reader asking "why is
this line here?" cannot answer the question by reading the code alone, no
matter how well-named the variables are.

The citation runs both directions on purpose:
- From code to practice: `# practice: disclose-landing` above
  `precedent_land.py`'s `DISCLOSE TO THE HUMAN:` print statements answers
  "why does this print this?" without anyone having to ask.
- From practice to code: a practice's own `## Install` section already
  names where its implementation lives (an established convention — see
  `reply-links-files.md`'s or `capture-gate.md`'s own Install sections).
  The comment is the return path: starting from the code, a reader reaches
  the practice; starting from the practice, `## Install` reaches the code.

**Slugs, never numbers, and this is not a style preference.** A practice's
slug is a stable identifier by design; the position-based scheme it
replaced was not, and it broke in the way stable identifiers exist to
prevent: three tool comments (`doc_html.py`, `table_fmt.py`, `doc_lint.py`)
cited a *practice number* that had been correct at the time, and silently
went stale the next time practices were renumbered — a comment-only fix
was needed later to catch up (`git log`: "Fix practice number citations in
three tool comments"). A slug does not renumber. This practice is that
lesson generalized past the one place it was fixed.

## Why
Asked directly whether retiring a practice in text could leave its
implementation quietly behind in code — with nothing to connect the two,
and nothing to notice the mismatch — the honest answer was that nothing
prevented it. A practice's own `## Install` section names its code in
prose, but nothing pointed the other way: code carried no marker saying
*this exists because of a practice*, so there was no way to find what
needs to change, or get removed, when that practice's own status changes.
`disclose-landing.md` is the concrete case that surfaced this: its
`DISCLOSE TO THE HUMAN:` print statements existed with no citation at all
until this practice asked for one.

## Story
Built alongside `disclose-landing`, not before it — the print statements
that practice requires were already written and merged with no citation
back to the practice that required them. Adding the citation after the
fact, rather than from the start, is exactly the gap this practice exists
to close: a citation that has to be remembered separately from the code it
belongs to is a citation that will eventually be forgotten, on the next
practice, by the next session.

## Install
`tools/precedent_check.py`'s `code-cites-practice` check scans `tools/**/*.py`
for the `# practice: SLUG` marker and verifies each cited slug is a real,
`active` practice — catching a typo, a deleted practice file, or a
retirement that left its implementation behind. It cannot check the
opposite direction: code that *should* carry a citation but doesn't. That
half stays a review judgment, the same limit `checkable-gets-checked`
already names for practices in general.
