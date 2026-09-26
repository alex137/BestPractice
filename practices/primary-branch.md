---
slug:        primary-branch
title:       "\"Primary branch\" names trunk -- the one shared branch regular work pushes to"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Primary branch\", or asks which branch is trunk or takes routine pushes and PRs"
gates:       []
index_clause: "trunk: the branch regular work pushes to and PRs target"
checked_by:  null
defines:     ["Primary branch"]
command:     {"Primary branch": "Trunk -- the one shared branch regular work pushes to and pull requests target, as this repository declares it (usually main)."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-22"
approved_by: "Morgan, 2026-09-22 -- asked to add \"Primary branch\" to the
  vocabulary list, wording it with \"trunk\": 'Can you add \"Primary branch\"
  to the vocabulary list, and in the phrase about it, use the word \"trunk\"
  there.'"
strength:    decided
---
## Rule
**"Primary branch" is this repo's own word for trunk** -- the one shared
branch regular work pushes to and pull requests target, whatever any one
repository happens to call it. Saying it does not itself trigger an action:
[go-merge](go-merge.md) and [push-directly](push-directly.md) already
resolve a bare instruction to this branch by default. This practice exists
so the word has a definition a session -- and a person -- can look up,
rather than one only ever spelled out inline inside those two.

**The repository declares it**: `base_branch` in its `precedent.json`, or
a rule of its own that names it. In most repositories that is `main`.
Absent a declaration, it is whichever branch the repository's own routine
work is actually developed and committed against -- never a configured
default chosen just because it is configured that way.

**Under the branch tiers it is the branch this person's `Go update` lands
on** ([spec/BRANCH_TIERS_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/BRANCH_TIERS_PLAN.md)):
`python3 tools/precedent_branches.py --landing` names it -- `pre-staging`
for everyone since 2026-09-25, unless a person's `landing_branch` says
staging, the branch the repository declares above, or `main`. Staging and main are then what the
primary branch is promoted into, never where routine work is pushed.
Morgan, 2026-09-25: *"we now have a concept called \"primary branch\" -
that should probably be updated in reference to this"* (strength:
decided).

**A branch rule belongs to the repository that made it.** A repository that
stages its work on a branch other than `main` says so in its own files, and
that rule never travels to the repositories that take updates from it: in
each of those, the primary branch is whatever *that* repository declares.
Morgan, 2026-09-24, about the one catalogue repository that does this:
*"this rule doesn't get vendored in anywhere, the primary branch of the
vendored-in repo should be used, often main."* The tiers are the one
exception: `pre-staging`, `staging` and `main` are the same three names in
every repository, so that part travels like any other practice.

## Why
"Primary branch" and "trunk" name the same thing, but neither had been
written down as this project's own vocabulary before now -- so a question
like "was everything pushed to trunk?" had no guarantee of being read the
same way a bare "push directly" already resolves to that branch. Naming it
once, with a `command:` entry, puts it in the
[vocabulary](vocabulary.md) listing without a session inferring the mapping
fresh in every conversation.

## Story
Coined 2026-09-22: asked what word developers use for the branch
[push-directly](push-directly.md) already calls "the primary branch," told
it was "trunk" in general developer usage, Morgan asked for the two to be
tied together in the project's own vocabulary rather than left as a private
mapping I'd have to re-derive each time.

## Install
No check on the answer, same reason [vocabulary](vocabulary.md) gives --
this defines a word, it does not check that a session used it. What's
checked is the generated copy: `python3 tools/build_views.py` regenerates
this row into AGENTS.md's loader block and the reader-facing table, same as
every other command entry (practice: registry-source-of-truth).
