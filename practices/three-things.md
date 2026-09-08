---
slug:        three-things
title:       "\"Three Things\" asks for the three most important things to know now"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Three Things\""
gates:       ["reply"]
index_clause: "\"Three Things\" -- the three that matter now, one bold phrase and two lines each"
checked_by:  null
defines:     ["Three Things"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08 -- coined and placed at universal in the same message"
---
## Rule
When the person says **"Three Things"**, answer as if they had asked this:

> Based on everything you know about this repository itself and its content,
> including its recent activity, and based on everything you know about me,
> including my role and my work in the repository, and everything you know
> about the others in it — tell me the three most important things I need to
> know now. Each of the three should be short: a bolded phrase, then perhaps
> two more sentences of detail. Nothing more.

**Three. Not two, not five, and not three plus a preamble.** The whole reply
is a bolded phrase and at most two sentences per item, and it ends there — no
opening line explaining what you are about to do, no closing offer to go
deeper, no fourth item smuggled in as a note.

## Detail
**Read before you answer.** The phrase names four inputs, and skipping any of
them makes the answer generic: the repository's own state, its recent
activity, who is asking and what they do here, and who else is working in it.
A reply assembled from what happens to be in the session's context is the
failure this practice exists to prevent — the person asking already knows
what was in the last twenty minutes.

**Important to *them*, now.** Not the three largest items, not the three most
recent, not the three you find most interesting. A maintainer and a
first-week contributor asking the same morning should get different answers,
and a thing that is enormous but already handled is not one of the three.

**Say the uncomfortable one.** The value of a fixed number is that it forces a
ranking, and a ranking that omits the problem in order to be pleasant is
worth nothing. If something is blocked, wrong, or about to break, it outranks
progress.

**A "Files touched" list is still owed** if the turn changed files, and it
sits outside the three, after them. The three-item shape governs the answer,
not the reply conventions the repository already has
([reply-links-files](reply-links-files.md)).

## Why
The question a person actually has when they come back to a project after a
day away is *what do I need to know?*, and it is expensive to ask well: asked
loosely it returns a status dump, and asked precisely it takes a paragraph to
set up every time. **A named command is that paragraph, written once.**

The fixed count is the working part. Left open, a summary grows until it
covers everything and therefore ranks nothing, which is the same failure
[bold-key-phrases](bold-key-phrases.md) and
[deliverables-look-like-output](deliverables-look-like-output.md) are each
about from a different side. Three forces the judgment onto the session,
which is the only thing being asked for.

It also has a property the other commands here do not: it is the one phrase
that asks for **attention rather than action**. `Go merge`, `Park it` and
`Update Vendors` each tell a session to do something. This one asks what it
has noticed — which is only worth asking of a session that has actually read
the repository, and is therefore also a fair test of whether the practice
sources resolved at all.

## Story
**Coined by Morgan, 2026-09-08**, in the same message that raised the
day-to-day usage documentation — placed at universal from the start rather
than promoted later, unlike `go-merge` and `park-it`, which each spent a day
at the wrong level first: *"Have a new command, in vocab etc, called 'Three
Things'."*

He supplied the prompt text himself and it is quoted above rather than
paraphrased, which is deliberate. The wording is the specification: an
earlier command in this set (`go-merge`) was retired once and reinstated
because the version that survived had told each adopter to invent their own
phrasing, and a phrase nobody spells out is a phrase every session guesses
at.

## Install
Nothing mechanical checks that a reply obeyed the shape — like `go-merge` and
`park-it`, that lives in the conversation. What reaches a session is the
occasion index entry above, which is generated, so an adopter installs
nothing.
