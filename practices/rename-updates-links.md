---
slug:        rename-updates-links
title:       "A rename is not done until every link to the old path is updated"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "renaming, moving, or deleting a file other files may link to"
gates:       []
index_clause: "renaming a file means repointing every link to it, in the same commit"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       "2026-09-06"
approved_by: "Morgan"
source_practice_number: null
---
## Rule
Renaming, moving or deleting a file is only half the change. Every
reference to its old path — a markdown link, an image, a path in a script,
a workflow, a config — is repointed **in the same commit**, so the
repository is never in a state where the rename has landed and the links
have not. Search the whole tracked tree for the old path, not just the
directory the file lived in.

## Why
A rename is the one edit that breaks files it never touches. The moved
file is fine, its own links are fine, and the damage lands in documents
the person renaming it did not open — so nothing they look at afterwards
looks wrong. Split across two commits, the repository is broken at every
commit in between, and anyone reading it there finds dead references with
no clue that a rename is what did it.

Splitting it also loses the only cheap moment to fix it: at rename time
the old path is known exactly, and one search finds every reference. A
week later the same job means guessing what the file used to be called.

## Story
Not a hypothetical here. A 2026-09-06 sweep of this repository found 96
markdown links resolving to nothing, and a second pass found nine more
pointing at headings that had been reworded since — a class where the
link still loads the right document, just at the top, so no reader ever
reports it. In a consuming repo the same sweep found eighteen links into
a directory that had been retired months earlier, still sitting in its
`TODO.md`. In every case the move itself was correct and complete; only
the references were left behind, and each one had gone unnoticed for as
long as it existed.

## Install
`tools/precedent_check.py`'s `rename-updates-links` check compares the
current branch against the published default branch, finds files git
records as renamed or deleted, and fails if any tracked file still
references an old path. It scopes to the branch's own changes on purpose:
a reference to a path deleted long ago is somebody else's history, and
this rule is about the rename you are making now.

`tools/doc_lint.py` covers the neighbouring case continuously — a
markdown link whose target does not exist, whatever caused it — including
`#fragment`s that no heading matches any more.
