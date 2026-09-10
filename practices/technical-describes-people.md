---
slug:        technical-describes-people
title:       Technical and non-technical describe people, never projects or repositories
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "naming or scoping something around a person's skill level"
index_clause: "a skill level describes a person; never a project, repo, file or directory"
gates:       []
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-10"
approved_by: "Morgan"
strength:    decided
source_practice_number: null
---
## Rule
**"Technical" and "non-technical" are facts about a person.** They never
describe a project, a repository, a directory, a file or a document.

There is no such thing as a non-technical project. There are projects with a
non-technical contributor in them — usually alongside technical ones, since
somebody set the repository up.

So never name an artifact for the skill level of one of the people who will
touch it. Name it for what it is, and say who it is for in its own words.

**The cost of getting this wrong is not tidiness.** Once a container is
labelled with a person's skill level, every rule inside it looks like a rule
about that person — and rules that bind the container bind *everyone in it*.
That is how a restriction meant for one contributor ends up applied to the
maintainer.

## Detail
The test: if the label moved to a different person, would the name still fit?
A `document-project` template still is one whoever opens it. A
`nontechnical-document-project` stops making sense the moment a technical
person works in it, which is immediately.

**This is not a rule against describing people.** Naming a person's skill
level where a person is the subject is exactly right — a *non-technical
contributor* is a person, and a spec about their access is correctly named
for them. The error is only in attaching it to a thing.

## Why
A name is the shortest description a reader ever gets, and it does most of
the work of framing what follows. A container named for a person's skill
level quietly asserts that everything in it concerns that kind of person,
which stops being true the moment a second kind of person shows up.

The failure mode is specific and it is not obvious: a **per-person rule
written into a shared file**. The file has no way to see who is running, so
the rule lands on everyone. Nothing about that is visible from reading the
file, because the directory name has already told you the answer.

## Story
2026-09-10. This repository's `templates/nontechnical-document-project/`
shipped a tracked `.claude/settings.json` denying `git push`, `git merge`,
`git reset` and `git rebase`. The intent was a defense-in-depth layer for one
non-technical contributor. A tracked settings file binds **every** session on
the repository, so it bound the maintainers too.

It was found the only way it could be: Morgan installed the template into a real
project and, as the repository's own administrator, could not push or merge his
own work. The shipped file's comment had to tell him to edit it before he could
land anything.

**The directory name is where the mistake started.** Reading
`nontechnical-document-project`, the whole repository looks like "the
non-technical thing", so a repo-wide restriction reads as correct. Morgan named
it after the fix was already underway: *"we don't differentiate between
technical and non-technical PROJECTS only people."* The template is now
`templates/document-project/`.

The restriction itself moved to the two layers that can see who is running —
the contributor's GitHub role, and their own session configuration.

## Install
Nothing to configure. The check reads file paths only: it cannot see a
per-person rule written into a shared file, which is the failure the bad
name leads to. A path whose label is followed by a person-noun
(`nontechnical-contributor-guide`) is left alone; `practices/` and
`record/` are skipped, since a slug about this rule must contain the word
and settled history is not renamed. Both behaviours are covered by
negative controls run when it landed. `tools/precedent_check.py --only technical-describes-people` fails any
tracked path containing `technical` as a descriptor of the file or directory
itself; prose naming a *person* is untouched.
