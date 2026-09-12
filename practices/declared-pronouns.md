---
slug:        declared-pronouns
title:       Use the pronouns a person declares; where none resolves, they/them
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing about a person in the third person -- a reply, a document, a commit message, a pull-request body"
gates:       ["reply"]
index_clause: "use the pronouns a person declares; none declared means they/them, never guess"
checked_by:  null
defines:     ["pronouns"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-12"
approved_by: "Morgan F, 2026-09-12 -- decided; he asked for the field and for the install-time prompt himself"
---
## Rule
**When you write about a person in the third person, use the pronouns their
own individual practice set declares** — the `pronouns` field in that set's
`identity.json`, beside their name, their timezone and their register.

**Where no declaration resolves — nobody identified, or nobody who has
stated pronouns — use they/them.** That is the floor, and it is not a
placeholder for a better guess: **never infer pronouns from a name.** A name
does not carry them, a wrong guess misgenders a real person in a way the
neutral default never does, and the cost lands on the person, not on you.

The declaration is a fact about a person, so **nothing at team or repo level
overrides it.** A shared repository deliberately names nobody and has no
business asserting one.

## Detail
**`pronouns` holds the pair a sentence actually uses** — `he/him`,
`she/her`, `they/them` — and nothing else. It is not a gender field, and one
was considered and refused: pronouns are what writing a sentence requires,
gender is a second and more sensitive fact that nothing here reads, and a
field nothing consumes is a field nobody maintains.

**It is declared, not enforced.** No tool can read a reply and tell whether
it used the right pronouns, so this is a rule a session follows rather than
a gate that catches it — the same standing as `register` in the same file.
What *is* mechanical is the declaration's presence: see Install.

The field covers **you writing about them**. A person's own prose about
themselves is theirs.

## Why
The alternative to a declared field is a guess, and the guess is made from a
name. Names do not carry pronouns — this repository's own owner has a
gender-ambiguous one — so the guess is wrong often enough that the safe
default has to be the unguessed one.

Putting the value in `identity.json` rather than in a practice is what makes
it work for **everyone** rather than for one person. A practice is prose in
one person's set; a field is a slot every set has, that an install can ask
about and a check can notice is empty. The same reasoning already moved
`register` there on 2026-09-10, and that file's own comment makes the
argument: it is a fact about a person, and no shared repository can know it.

## Story
**2026-09-12.** The rule existed here, and only for one person, as a single
clause buried in the Detail section of `commit-author` in the individual
set — a practice about which name and address git records: *"where a
document refers to me by name or pronoun, use 'Morgan' and he/him."*

Two things were wrong with that. It sat in a practice about git config, so
the only route to it was reading a git-identity rule to the end; and being
prose in one private set, it answered the question for its author and left
it permanently unanswered for everybody else — a session working with any
other person had nothing to read and nothing telling it not to guess.

Morgan raised it himself and chose the shape: *"in each person's identity
file, it should define it for that one individual"*, and — the half that
turns a field into an answered question — *"as part of the installation or
the migration, if the pronouns is blank, I think it should just ask you and
then update it."* The clause came out of `commit-author`, which is now about
commit authorship alone.

**This landed at universal** because nothing in it is specific to this
project or this team: any repository, for any person, needs the same answer.

## Install
`identity.json` carries `pronouns`, shipped in the individual skeleton at
[`templates/practice-set-individual/identity.json.template`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/practice-set-individual/identity.json.template)
as `{{PERSON_PRONOUNS}}`.

**Two halves of "is it filled in", because a new set and a migrated set fail
differently.** A set created by
[`tools/precedent_bootstrap_source.py`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_bootstrap_source.py)
and never finished still holds the literal placeholder, which that tool's
`verify()` already sweeps for. A set **migrated** into place predates the
field entirely and holds no `pronouns` key at all — which the placeholder
sweep structurally cannot see, since there is no placeholder to find. So
`verify()` also names the absent key directly, for the `individual` level,
and says to ask the person rather than guess. Every individual set created
before 2026-09-12 is in that second position; the check found the one that
exists here and nothing else.

**`checked_by` is null deliberately, and the reason is specific rather than
"too hard":** the thing worth checking is whether a sentence used the right
pronouns, and no gate can read intent out of prose to decide that. The
checkable half — the declaration exists and is filled in — is checked, in
`verify()`, which is where install and migration both already look. Wiring a
second check into `tools/checks/` would add nothing: a consuming repo has no
`identity.json` to check.

The install and migration procedures name it as a value to ask for:
[`spec/BOOTSTRAP_NEW_SOURCES.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/BOOTSTRAP_NEW_SOURCES.md)
and
[`spec/MIGRATING_EXISTING_INSTALLS.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/MIGRATING_EXISTING_INSTALLS.md).
