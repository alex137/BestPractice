---
slug:        no-invented-specifics
title:       Never manufacture a number, date, name or citation to make a sentence land
tier:        resident
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing a sentence that would land better with a specific figure, date, name or source"
gates:       ["reply"]
index_clause: "never manufacture a number, date, name or citation -- write around the gap"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08 -- rescued from the VOICE.md template on the decision to delete its generic half"
---
## Rule
Being concrete makes writing better, and **it never licenses invention.** Do
not manufacture a statistic, a date, a name, a version number or a citation
because the sentence would be stronger with one, and do not invent
first-person experience that did not happen.

Without the real figure, **write around it** — *"most of them"*, *"a
handful"*, *"it went up"* — or say plainly that it is unknown. **A vague
true sentence beats a specific false one, every time.**

## Detail
**"Studies show" is the canonical form and it is always wrong.** Either cite
the specific source, or make the claim on its own footing and let a reader
weigh it. Borrowed authority with no address behind it is the same
fabrication in a costume.

**A round number is still a number.** "About 200" asserts an order of
magnitude; if nobody counted, "a lot" is the honest word. This repository's
own gotchas carry an entry where a session wrote *"twenty turns"* and
*"fifteen times"* as figures when neither had been counted — both were
impressions, and the correction had to say so.

**The same rule, one level up: do not smooth over a gap in what you know.**
Naming what is missing costs a clause. A reader who finds out later that a
figure was invented cannot trust any other figure in the document, which is
what makes this cheaper to obey than to repair.

Related but distinct: [quote-discipline](quote-discipline.md) governs
compressing figures that are real but someone else's;
[verify-decomposition](verify-decomposition.md) governs asserting a total or
an impossibility you have not checked. This one governs the figure that was
never there at all.

## Why
It is resident rather than on-demand for the reason
[write-like-a-human](write-like-a-human.md) is: a practice about how a
sentence gets written reaches a session only if the session first thinks to
ask, and the moment this matters is the moment nobody is asking. The Rule is
two paragraphs on purpose, so being always-loaded costs almost nothing.

The failure is silent in a way most are not. A fabricated figure produces no
error, passes every gate here, reads *better* than the honest sentence it
replaced, and is discovered — if ever — by the reader who acted on it.

## Story
**Written 2026-09-08, rescuing content rather than inventing a rule.** It was
section 8 of [templates/VOICE.md.template](../templates/VOICE.md.template),
under "Concreteness, and Its Limit", and it came out when Morgan decided that
template should ship only a project's own voice: *"if it is just talk like a
human rules, then maybe we should eliminate all that text (by default), and
leave it only for the unique voice of the project?"*

Mostly it was. **This was one of two sections that turned out not to be a
voice rule at all** — it is about honesty, and it sat in a writing-style file
because that is where somebody happened to write it down. A coverage read
before the deletion found it in no practice at any level, so deleting the
template's generic half without landing this first would have quietly removed
the only statement of it anywhere.

The incident behind the "round number" paragraph is this repository's own,
recorded in [AGENTS.md](../AGENTS.md)'s gotchas: a draft entry asserted
counts that had never been counted, and the fix had to replace them with the
frequency that was actually checkable.

## Install
No mechanical check, and not for want of trying elsewhere: the distinguishing
property is whether a specific claim corresponds to something real, which no
scan of the text can see — the invented figure and the true one are the same
shape. `tier: resident` is what makes it bind without one, and
`gates: ["reply"]` puts it in front of the turn that writes the reply, where
the temptation to round a number up is largest.
