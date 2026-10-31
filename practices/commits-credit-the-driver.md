---
slug:        commits-credit-the-driver
title:       Commits are credited to the human driving the session
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A moment -- the first commit a session makes for a person. No path reaches it; the commit-identity hooks enforce the author where they are installed."
occasion:    "making the first commit of a session for a person"
gates:       []
gates_why:   "No gate runs before a commit; the commit-identity hooks are the mechanism, and this is the rule they carry out."
index_clause: "author each commit as the person; name yourself as co-author"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-31"
approved_by: "Morgan, 2026-10-31 (strength: decided): moved from the AGENTS.md template's Conventions section into a practice -- \"With all this approved, act booked.\""
---
## Rule
**Commits are credited to the human driving the session.** Author each
commit as the member, with their name and GitHub noreply email (ask
**before the first commit** if you don't know who you're working for:
`git commit --author="Name <ID+user@users.noreply.github.com>"`), and
name yourself in a `Co-Authored-By:` trailer. Where a platform forces its
own committer identity, the author field still records the human.

## Why
Hosted agent harnesses author commits as the agent unless told otherwise,
so a session that never asks mis-attributes silently, and authorship is
how [working-in-parallel](working-in-parallel.md) knows whose work a diff
reworks.

## Story
*Observed 2026-08 on hosted Claude Code sessions; GitHub attributes by
author email, verified 2026-08.* The rule was a bullet in the AGENTS.md
template's Conventions section, the one bullet there that named no
practice. When that section was removed on 2026-10-31 (its other bullets
pointed at practices that load on their own), the bullet became this
practice, word for word (Morgan, strength: decided).

## Install
The commit-identity hooks Precedent installs set and check the author.
Nothing else to install.
