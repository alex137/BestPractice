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
in_force_at: null
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
Precedent's internal install playbook. For a dependent repo, that
document is [templates/GETTING_STARTED.md](../templates/GETTING_STARTED.md)'s
administrator section — [INSTALL.md](../INSTALL.md) records the installation
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
**A check that needed one click sat off, silently.** An install turned on a
hosted-automation workflow and recorded that fact faithfully -- in this
repo's own technical install log, which is a document a project's
administrator has no ordinary reason to ever reopen. Nothing pointed them at
it from the page they actually return to, so the setting stayed unset until
somebody happened to look at the automation tab.

The failure is not that the fact went unrecorded. It was recorded,
accurately, in a reasonable place. The failure is that **recording and
disclosing are different acts with different audiences**, and doing the
first well makes the second feel done.

That is why the rule names the destination rather than the content: the
document that project's own people read, not the install log, and with the
exact detail needed to act -- what it is called, what it does, and any
manual click required. A disclosure a reader cannot act on without asking a
follow-up question has the same effect as no disclosure. See also
[decisions/2026-09-03-setup-getting-started-disclosure-gap.md](../decisions/2026-09-03-setup-getting-started-disclosure-gap.md).

## Install
[templates/GETTING_STARTED.md](../templates/GETTING_STARTED.md)'s
administrator section carries a standing note for "automatic checks
installed for this project," naming each workflow and what it does. Any
future GitHub-specific addition — a required secret, a new required check —
gets a line there too, added by whichever install step introduces it.
