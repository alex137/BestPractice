---
slug:        session-tags
title:       "A session is tagged when it is created, in four namespaces"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "creating a session, or retagging one"
gates:       ["reply"]
index_clause: "tag a session at creation -- subject, repo, role, wants; never retrofitted"
checked_by:  null
defines:     ["subject:", "repo:", "role:", "wants:"]
command:     null
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "Morgan, 2026-09-14 -- \"Approved, do it, go merge\"; strength: decided"
---
## Rule
**Every session you create carries tags, applied in the `create_session` call
itself.** Four namespaces, each `namespace:value`, and a session carries as
many as apply:

| Namespace | Value | What it answers |
|---|---|---|
| `subject:` | a practice slug, an open-item anchor, a pull-request number | **What is this about?** |
| `repo:` | the short repository name | **Where can it write?** |
| `role:` | `cos`, `worker`, `watch` | **What kind of session is this?** |
| `wants:` | `merge`, `decision`, `review`, `nothing` | **What does it need from the person?** |

**`subject:` is the one that earns its keep, and it is the one that cannot be
added later.** Two live sessions sharing a `subject:` is the collision signal
[chief-of-staff](chief-of-staff.md) exists to catch — and a collision is only
worth catching *before* both sessions have run. A tag applied afterwards
describes work that is already duplicated.

**Give a session `wants:nothing` rather than leaving `wants:` off.** The
absent tag and the "needs nothing from you" tag look identical in a listing
and mean opposite things.

## Detail
**A tag is a free-form string on the session record**, held by the session
service. Not in the repository, not in a file, nothing to do with git tags.
Nothing is committed and nothing appears in a diff.

Three facts that shape how they are used (verified 2026-09-13):

- **Any session reads every session's tags**, not only ones it created — they
  come back on every `list_sessions` row.
- **The tag FILTER is refused in-session**; `list_sessions` accepts a `tags`
  argument and answers *"tags filter is not currently available"*. So a reader
  filters the full listing itself. This costs nothing at a fleet of dozens and
  would need revisiting at hundreds.
- **No interface shows them to the person.** They are readable by sessions and
  invisible to their owner, which is exactly why the reader has to turn them
  back into something he can see.

**The harness sets some of its own** — every session on this account carries
`config:auto-create-pr:off`, which is configuration riding in the same field.
Leave those alone and never treat one as a subject.

**Exactly one session carries `role:cos`.** More than one is a bug, not a
fleet.

**Retagging an existing session is allowed** and is how a fleet opened before
this rule gets covered: `set_session_tags` works on any session by identifier,
including ones this session did not create. It is worth doing for sessions
still running or still blocked. **It is not worth doing for archived ones** —
a finished session cannot collide with anything.

## Why
Two sessions taking the same subject and producing two divergent results is
worse than producing it twice, and **no session can see another from the
inside.** The only shared surface is the listing, and until something writes a
subject into it the listing cannot answer *is anyone already on this?*

The rule sits at creation rather than at any later point because that is the
only moment with both pieces of information in one place: **the spawning
session knows what the work is about, and the spawned one does not yet exist
to be asked.** This is the same argument
[spawn-session](spawn-session.md) makes for enumerating before spawning — the
check can only happen at the spawner, because nothing downstream can reach it.

**Four namespaces rather than free strings**, because the value of a tag is
that two sessions written by different people agree on it. Ad-hoc single-word
tags are the same idea without the agreement: `item-74` and a bare practice
slug are both trying to be `subject:`.

## Story
**Drafted 2026-09-13** as part of
[spec/CHIEF_OF_STAFF.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/CHIEF_OF_STAFF.md),
where the namespaces were proposed and their platform behaviour measured.
Morgan held the whole proposal for a decision, so the tags waited with it.

**Built 2026-09-14**, immediately after the rest of Chief of Staff, on the
reasoning that this was the half that decays while it waits. The fleet on that
date carried ad-hoc tags on a handful of sessions — `item-74`,
`reply-check-rollout`, a bare practice slug — and nothing had ever read one.
Two sessions were running at that moment on what looked like the same
documentation work, and **neither could see the other**, which is the whole
case for the rule in one observation.

## Install
Nothing mechanical checks this: a tag lives on the session service, not in any
repository, so no gate in any tree can see whether a session was tagged. What
reaches a session is the occasion index entry above, which is generated.
