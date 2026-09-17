---
slug:        session-title-names-the-difference
title:       "A session's title names what makes it different, not its category"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "naming or renaming a session, at creation or once its differentiator is known"
gates:       ["reply"]
index_clause: "title each session by its differentiator, never its task category alone"
checked_by:  null
defines:     []
command:     null
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-17"
approved_by: "Morgan, 2026-09-17 -- \"This is great, I love it, let's implement this please\"; strength: decided"
---
## Rule
**A session's title is `<repo>: <differentiator>`** — a short tag for the
repository the session writes to, then the one thing that makes this session
unlike any other session doing the same kind of work: a PR number, a commit,
a branch name, a file, a named blocker. Never the task category alone —
"vendor update," "commit identity," "vendoring exclusion mechanism" are
categories, not identities, and a fleet listing with several of them side by
side cannot tell you which one you're looking for.

Set the title this way at creation (`create_session`'s `title`), and
re-set it with `set_session_title` the moment the differentiator becomes
known mid-session — a session opened before its PR number existed does not
stay generically named once the PR does.

**A session touching several repos at once names the outcome repo**, or
says plainly how many (`5-repo commit-identity sync`) when there isn't one
obvious owner.

## Why
[session-tags](session-tags.md) exists because "is anyone already on this?"
can only be answered from a listing, and a `subject:` tag is only something a
*session* reads. A title answers the same question for a *person* — it is
the one field visible in the fleet UI without opening anything. A title that
repeats the category answers "what kind of work is this," which every
sibling session already answers identically; it never answers "which one."

## Story
Drafted 2026-09-17, from a listing where six of ten live titles read "vendor
update," "vendoring exclusion mechanism verification," or "vendoring
exclusion mechanism fix" — three sessions doing recognizably different work,
one shared label apiece. Demonstrated on ten live sessions in chat first,
each given a proposed `<repo>: <differentiator>` name; Morgan approved
implementing it once he saw the renamed list side by side with the
originals.

## Install
Nothing mechanical checks this: a title lives on the session service, not in
any tree, so no gate in any repo can see whether one was set well. What
reaches a session is the occasion index entry above, generated, and the
`reply` gate reminder.
