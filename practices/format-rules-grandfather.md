---
slug:        format-rules-grandfather
title:       A format rule never stops an old practice from being used
tier:        on-demand
severity:    default
applies_to:  ["tools/precedent_check.py", "tools/frontmatter_yaml.py", "spec/PRACTICE_FORMAT.md", "tools/precedent_update.py"]
applies_to_why: "These are the files where a rule about the shape of a practice, an open item or a record is written, enforced or rolled out, so editing one is when a new format rule is about to reach every repository. Decided: 2026-10-05, the evening the field-order check stopped a project repo."
occasion:    "adding or tightening a rule about how practices, open items or other records are laid out"
gates:       []
index_clause: "old files get a warning and an automatic tidy, never a refusal"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan, 2026-10-05: \"I think we should be flexible and graceful in grandfathering in old practices, updating them as needed but not stopping them from being used\""
strength:    decided
---
## Rule
**A rule about format never stops an old practice, open item or record from
being used.** When one is added or tightened -- field order, which fields
exist, how a park or a label is written -- everything written before it
keeps loading and keeps working:

- **The check warns, it does not refuse.** It names the file and the one
  command that fixes it, and the push goes ahead.
- **The tooling updates old files as it touches them**: the commit hook on
  the files being committed, Update Vendors on a repository's own practices.
  Nobody has to stop and tidy by hand before they can work.
- **A field this engine does not know is ignored, with a warning**, never
  treated as a broken practice.

A check may refuse only what makes a practice or an item **behave wrongly**,
never how it is laid out.

## Detail
**Register a format check as a warning from the start**, with
`advisory=True` and a permanent term saying it is a shape rule
(`advisory-checks-declare-their-term` asks for one). Making it a refusal
later, "once everyone has tidied", is the mistake this practice records:
other people's repositories do not tidy on BestPractice's schedule, and
some of them are not people BestPractice can reach.

**Give the warning its fix.** A warning that names
`python3 tools/frontmatter_yaml.py --fix-order` or
`python3 tools/todo_disposition.py park` costs the reader one command; one
that only says "out of order" costs them an investigation.

**Fix the source, never a copy.** A project repository's own practices live
in `local/practices/` and are rendered into `practices/`; tidying the
rendered copy is undone by the next sync.

## Why
Precedent is used by people who are not its authors, in repositories whose
history predates every rule it adds. A stricter format that refuses old
files turns each engine update into a stop-the-world chore for every one of
them, for a difference that changes nothing about how a practice works.
The cost lands on the people least able to absorb it, and the lesson they
take is to stop updating.

## Story
**2026-10-05.** That morning the field-order check, a warning since
2026-09-26, was made a hard check, on the reasoning that every practice set
had just been tidied. The same evening a project repository took the new
engine and could not push until a session reordered ten of its own practice
files -- files that loaded and worked exactly as before. Two other checks
added that morning, on how a "Drop it" park is recorded in a todo item, were
hard too and would have stopped any repository with older parks. Morgan:
*"Some repos are having problems because of the new stricter format. This
will cause problems with others using [BestPractice]. I think we should be flexible and
graceful in grandfathering in old practices, updating them as needed but not
stopping them from being used."* All three became permanent warnings, and
Update Vendors began tidying a repository's own practice files itself. The
full account is in
[spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md).

## Install
Nothing to install. The field-order and park-record checks in
[tools/precedent_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py)
are warnings, and
[tools/precedent_update.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update.py)
tidies field order on every Update Vendors.
