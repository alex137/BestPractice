---
slug:        practice-standing
title:       A practice says how binding it is, and only authority makes one binding
tier:        on-demand
severity:    default
applies_to:  ["practices/*.md", "local/practices/*.md"]
applies_to_why: "The label is written into a practice file's frontmatter, so editing one is when a standing gets set or changed. The other half -- setting a Preference aside -- needs no route of its own: every channel that shows a labelled practice prints the label and what it allows beside it. Decided: 2026-10-05, spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md step 5."
occasion:    "labelling a practice Protocol, Principle or Preference, or setting a Preference aside"
gates:       []
index_clause: "no label means Protocol; only authority sets Protocol or Principle"
checked_by:  "tools/precedent_check.py"
defines:     ["Protocol", "Principle", "Preference"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan, 2026-10-05 -- the three standings, Protocol as the default, Preferences kept, and Morgan and Alex approving Protocols and Principles in the universal set were each decided on their own (spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md); this wording and the relayed-approval line came with the plan he approved as a whole"
strength:    assented
---
## Rule
Every practice has a **standing**:

- **Protocol** — must be followed. **A practice with no `standing:` is a
  Protocol**; only the exceptions are labelled.
- **Principle** — a standing philosophy, applied with judgment.
- **Preference** — someone's way of doing things. Follow it by default; a
  session that sets one aside **says why**, in the reply.

**Only someone with authority over the source sets a Protocol or a
Principle**: Morgan or Alex in the universal set, the approvers of a shared
set, the person who owns an individual set. Anyone can hold a Preference.
`standing_by:` records who set it.

**A session never sets one on its own say-so.** It may draft a label; the
label is set only by the person's own message in that session, never by a
summary relayed from another one. Relaxing a Protocol to a Preference is
the same decision and needs the same person; a safety rule is never
relaxed.

## Detail
Write the label only for an exception, in the frontmatter:

```
standing:    preference
standing_by: themorgan
```

`standing_by:` is the GitHub username the source's registry uses (an
individual set may use the email in its `identity.json`).
`python3 tools/practice_standing.py` says who that registry names here.

**Setting a Preference aside is allowed, silently is not.** One line in the
reply is enough: which Preference, and why it did not fit this time. A
Preference that keeps being restated in conversation is a sign it should be
a Protocol; a Protocol that keeps needing exceptions, a sign it should be a
Preference. Either is a suggestion to the people with authority, never a
change a session makes.

**Recording the decision** follows
[decision-strength](decision-strength.md): a label the person ruled on by
itself is `decided`; labels approved together as a list are `assented`.

## Why
Every practice used to read as equally binding, so a habit of one person's
and a rule the team cannot work without carried the same weight. That made
two things impossible: letting a session use judgment where judgment is the
point, and telling apart a rule the team set from a preference someone
wrote down. The label says how binding a practice is **and on whose
authority**, which is the part that matters wherever several people work
to one set of rules: the people who run the work set them, and everyone,
including them, can still have preferences.

## Story
**2026-10-05, from Morgan's own argument.** The first draft labelled each
practice by how it is applied, and a second session reviewing it objected
that the three-way split mixed two questions. Morgan answered: *"It's okay
if a Preference is weaker and can be violated, that is the point!"* A
preference he keeps restating should become a Protocol so it can be
enforced; in a team, the boss sets Protocols and employees cannot, though
they still have preferences. That made the label a statement of authority,
not of style. A trial sort of 40 practices found about two thirds
Protocols, a handful of Principles and one clear Preference, so Protocol
became the default and only the exceptions carry a label. The whole plan
and its decisions are in
[spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md).

## Install
Nothing to install: [tools/practice_standing.py](../tools/practice_standing.py)
travels with the engine, and the `practice-standing` check in
[tools/precedent_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py)
reads the registry a source already keeps for its code owners. A source
with no registry cannot set a Protocol or a Principle until it declares
one.
