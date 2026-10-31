---
slug:        administrator-requests
title:       "\"What's waiting for me?\" and \"Add project members\": the administrator's two requests, guided end to end"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A moment, and specifically a phrase in a MESSAGE -- no file path reaches it. Routed by the `reply` gate."
occasion:    "a person says \"What's waiting for me?\" or \"Add project members\", or asks to review pending changes or add someone to the project"
gates:       ["reply"]
gates_why:   "Both requests are answered in the conversation, step by step, in plain words."
index_clause: "list what waits, with stakes and collisions; or guide adding a member"
checked_by:  null
defines:     ["What's waiting for me?", "Add project members"]
command:     {"What's waiting for me?": "List the changes waiting for your review, in plain words, and take your verdict on each.", "Add project members": "Guide you through giving someone access to this project, and write their welcome message."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-31"
approved_by: "Morgan, 2026-10-31 (strength: decided): moved from the AGENTS.md template's \"Administrator requests\" section into a practice -- \"With all this approved, act booked.\""
---
## Rule
These are conversational workflows the administrator triggers by plain
phrases. Guide them end-to-end in plain language -- they may not be a
programmer.

- **"What's waiting for me?"** (or "review pending changes") -- the
  administrator's review loop, entirely in conversation:
  1. List the open PRs, plus any branches ahead of the default branch
     with no PR yet. For each: a plain-language summary -- what changed,
     who drove it, and any hits against the review sensitivities or the
     spirit check ([working-in-parallel](working-in-parallel.md)).
  2. Point out proposals that collide with each other; offer to
     integrate colliding proposals and show the combined result before
     anything merges.
  3. Take the verdict in chat -- approve (merge, with required checks
     passing), adjust-then-merge, or send back -- and record the
     reasoning in the PR conversation either way.
  4. Merge only what the administrator has approved in conversation,
     unless they have told you a category of change is routine for them.
- **"Add project members"** -- guide the administrator through the whole
  thing:
  1. Ask, in one message: the member's GitHub username (or email), what
     they'll work on, and which AI tool they use (Claude, Codex, ChatGPT,
     Gemini, Grok, other).
  2. Give the exact GitHub steps to grant access -- for a personal repo:
     repository **Settings -> Collaborators -> Add people**; in an
     organization, their existing team flow. One sentence on the choice:
     read access lets the member's assistant answer questions; write
     access lets it propose changes (which still need approval to join
     the project).
  3. Generate a short personal welcome message the administrator can
     paste into email or chat: greet the member by name, one sentence on
     what the project is, the link to this repository's
     GETTING_STARTED.md naming the section for their tool, and one
     suggested first task drawn from the open items.
  4. Confirm there is nothing else to install or configure -- once access
     exists, the member's Getting Started section is everything they
     need.

## Why
An administrator who is not a programmer has two recurring needs: seeing
what others propose before it joins the project, and letting a new person
in. Both are a handful of GitHub screens that are easy to get wrong alone,
so the assistant walks them through in conversation, and the record of
each verdict stays on the pull request where the next reader finds it.

## Story
This was the AGENTS.md template's "Administrator requests you must know
how to handle" section from the start. On 2026-10-31 a reduction pass in a
consuming repository found that section among the largest copied word for
word, and a second consuming repository's locally trimmed copy already
lacked "in an organization, their existing team flow" and the spirit-check
reference. Morgan approved moving it into a practice (strength: decided).
The spoken phrases keep their line in the occasion index, as every phrase
a person says does.

## Install
Nothing to install. An installed repository's copy of the old template
section goes at its next Update Vendors; any lines of its own move into an
add-on practice that `adds_to: administrator-requests`.
