---
slug:        github-setup-disclosed
title:       GitHub-specific setup is disclosed where the reader will actually see it
tier:        on-demand
severity:    default
applies_to:  [".github/**", "templates/github-actions/**"]
occasion:    "an install step adds something GitHub-specific"
gates:       []
index_clause: "disclose GitHub-specific setup where the project's people read"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 37
---
## Rule
Whenever an install step adds something GitHub-specific that a
project's own people need to know about — a required Actions workflow, a
repository secret, a branch-protection or required-check setting, a
permission grant — the fact, and the exact detail needed to act on it (what
it's called, what it does, any manual click to enable it), is written into
the document that project's own people actually read, not left only inside
BestPractice's internal install playbook. For a dependent repo, that
document is [templates/GETTING_STARTED.md](templates/GETTING_STARTED.md)'s
administrator section — [INSTALL.md](INSTALL.md) records the installation
mechanics; GETTING_STARTED.md records the consequence for this project's
administrator.

## Detail

## Why
An install can turn on a GitHub Actions workflow and record that
fact faithfully in this repo's own technical install log — a document a
project's administrator has no ordinary reason to reopen. Nothing points
them at it from the page they'll actually return to, so a check that needs
one click to enable can sit off, silently, until someone happens to look at
the Actions tab.

## Story

## Install
[templates/GETTING_STARTED.md](templates/GETTING_STARTED.md)'s
administrator section carries a standing note for "automatic checks
installed for this project," naming each workflow and what it does. Any
future GitHub-specific addition — a required secret, a new required check —
gets a line there too, added by whichever install step introduces it.
