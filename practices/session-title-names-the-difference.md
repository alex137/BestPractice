---
slug:        session-title-names-the-difference
title:       "A session's title names what makes it different, not its category"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A moment -- creating or renaming a session -- and the title lives on the session service, not in any tree. No file path reaches it. Routed by the `reply` gate. Decided: 2026-09-17, when the practice landed."
occasion:    "creating, renaming or retagging a session"
gates:       ["reply"]
gates_why:   "The naming decision is made while composing a reply, at creation or the moment the differentiator becomes known -- the same moment session-tags' obligation lands in."
index_clause: "title by the differentiator; never the task alone, never an open sibling's title"
index_required: true
checked_by:  null
defines:     []
command:     null
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-17"
approved_by: "Morgan, 2026-09-17 -- \"This is great, I love it, let's implement this please\"; strength: decided. Check against open sibling titles added 2026-09-29, Morgan -- \"Please Act, and build this solution\" after two of his sessions came out with the same title; strength: decided"
---
## Rule
**A session's title is `<repo>: <differentiator>`** — a short tag for the
repository the session writes to, then the one thing that makes this session
unlike any other session doing the same kind of work: a PR number, a commit,
a branch name, a file, a named blocker. Never the task category alone.

**Before setting a title, read the titles of the person's other open
sessions** (on Claude Code, `list_sessions`) **and make sure yours matches
none of them on the same repo.** A match means the differentiator is not
sharp enough yet. A title the client already chose gets the same check
before you keep it.

Set it at creation, and re-set it the moment a sharper differentiator
becomes known.

## Detail
"Vendor update," "commit identity," "vendoring exclusion mechanism" are
categories, not identities, and a fleet listing with several of them side by
side cannot tell you which one you're looking for.

**At creation** is `create_session`'s `title`; **mid-session** is
`set_session_title` — a session opened before its PR number existed does not
stay generically named once the PR does.

**Why the client's title needs the check too:** a web client titles a
session from its first message, so two sessions opened with similar first
messages get the same title, and each looks fine on its own. On a match,
reach for the branch, the PR, the file, or the specific failure.

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

On 2026-09-29 two sessions on the same repo, opened under two hours
apart, both carried "Precedent check engine fixes" until Morgan put "MAIN"
in one and "ONCE LIVE" in the other by hand. Neither session had looked at
the other's title, because nothing told it to: the rule said the
differentiator should be unlike any other session's, and gave no step for
finding out what the others said. The check-the-open-sessions step was added
that day.

## Install
Nothing mechanical checks this: a title lives on the session service, not in
any tree, so no gate in any repo can see whether one was set well. What
reaches a session is the occasion index entry above, generated, and the
`reply` gate reminder.

**`index_required: true`, added 2026-09-22.** Without it,
[build_views.py](../tools/build_views.py)'s `index_is_redundant()` saw
`gates: ["reply"]` and dropped this rule's own occasion-index line, on the
theory that the reply gate already routes it. It does not: the reply gate
fires at the END of a turn, after `create_session` has already run with
whatever title got chosen. For a rule about what title to pick AT CREATION,
that is too late to do its job -- the occasion index is the only channel
that fires before the choice is made.
[precedent_check.py](../tools/precedent_check.py)'s
`index-required-is-declared` was meant to catch a missing flag like this one,
but its regex only recognizes occasions
phrased as something a *person says* ("Morgan asks", "the message says") --
"naming or renaming a session, at creation" doesn't match that shape, so
the check passed clean. Caught downstream: precedent-individual's own
override of this rule, `session-title-abbreviates-repo`, had the identical
gap and is what surfaced it -- Morgan noticed session titles weren't
getting abbreviated and asked why.
